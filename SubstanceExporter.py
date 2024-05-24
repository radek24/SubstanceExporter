import bpy
import os
import subprocess

bl_info = {
    "name": "Auto exporter",
    "author": "Radovan Stastny <radovan.stastny2004@gmail.com>",
    "version": (1, 0),
    "blender": (2, 85, 0),
    "category": "Import-Export",
    "doc_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=RickAstley",
    "location": "View3D > Side Panel > Auto export",
    "description": "Addon to streamline blender->substance workflow",
}

# UI
# -----------------------------------------------------------------------------------------------------------------------#

class ExampleAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    substance_path_pref: bpy.props.StringProperty(
        name="Substance path",
        subtype='FILE_PATH',
        default='C:/Users/radov/OneDrive/Plocha/3d_veci/Substance/Hra/FBX/'
    )
    SubstanceFoldersPath_pref: bpy.props.StringProperty(
        name="substance folder path",
        subtype='FILE_PATH',
        default='C:/Users/radov/OneDrive/Plocha/3d_veci/shooter/Substance/'
    )
    Steampath_pref: bpy.props.StringProperty(
        name="steam.exe location",
        subtype='FILE_PATH',
        default='C:\Program Files (x86)\Steam\Steam.exe'
    )
    AppID_pref: bpy.props.StringProperty(
        name="Steam app ID",
        default='1775390'
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="This is the path where FBX files for substance project will be saved")
        layout.prop(self, "substance_path_pref")
        
        layout.label(text="This is the path where folder for youre substance textures will be created")
        layout.prop(self, "SubstanceFoldersPath_pref")
        
        layout.label(text="Location of steam.exe")
        layout.prop(self, "Steampath_pref")
        
        layout.label(text="ID of your substance version, you can find this in steam link")
        layout.prop(self, "AppID_pref")

class VIEW3D_PT_AUTOEXPORT(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Auto export"
    bl_label = "Auto export"

    def draw(self, context):
        filename = bpy.path.basename(bpy.context.blend_data.filepath).removesuffix(".blend")
        col = self.layout.column(align=True)
        export_prop_grp = context.window_manager.export_prop_grp
        col.label(text="Export Name")
        col.prop(export_prop_grp, "use_file_name_as_name")
        col.prop(export_prop_grp, "export_name")
        if export_prop_grp.use_file_name_as_name == True:
            if filename == "":
                export_prop_grp.export_name = "untitled"
            else:
                export_prop_grp.export_name = filename
        col.label(text="")
        col.label(text="Preferences:")
        col.prop(export_prop_grp, "substance_open_type")
        col.prop(export_prop_grp, "substance_folder")
        col.label(text="")
        col.prop(export_prop_grp, "create_in_folder")
        if export_prop_grp.create_in_folder ==True:
            col.prop(export_prop_grp, "name_of_folder")
        else:
            export_prop_grp.name_of_folder = filename
        col.prop(export_prop_grp, "only_selected")

        col.label(text="")
        col.operator('mesh.substance_export', icon='EXPORT')

#Props
#-----------------------------------------------------------------------------------------------------------------------#
class ExportPropertyGroup(bpy.types.PropertyGroup):
    
    substance_open_type: bpy.props.EnumProperty(
        name="Method",
        items=[
            ('1', "Create Project", "Will create project from exported mesh"),
            ('0', "Dont create project and rewrite", "Will just overwrite fbx file"),
        ],
        default='1',
    )
    
    only_selected: bpy.props.BoolProperty(name="Export selected", default=True, description="Export just selection")
    use_file_name_as_name: bpy.props.BoolProperty(name="Filename as name", default=True, description="Can use custom name")
    export_name: bpy.props.StringProperty(name="Name", default="Asset",
                                          description="Name of export")
    substance_folder: bpy.props.BoolProperty(name="Open substance folder", default=True, description="Will open folder where textures will be exported")
    create_in_folder: bpy.props.BoolProperty(name="Export to new folder", default=False, description="Create custom folder for export")
    name_of_folder: bpy.props.StringProperty(name="Name", default="Asset",
                                          description="Name of the custom folder")

class MESH_OT_AUTO_export(bpy.types.Operator):
    """export to substance"""
    bl_idname = 'mesh.substance_export'
    bl_label = "Substance Export"
    bl_options = {'REGISTER', 'UNDO', 'UNDO_GROUPED', }

    # Checking if it is possible to perform operator
    @classmethod
    def poll(cls, context):
        export_prop_grp = context.window_manager.export_prop_grp
        objs = context.selected_objects
        if len(objs) != 0 or not export_prop_grp.only_selected:
            current_mode = bpy.context.object.mode
            return context.area.type == 'VIEW_3D' and current_mode == 'OBJECT'
        else:
            return False

    def execute(self, context):
        export_prop_grp = context.window_manager.export_prop_grp
        
        if export_prop_grp.export_name=="":
            self.report({'ERROR'}, "Bych pojmenoval mesh idk")
            return {'CANCELLED'}
       
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        substance_path = addon_prefs.substance_path_pref
        
        if export_prop_grp.create_in_folder:
            substance_path = substance_path + export_prop_grp.name_of_folder+"/"
            if not os.path.exists(substance_path):
                os.makedirs(substance_path)
            
        finalpath = substance_path + export_prop_grp.export_name + ".fbx"     
        bpy.ops.export_scene.fbx(filepath=finalpath,use_selection=export_prop_grp.only_selected,mesh_smooth_type='FACE')

        # Substance cary mary
        if export_prop_grp.substance_open_type=='1':
            SubstanceExportPath = addon_prefs.SubstanceFoldersPath_pref + export_prop_grp.export_name
            if not os.path.exists(SubstanceExportPath):
                    os.makedirs(SubstanceExportPath)
            
            if export_prop_grp.substance_folder:
                subprocess.run('explorer ' + SubstanceExportPath.replace("/","\\"))
            steamPath = addon_prefs.Steampath_pref
            command = '\"'+steamPath+'\" -applaunch \"'+ addon_prefs.AppID_pref +'\" --mesh ' + finalpath + " --export-path " + SubstanceExportPath
            subprocess.run(command,shell=True)

        return {'FINISHED'}

# ---------------------------------------------------------------------------------------------------------------------#
# Adds function to F3 search
def menu_func_origin(self, context):
    self.layout.operator(MESH_OT_AUTO_export.bl_idname, icon='OBJECT_ORIGIN')

# --------------------------------------------------------------------------------------------------------------------#
# Registration
def register():
    # UI
    bpy.utils.register_class(VIEW3D_PT_AUTOEXPORT)

    # operators
    bpy.utils.register_class(MESH_OT_AUTO_export)

    # F3 menu
    bpy.types.VIEW3D_MT_edit_mesh.append(menu_func_origin)

    # Properties
    bpy.utils.register_class(ExportPropertyGroup)
    bpy.types.WindowManager.export_prop_grp = bpy.props.PointerProperty(type=ExportPropertyGroup)

    # Addon preferences
    bpy.utils.register_class(ExampleAddonPreferences)

def unregister():
    # UI
    bpy.utils.unregister_class(VIEW3D_PT_AUTOEXPORT)

    # Operators
    bpy.utils.unregister_class(MESH_OT_AUTO_export)

    # F3 menu
    bpy.types.VIEW3D_MT_edit_mesh.remove(menu_func_origin)
   
    # Properties
    bpy.utils.unregister_class(ExportPropertyGroup)
    del bpy.types.WindowManager.export_prop_grp

    # Addon preferences
    bpy.utils.unregister_class(ExampleAddonPreferences)