from bpy.types import WindowManager
import bpy.utils.previews
from bpy.props import PointerProperty, StringProperty, EnumProperty, FloatProperty, BoolProperty
import bpy
import os
import sys
import re
import subprocess
import webbrowser

from . import addon_updater_ops

bl_info = {
    "name": "iMeshh Asset Manager",
    "version": (0, 2, 82),
    "blender": (2, 90, 1),
    "location": "View3D > TOOLS > iMeshh",
    "author": "iMeshh",
    "description": "Manager for iMeshh models",
    "category": "Assets Management"
}


HDRI_NODE_TAG = 'iMeshhHDRINode'


def is_2_80():
    return bpy.app.version >= (2, 80, 0)

def reset_cat(self, context):
    context.scene.asset_manager.cat = 'All'
    context.scene.asset_manager.subcat = '.'


# Make folders for storing assets
def make_folders(root):
    folders = {
        'Architectural': ['Decoration', 'Doors', 'Radiators', 'Stairs', 'Switches', 'Windows'],
        'Bathroom': ['Basins', 'Baths', 'Details', 'Mirrors', 'Radiators', 'Showers', 'WC'],
        'Bedroom': ['Beds', 'Furniture'],
        'Clothing': ['Accessories', 'Tops'],
        'Decorations': ['Modern', 'Toys', 'Traditional', 'Wall'],
        'Dining': ['Dinnerware', 'Glassware', 'Table'],
        'Electronics': ['TVs', 'Monitors'],
        'Food & drink': ['Alcohol', 'Food', 'Soft Drinks'],
        'Furniture Details': ['Blinds', 'Curtains', 'Cushions', 'Rugs'],
        'Kitchen': ['Accessories', 'Cooking', 'Kitchen Electronics', 'Sinks', 'Taps & Utensils'],
        'Lighting': ['Bulbs', 'Ceiling pendants', 'Desk lamps', 'Floor Lamps', 'Wall Lamps'],
        'Office': ['Electronics', 'Desks', 'Chairs'],
        'Plants': ['Indoor', 'Outdoor'],
        'Seating': ['Stools', 'Lounge Chairs', 'Sofas', 'Benches', 'Chairs'],
        'Storage': ['Book Shelves', 'Dressers', 'TV Units', 'Wardrobes'],
        'Tables': ['Coffee Tables', 'Dining Tables', 'Office Desks', 'Side Tables'],
        'Materials': ['Brick', 'Concrete', 'Fabrics', 'Ground', 'Leather', 'Worktops', 'Metal', 'Paint',
                      'Plaster', 'Plastic', 'Stone', 'Tiles', 'Wood', 'Wood Floors'],
        'HDRI': ['Interior', 'Exterior']
    }

    if not os.path.exists(root):
        os.mkdir(root)

    for cat, subs in folders.items():
        path = os.path.join(root, cat)
        if not os.path.exists(path):
            os.mkdir(path)

        for sub in subs:
            path1 = os.path.join(path, sub)
            if not os.path.exists(path1):
                os.mkdir(path1)

class KAM_PrefPanel(bpy.types.AddonPreferences):
    bl_idname = __name__

    asset_dir : StringProperty(
        name="Assets Path",
        default=os.path.join(os.path.dirname(__file__), 'Assets'),
        description="Show only hotkeys that have this text in their name",
        subtype="DIR_PATH")
    
    material_dir : StringProperty(
        name="Material Path",
        default=os.path.join(os.path.dirname(__file__), 'Assets'),
        description="Show only hotkeys that have this text in their name",
        subtype="DIR_PATH")
    
    hdri_dir : StringProperty(
        name="HDRI Path",
        default=os.path.join(os.path.dirname(__file__), 'Assets'),
        description="Show only hotkeys that have this text in their name",
        subtype="DIR_PATH")
    

    switch_corona : BoolProperty(
        name="Enable Corona/Blender switch",
        default=False,
        description=" Enable switch corona / cycle in Imeshh settings panel")

    # addon updater preferences
    auto_check_update : bpy.props.BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=False,
    )

    updater_intrval_months : bpy.props.IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0
    )
    updater_intrval_days : bpy.props.IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=7,
        min=0,
    )
    updater_intrval_hours : bpy.props.IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23
    )
    updater_intrval_minutes : bpy.props.IntProperty(
        name='Minutes',
        description="Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "asset_dir", text='Assets path')
        row.prop(self, "material_dir", text='Materials path')
        row.prop(self, "hdri_dir", text='HDRI path')
        row.operator("asset_manager.make_folder", icon="PROP_CON")
        row = layout.row()
        row.prop(self, "switch_corona")

        addon_updater_ops.update_settings_ui(self, context)


class KAM_MakeFolder(bpy.types.Operator):
    bl_idname = "asset_manager.make_folder"
    bl_label = "Make"
    bl_description = 'Make Assets folder'

    def execute(self, context):
        hdri_dir = context.preferences.addons[__name__].preferences.hdri_dir
        material_dir = context.preferences.addons[__name__].preferences.material_dir
        root = get_root_dir(context)
        make_folders(root)
        if hdri_dir == root:
            hdri_dir = os.path.join(root, 'HDRI')
        if material_dir == root:
            material_dir = os.path.join(root, 'Materials')

        return {'FINISHED'}


#Settings panel for menu on the right
class KAM_SettingsPanel(bpy.types.Panel):
    bl_label = "iMeshh Settings"
    bl_idname = "KRIS_PT_Imesh_Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "iMeshh"
    bl_options = {"DEFAULT_CLOSED"}

    # Draw the panel
    def draw(self, context):
        layout = self.layout
        if get_pref_switch(context):
            manager = context.scene.asset_manager
            layout.prop(manager, 'blend')
        col = layout.column(heading ='Linked Object Settings')
        col.prop(context.window_manager, 'asset_manager_collection_import')
        col.prop(context.window_manager, 'asset_manager_auto_rename')
        col = layout.column(heading ='Camera Settings')
        col.prop(context.window_manager, 'asset_manager_ignore_camera')


# Panel for menu on the right
class KAM_Panel(bpy.types.Panel):
    bl_label = "iMeshh Asset Manager"
    bl_idname = "KRIS_PT_Asset_Manager"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "iMeshh"
    bl_options = {"DEFAULT_CLOSED"}

    # Draw the panel
    def draw(self, context):
        KAM_UI(self, context)


class KAM_OpenThumbnail(bpy.types.Operator):
    """Open the thumbnail image"""
    bl_idname = "asset_manager.open_thumbnail"
    bl_label = "Thumbnail"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_blend = context.window_manager.asset_manager_prevs
        
        for (blend_path, _, file_blend, icon_id, _) in preview_collections['main'].asset_manager_prevs:
            #print(blend_path, file_blend, icon_id)
            if blend_path == selected_blend:
                for (preview_path, preview_image) in preview_collections['main'].items():
                    if preview_image.icon_id == icon_id:
                        webbrowser.open(preview_path)

        return {'FINISHED'}


def open_blend(binary, filepath):
    if sys.platform.startswith("win"):
        base, exe = os.path.split(binary)
        subprocess.Popen(["start", "/d", base, exe, filepath], shell=True)
    else:
        subprocess.Popen([binary, filepath])

def enum_members_from_type(rna_type, property):
    prop = rna_type.bl_rna.properties[property]
    return [e.identifier for e in prop.enum_items]

def enum_members_from_instance(data, property):
    """get all available entries for an enum property
    - data : (AnyType) data from wich tot ake property
    - property : (string) Edientifier property in data"""
    return enum_members_from_type(type(data), property)

class KAM_OpenBlend(bpy.types.Operator):
    """Open the .blend file for the asset"""
    bl_idname = "asset_manager.open_blend"
    bl_label = ".blend"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(get_selected_blend(context))

    def execute(self, context):
        selected_blend = get_selected_blend(context)

        open_blend(bpy.app.binary_path, selected_blend)
        return {'FINISHED'}

# Draw the dialog
def KAM_UI(self, context):
    layout = self.layout
    wm = context.window_manager
    manager = context.scene.asset_manager

    row = layout.row()
    row.operator("asset_manager.link_to", icon='MESH_UVSPHERE')
    #TABS
    col = layout.column()
    row = col.split()
    for item in enum_members_from_instance(manager, 'tabs'):
        row.prop_enum(manager, 'tabs', value=item, text= '')

    # Categories Drop Down Menu
    col = layout.column()
    col.prop(manager, "cat")
    if manager.subcat:
        col.prop(manager, "subcat")
    
    # Thumbnail view
    if len(wm.asset_manager_prevs) != 0:
        row = layout.row()
        row.template_icon_view(wm, "asset_manager_prevs", show_labels=True)

        row = layout.row(align=True)
        row.operator("asset_manager.open_thumbnail", icon="FILE_IMAGE")
        row.operator("asset_manager.open_blend", icon="FILE_BLEND")
        #HDRI tab
        if context.scene.asset_manager.tabs == 'HDRI' or get_selected_hdr(context):
            row = layout.row()
            row.operator("asset_manager.import_hdr", icon='TEXTURE_DATA')
            row = layout.row()
            if context.scene.world.node_tree and 'GROUND_PROJECTION' in context.scene.world.node_tree.nodes:
                col = layout.column(heading ='Ground projection')
                for inp in context.scene.world.node_tree.nodes['GROUND_PROJECTION'].inputs:
                    col.prop(inp, 'default_value', text=inp.name)
            if context.scene.world.node_tree and 'HDRI_GROUP' in context.scene.world.node_tree.nodes:
                col = layout.column(heading ='HDRI')
                for inp in context.scene.world.node_tree.nodes['HDRI_GROUP'].inputs:
                    if inp.name != 'HDRI':
                        col.prop(inp, 'default_value', text=inp.name)
        #OBJECT tab
        elif context.scene.asset_manager.tabs == 'OBJECT':
            row = layout.column()
            spl = row.split()
            spl.operator("asset_manager.import_object", icon='APPEND_BLEND').link = False
            spl.operator("asset_manager.import_object", icon='LINK_BLEND', text='Link Object').link = True
        #MATERIAL tab
        elif context.scene.asset_manager.tabs == 'MATERIAL':
            row = layout.row()
            row.operator("asset_manager.import_material", icon='TEXTURE_DATA')


# Get root directory from user preferences
def get_root_dir(context=None):
    if not context:
        context = bpy.Context

    if hasattr(context, "preferences"):
        pref = context.preferences.addons[__name__].preferences
    else:
        pref = context.user_preferences.addons[__name__].preferences
    
    if context.scene.asset_manager.tabs == 'HDRI':
        return pref.hdri_dir
    elif context.scene.asset_manager.tabs == 'MATERIAL':
        return pref.material_dir
    return pref.asset_dir

def get_pref_switch(context=None):
    if not context:
        context = bpy.Context

    if hasattr(context, "preferences"):
        pref = context.preferences.addons[__name__].preferences
    else:
        pref = context.user_preferences.addons[__name__].preferences

    return pref.switch_corona

def category_items(self, context):
    categories = []
    index = 1
    root_dir = get_root_dir(context)
    # print('category')
    for folder in sorted(os.listdir(root_dir)):
        path = os.path.join(root_dir, folder)

        if os.path.isdir(path) and not folder.startswith('.'):
            categories.append((folder, folder, '', index))
            index += 1

    categories.insert(0, ('All', 'All', '', 0))
    return check_display_folder(categories)

# Fill out sub categories.
def subcategory_items(self, context):
    subcategories = [('All', 'All', '', 0)]
    index = 1
    root_dir = get_root_dir(context)

    if self.cat == 'All':
        return [('.', '.', '', 0)]
    if self.tabs != 'OBJECT':
        return [('0', '.', '', 0)]
    cat_path = os.path.join(root_dir, self.cat)
    for folder in sorted(os.listdir(cat_path)):
        path = os.path.join(cat_path, folder)
        if os.path.isdir(path) and not folder.startswith('.'):
            subcategories.append((folder, folder, '', index))
            index += 1
    
    return subcategories

def check_display_folder(categories):
    split_hdri = bpy.context.preferences.addons[__name__].preferences.hdri_dir.split(os.sep)
    hdri_folder_name = split_hdri[-2]
    del split_hdri[-2]
    split_material = bpy.context.preferences.addons[__name__].preferences.material_dir.split(os.sep)
    material_folder_name = split_material[-2]
    del split_material[-2]

    path_hdri = os.sep.join(split_hdri)
    path_material = os.sep.join(split_material)
    names_to_remove = []
    if path_hdri == bpy.context.preferences.addons[__name__].preferences.asset_dir or path_material == bpy.context.preferences.addons[__name__].preferences.asset_dir:
        for folder in categories:
            if folder[0] == material_folder_name or folder[0] == hdri_folder_name:
                names_to_remove.append(folder)
    for name in names_to_remove:
        categories.remove(name)
    return categories





# PropertyGroup for this asset manager
class KrisAssetManager(bpy.types.PropertyGroup):
    cat : EnumProperty(
        items=category_items,
        name="Category",
        description="Select a Category",
        update=subcategory_items)

    subcat : EnumProperty(
        items=subcategory_items,
        name="Subcategory",
        description="Select subcategory",
        update=None)

    blend : EnumProperty(
        items=[('cycles', 'Cycles', '', 0), ('corona', 'Corona', '', 1)],
        name="Blend",
        description="Select blend")

    #Tabs
    tabs : EnumProperty(
        #(identifier, name, description, icon, number)
        items=[('OBJECT', 'Object', 'Object tab', 'MESH_MONKEY', 0),
               ('MATERIAL', 'Material', 'Material tab', 'MATERIAL', 1),
               ('HDRI', 'Hdri', 'Hdri tab', 'WORLD_DATA', 2)], 
        name = 'Tabs', 
        description = 'Selected tab', 
        update=reset_cat)



# EnumProperty(asset_manager_prevs) Callback
def scan_directory(self, context):
    curr_tab = context.scene.asset_manager.tabs
    root_dir = get_root_dir(context)
    category = context.scene.asset_manager.cat
    subcategory = context.scene.asset_manager.subcat
    if subcategory == '0':
        directory = os.path.join(root_dir, category)
    else:
        directory = os.path.join(root_dir, category, subcategory)

    enum_items = []
    if context is None:
        return enum_items

    # Get the Preview Collection (defined in register func)
    pcoll = preview_collections["main"]


    # Skip if scanned already
    if directory == pcoll.asset_manager_prev_dir:
        return pcoll.asset_manager_prevs

    print("Scanning directory: %s" % directory)

    if category == 'All' and curr_tab == 'OBJECT':
        enum_items = scan_for_assets_root(root_dir, enum_items, pcoll)
    elif category == 'All' and curr_tab == 'HDRI':
        enum_items = scan_for_assets_subcategory(root_dir, enum_items, pcoll)
    elif category == 'All' and curr_tab == 'MATERIAL':
        enum_items = scan_for_assets_category(root_dir, enum_items, pcoll)
    elif subcategory == 'All':
        enum_items = scan_for_assets_category(os.path.join(root_dir, category), enum_items, pcoll)
    elif directory and os.path.exists(directory):
        enum_items = scan_for_assets_subcategory(directory, enum_items, pcoll)

    # Return validation
    empty_path = os.path.join(os.path.dirname(root_dir), "empty.png")
    if len(enum_items) == 0:
        if 'empty' in pcoll:
            enum_items.append(('empty', '', "", pcoll['empty'].icon_id, 0))
        else:
            empty = pcoll.load('empty', empty_path, 'IMAGE')
            enum_items.append(('empty', '', '', empty.icon_id, 0))

    pcoll.asset_manager_prevs = enum_items
    pcoll.asset_manager_prev_dir = directory

    bpy.data.window_managers[0]['asset_manager_prevs'] = 0

    return enum_items


def is_hdr(file):
    return file.lower().endswith(('.hdr', '.hdri', '.exr'))


def is_blend(file):
    return file.lower().endswith(('.blend',))


def is_image(file):
    return file.lower().endswith(('.png', '.jpg'))


def find_blend_in_path(path):
    file_name = "no blend"
    for file in os.listdir(path):
        if is_blend(file):
            file_name = file
            break
        elif is_hdr(file) and file_name == 'no blend':
            file_name = file
    return file_name


def load_preview(img_path, pcoll):
    if img_path in pcoll:
        return pcoll[img_path].icon_id
    else:
        thumb = pcoll.load(img_path, img_path, 'IMAGE')
        return thumb.icon_id


def scan_for_assets_subcategory(directory, enum_items, pcoll):
    """
    Scan for assets inside a sub category

    :param directory: The path to the sub-category
    :param enum_items: List of all enum items already scanned (will be mutated and returned)
    :param pcoll: Preview collection
    :return: Original enum_items parameter with the items from this sub-category added
    """
    if os.path.isdir(directory):
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            

            # Handle loose .hdr file
            if is_hdr(item):
                icon_id = load_preview(item_path, pcoll)
                enum_items.append((item_path, item, item, icon_id, len(enum_items)))
                continue

            #Check validity of item_path
            if os.path.isdir(item_path):
                # The item is a folder that contains either a blend file or an HDRI file
                file_blend = find_blend_in_path(item_path)
                # Find the preview and load it
                for file in os.listdir(item_path):
                    if is_image(file):
                        img_path = os.path.join(item_path, file)
                        blend_path = os.path.join(item_path, file_blend)
                        icon_id = load_preview(img_path, pcoll)
                        enum_items.append((blend_path, item, file_blend, icon_id, len(enum_items)))
                        break
                else:
                    # No preview found, if it's an HDRI than load that as the preview
                    if is_hdr(file_blend):
                        img_path = os.path.join(item_path, file_blend)
                        icon_id = load_preview(img_path, pcoll)
                        enum_items.append((img_path, item, file_blend, icon_id, len(enum_items)))

    return enum_items


def scan_for_assets_category(directory, enum_items, pcoll):
    """
    Scan for all assets inside a category

    :param directory: The path to the category
    :param enum_items: List of all enum items already scanned (will be mutated and returned)
    :param pcoll: Preview collection
    :return: Original enum_items parameter with the items from this category added
    """
    if os.path.isdir(directory):
        for subcategory in os.listdir(directory):
            scan_for_assets_subcategory(os.path.join(directory, subcategory), enum_items, pcoll)
    return enum_items


def scan_for_assets_root(root, enum_items, pcoll):
    """
    Scan for all assets in the asset library

    :param root: Path to the root folder of the asset library
    :param enum_items: List of all enum items already scanned (will be mutated and returned)
    :param pcoll: Preview collection
    :return: Original enum_items parameter with the items from the asset library
    """
    if os.path.isdir(root):
        for category in os.listdir(root):
            scan_for_assets_category(os.path.join(root, category), enum_items, pcoll)
    return enum_items



# Import button
class KAM_ImportObjectButton(bpy.types.Operator):
    bl_idname = "asset_manager.import_object"
    bl_label = "Append Object"
    bl_description = 'Appends object to scene'
    link : BoolProperty(False)

    def execute(self, context):
        import_object(context, link=self.link)
        return {'FINISHED'}


# Import button
class KAM_ImportMaterialButton(bpy.types.Operator):
    bl_idname = "asset_manager.import_material"
    bl_label = "Import Material"
    bl_description = 'Imports material to scene'

    def execute(self, context):
        import_material(context, link=False)
        return {'FINISHED'}

# Import button
class KAM_ImportHDR(bpy.types.Operator):
    bl_idname = "asset_manager.import_hdr"
    bl_label = "Import HDR"
    bl_description = "Imports an HDR into the world material"

    def execute(self, context):
        if context.scene.asset_manager.blend == 'cycles':
            import_hdr_cycles(context)
        else:
            import_hdr_corona(context)
        
        return {'FINISHED'}


class KAM_LinkToButton(bpy.types.Operator):
    bl_idname = "asset_manager.link_to"
    bl_label = "Go to iMeshh"
    bl_description = 'Imports material to scene'

    def execute(self, context):
        webbrowser.open('https://imeshh.com/')
        return {'FINISHED'}


def select(obj):
    if is_2_80():
        obj.select_set(True)
    else:
        obj.select = True

def get_data_colls():
    if hasattr(bpy.data, "collections"):
        return bpy.data.collections
    elif hasattr(bpy.data, "groups"):
        return bpy.data.groups

# Get the selected file (either a blend or an HDR)
def get_selected_file(context):
    return context.window_manager.asset_manager_prevs


def get_selected_blend(context):
    file = get_selected_file(context)

    if is_blend(file):
        if context.scene.asset_manager.blend == 'corona':
            return file.replace('Cycles', 'Corona')
        else:
            return file.replace('Corona', 'Cycles')


def get_selected_hdr(context):
    file = get_selected_file(context)
    if is_hdr(file):
        return file


def selectable_objects(context):
    if is_2_80():
        return context.view_layer.objects
    return context.scene.objects


# Import objects into current scene.
def import_object(context, link):
    # active_layer = context.view_layer.active_layer_collection

    # Deselect all objects
    if  bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
    bpy.ops.object.select_all(action='DESELECT')

    # 2.79 and 2.80 killing me.
    if is_2_80():
        if 'Assets' not in bpy.context.scene.collection.children.keys():
            asset_coll = bpy.data.collections.new('Assets')
            context.scene.collection.children.link(asset_coll)

    blend = get_selected_blend(context)
    if blend:
        append_blend(blend, link)

def create_instance_collection(collection, parent_collection):
    empty = bpy.data.objects.new(name = collection.name, object_data = None)
    empty.instance_collection = collection
    empty.instance_type = 'COLLECTION'
    parent_collection.objects.link(empty)
    return empty

def select_coll_to_import(collection_names):
    """ Select wich collection import following the file type and user preferences
    - collection_names : collections names array avalaibles in the blender file
    """
    #file has no collections (blander version < blender 2.80)
    if not collection_names:
        return None
    
    #User ask for import all collections of blend file
    if bpy.context.window_manager.asset_manager_collection_import == True:
        return collection_names

    # there is a collection call 'Collection'
    if 'Collection' in collection_names:
        return ['Collection']
    
    # there is no 'Collection' but something like 'Collection.xxx'
    colls = []
    for col in collection_names:
        if re.match(r'(^collection)', col, re.IGNORECASE):
            colls.append(col)
    if colls:
        return colls
    #there is collection but no match, import all
    else:
        return collection_names

def link_collections(blend_file, parent_col):
    """ Import collections of a blend file as instances collection if it's possible
    - blend_file : file with collection to import
    - parent_col : collection of actual file wich will get as child news instances collections
    """
    objects_linked = False
    with bpy.data.libraries.load(blend_file, link = True) as (data_from, data_to):
        data_to.collections = select_coll_to_import(data_from.collections)
        if data_to.collections == None:
            objects_linked = True
            data_to.objects = data_from.objects
    
    # fix if color space unrecognized
    for img in bpy.data.images:
        if img.colorspace_settings.name == '':
            img.colorspace_settings.name = 'sRGB'
    #no collection found in blend file
    if objects_linked:
        for obj in data_to.objects:
            if bpy.context.window_manager.asset_manager_ignore_camera and obj.type == 'CAMERA':
                continue
            parent_col.objects.link(obj)
            select(obj)
    else:
        #create all instances collections
        for col in data_to.collections:
            instance = create_instance_collection(col, parent_col)
            if re.match(r'(^collection)', instance.name, re.IGNORECASE) and bpy.context.window_manager.asset_manager_auto_rename == True:
                instance.name = parent_col.name
            select(instance)

# Import blend file
def append_blend(blend_file, link=False):
    coll_name = os.path.splitext(os.path.basename(blend_file))[0].title()
    obj_coll = get_data_colls().new(coll_name)

    if is_2_80():
        asset_coll = get_data_colls()['Assets']
        asset_coll.children.link(obj_coll)

    if not link:
        with bpy.data.libraries.load(blend_file, link = link) as (data_from, data_to):
            data_to.objects = data_from.objects
        
        # fix if color space unrecognized
        for img in bpy.data.images:
            if img.colorspace_settings.name == '':
                img.colorspace_settings.name = 'sRGB'

        for obj in data_to.objects:
            if bpy.context.window_manager.asset_manager_ignore_camera and obj.type == 'CAMERA':
                continue
            obj_coll.objects.link(obj)
            select(obj)
    else:
        link_collections(blend_file, obj_coll)

    bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)

# Import objects into current scene.
def import_material(context, link):
    active_ob = context.active_object
    if bpy.ops.object.mode_set.poll(): 
        bpy.ops.object.mode_set(mode='OBJECT', toggle = False)
    bpy.ops.object.select_all(action='DESELECT')

    blend = get_selected_blend(context)
    files = []
    with bpy.data.libraries.load(blend) as (data_from, data_to):
        for name in data_from.materials:
            files.append({'name': name})
    action = bpy.ops.wm.link if link else bpy.ops.wm.append
    action(directory=blend + "/Material/", files=files)

    if active_ob is not None:
        for file in files:
            mat = bpy.data.materials[file['name']]
            active_ob.data.materials.append(mat)
            select(active_ob)

def import_hdr_cycles(context):
    hdr = get_selected_hdr(context)

    if not hdr:
        return

    scene = context.scene
    world = scene.world
    world.use_nodes = True
    node_tree = world.node_tree

    path_nodes_blend = os.path.join(os.path.dirname(__file__), 'hdrinodes.blend')
    
    if not 'OUTPUTNODE' in node_tree.nodes:
        node_output = None
        for node in node_tree.nodes:
            if node.bl_idname == 'ShaderNodeOutputWorld':
                node_output = node
        if not node_output:        
            node_output = node_tree.nodes.new("ShaderNodeOutputWorld")
        node_output.name = 'OUTPUTNODE'
    else:
        node_output = node_tree.nodes['OUTPUTNODE']

    if not 'Ground Projection Off/On' in bpy.data.node_groups or not 'HDRI Nodes' in bpy.data.node_groups:
        with bpy.data.libraries.load(path_nodes_blend, link = False) as (data_from, data_to):
            data_to.node_groups = data_from.node_groups

    if not 'HDRI_GROUP' in node_tree.nodes:
        hdri_group = node_tree.nodes.new('ShaderNodeGroup')
        hdri_group.name = 'HDRI_GROUP'
        hdri_group.node_tree = bpy.data.node_groups['HDRI Nodes']
    else:
        hdri_group = node_tree.nodes['HDRI_GROUP']

    if not 'GROUND_PROJECTION' in node_tree.nodes:
        ground_projection = node_tree.nodes.new('ShaderNodeGroup')
        ground_projection.name = 'GROUND_PROJECTION'
        ground_projection.node_tree = bpy.data.node_groups['Ground Projection Off/On']
    else:
        ground_projection = node_tree.nodes['GROUND_PROJECTION']
    
    if not 'ENVTEX' in node_tree.nodes:
        node_env_tex = node_tree.nodes.new("ShaderNodeTexEnvironment")
        node_env_tex.name = 'ENVTEX'
    else:
        node_env_tex = node_tree.nodes['ENVTEX']

    nodes = [
        node_output,
        hdri_group,
        node_env_tex,
        ground_projection,
    ]
    x = 600

    for i, node in enumerate(nodes):
        x -= nodes[i].width
        x -= 80
        node.location.x = x

    node_tree.links.new(ground_projection.outputs["Color"], node_env_tex.inputs["Vector"])
    node_tree.links.new(node_env_tex.outputs["Color"], hdri_group.inputs["HDRI"])
    node_tree.links.new(hdri_group.outputs["Shader"], node_output.inputs["Surface"])

    # Load in the HDR
    hdr_image = bpy.data.images.load(hdr)
    node_env_tex.image = hdr_image

def import_hdr_corona(context):
    hdr = get_selected_hdr(context)

    if not hdr:
        return

    corona = context.scene.world.corona
    corona.mode = 'latlong'
    corona.enviro_tex = hdr

def update_hdri_strength_corona(corona, strength):
    corona.map_gi.intensity = strength

def update_hdri_rotation_corona(corona, rotation):
    corona.latlong_enviro_rotate = rotation


preview_collections = {}

# Classes to register
classes = (
    KAM_PrefPanel,
    KAM_SettingsPanel,
    KAM_MakeFolder,
    KAM_Panel,
    KAM_OpenBlend,
    KAM_OpenThumbnail,
    KAM_ImportHDR,
    KAM_ImportObjectButton,
    KAM_ImportMaterialButton,
    KAM_LinkToButton,
    KrisAssetManager,
)

def select_tab(self, context):
    if get_selected_hdr(context):
        context.scene.asset_manager.tabs = 'HDRI'
    


# Register classes and ...
def register():
    # Initialize addon updater
    addon_updater_ops.register(bl_info)

    for cls in classes:
        bpy.utils.register_class(cls)

    WindowManager.asset_manager_prev_dir = StringProperty(
        name="Folder Path",
        subtype='DIR_PATH',
        default="")
    
    WindowManager.asset_manager_ignore_camera = BoolProperty(
        name="Ignore camera when importing",
        default=True,
        description="This addon will ignore all cameras by default. If you want to import cameras then untick this box")
    
    WindowManager.asset_manager_collection_import = BoolProperty(
        name="Import other collections if available",
        default=False,
        description="If there are multiple collections in this file, and you don't want to just import the scene collection, then tick this box")
    
    WindowManager.asset_manager_auto_rename = BoolProperty(
        name="Auto rename Collection to file name",
        default=True,
        description="This addon, by default, will just import the scene collection. This will then auto-rename the scene collection to the assets file name. This will make it easier to find in the library")


    WindowManager.asset_manager_prevs = EnumProperty(items=scan_directory, update=select_tab)

    pcoll = bpy.utils.previews.new()
    pcoll.asset_manager_prev_dir = ""
    pcoll.asset_manager_prevs = ""

    preview_collections["main"] = pcoll
    bpy.types.Scene.asset_manager = PointerProperty(type=KrisAssetManager)


# Unregister
def unregister():
    addon_updater_ops.unregister()

    del WindowManager.asset_manager_prevs
    del WindowManager.asset_manager_ignore_camera
    
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)

    preview_collections.clear()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.asset_manager


if __name__ == "__main__":
    register()
