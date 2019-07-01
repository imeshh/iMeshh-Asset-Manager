from bpy.types import WindowManager
import bpy.utils.previews
from bpy.props import PointerProperty, StringProperty, EnumProperty, FloatProperty
import bpy
import os
import sys
import subprocess
import webbrowser

from . import addon_updater_ops

bl_info = {
    "name": "iMeshh Asset Manager",
    "version": (0, 1, 14),
    "blender": (2, 80, 0),
    "location": "View3D > TOOLS > iMeshh",
    "author": "iMeshh",
    "description": "Manager for iMeshh models",
    "category": "Assets Management"
}


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
        'Materials': ['Brick', 'Concrete', 'Fabrics', 'Ground', 'HDRI', 'Leather', 'Worktops', 'Metal', 'Paint',
                      'Plaster', 'Plastic', 'Stone', 'Tiles', 'Wood', 'Wood Floors']
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

    asset_dir = StringProperty(
        name="Assets Path",
        default=os.path.join(os.path.dirname(__file__), 'Assets'),
        description="Show only hotkeys that have this text in their name",
        subtype="DIR_PATH")

    # addon updater preferences
    auto_check_update = bpy.props.BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=False,
    )

    updater_intrval_months = bpy.props.IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0
    )
    updater_intrval_days = bpy.props.IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=7,
        min=0,
    )
    updater_intrval_hours = bpy.props.IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23
    )
    updater_intrval_minutes = bpy.props.IntProperty(
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
        row.operator("asset_manager.make_folder", icon="PROP_CON")

        addon_updater_ops.update_settings_ui(self, context)


class KAM_MakeFolder(bpy.types.Operator):
    bl_idname = "asset_manager.make_folder"
    bl_label = "Make"
    bl_description = 'Make Assets folder'

    def execute(self, context):
        root = get_root_dir(context)
        make_folders(root)
        return {'FINISHED'}


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


# Operator for popup dialog in panel
class KAM_Popup(bpy.types.Operator):
    """Acces to your Objects Library"""
    bl_idname = "view3d.kris_asset"
    bl_label = "iMeshh Asset Manager"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}


class KAM_OpenThumbnail(bpy.types.Operator):
    """Open the thumbnail image"""
    bl_idname = "asset_manager.open_thumbnail"
    bl_label = "Open Thumbnail"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_blend = bpy.data.window_managers["WinMan"].asset_manager_prevs

        for (blend_path, _, file_blend, icon_id, _) in preview_collections['main'].asset_manager_prevs:
            print(blend_path, file_blend, icon_id)
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


class KAM_OpenBlend(bpy.types.Operator):
    """Open the .blend file for the asset"""
    bl_idname = "asset_manager.open_blend"
    bl_label = "Open Thumbnail"
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

    # Categories Drop Down Menu
    col = layout.column()
    col.prop(manager, "cat")
    col.prop(manager, "subcat")

    # Thumbnail view
    if len(wm.asset_manager_prevs) != 0:
        row = layout.row()
        row.template_icon_view(wm, "asset_manager_prevs", show_labels=True)

        row = layout.row(align=True)
        row.operator("asset_manager.open_thumbnail", icon="FILE_IMAGE")
        row.operator("asset_manager.open_blend", icon="FILE_BLEND")

        row = layout.row()
        row.prop(manager, "blend", expand=True)

        if get_selected_blend(context):
            row = layout.row()
            row.operator("asset_manager.import_object", icon='APPEND_BLEND')

            row = layout.row()
            row.operator("asset_manager.import_material", icon='TEXTURE_DATA')
        elif get_selected_hdr(context):
            row = layout.row()
            row.operator("asset_manager.import_hdr", icon='TEXTURE_DATA')

            row = layout.row()
            row.prop(manager, "hdr_strength")

            row = layout.row()
            row.prop(manager, "hdr_rotation")


# Get root directory from user preferences
def get_root_dir(context=None):
    if not context:
        context = bpy.Context

    if hasattr(context, "preferences"):
        pref = context.preferences.addons[__name__].preferences
    else:
        pref = context.user_preferences.addons[__name__].preferences

    return pref.asset_dir


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

    return categories


# Update category list
def update_category(self, context):
    scan_directory(self, context)


# Fill out sub categories.
def subcategory_items(self, context):
    subcategories = [('All', 'All', '', 0)]
    index = 1
    root_dir = get_root_dir(context)

    if self.cat == 'All':
        return [('.', '.', '', 0)]

    cat_path = os.path.join(root_dir, self.cat)
    for folder in sorted(os.listdir(cat_path)):
        path = os.path.join(cat_path, folder)
        if os.path.isdir(path) and not folder.startswith('.'):
            subcategories.append((folder, folder, '', index))
            index += 1

    return subcategories


# PropertyGroup for this asset manager
class KrisAssetManager(bpy.types.PropertyGroup):
    cat = EnumProperty(
        items=category_items,
        name="Category",
        description="Select a Category",
        update=subcategory_items)

    subcat = EnumProperty(
        items=subcategory_items,
        name="Subcategory",
        description="Select subcategory",
        update=None)

    blend = EnumProperty(
        items=[('cycles', 'Cycles', '', 0), ('corona', 'Corona', '', 1)],
        name="Blend",
        description="Select blend")

    # HDR properties
    hdr_strength = FloatProperty(
        default=1,
        soft_max=1,
        soft_min=0,
        name="Sky Strength",
        description="The strength of the HDR environment"
    )

    hdr_rotation = FloatProperty(
        default=0,
        subtype="ANGLE",
        name="Environment Angle",
        description="Rotate the HDR environment to this angle"
    )


# EnumProperty(asset_manager_prevs) Callback
def scan_directory(self, context):
    root_dir = get_root_dir(context)

    category = context.scene.asset_manager.cat
    subcategory = context.scene.asset_manager.subcat
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

    if category == 'All':
        enum_items = scan_for_elements_root(root_dir, enum_items, pcoll)
    elif subcategory == 'All':
        enum_items = scan_for_elements_category(os.path.join(root_dir, category), enum_items, pcoll)
    elif directory and os.path.exists(directory):
        enum_items = scan_for_elements(directory, enum_items, pcoll)

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
    return file.lower().endswith(('.hdr', '.hdr'))


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


# Scan for images and blend file (.blend)
def scan_for_elements(directory, enum_items, pcoll):
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        file_blend = find_blend_in_path(item_path)

        for file in os.listdir(item_path):
            if is_image(file):
                img_path = os.path.join(item_path, file)
                blend_path = os.path.join(item_path, file_blend)
                if img_path in pcoll:
                    enum_items.append((blend_path, item, file_blend, pcoll[img_path].icon_id, len(enum_items)))
                else:
                    thumb = pcoll.load(img_path, img_path, 'IMAGE')
                    enum_items.append((blend_path, item, file_blend, thumb.icon_id, len(enum_items)))
                break

    return enum_items


# Scan all subcategories inside a category
def scan_for_elements_category(directory, enum_items, pcoll):
    for subcategory in os.listdir(directory):
        scan_for_elements(os.path.join(directory, subcategory), enum_items, pcoll)
    return enum_items

# Scan for images and blend file (.blend)
def scan_for_elements_root(root, enum_items, pcoll):
    image_paths = []
    i = 0

    for cat in os.listdir(root):
        cat_path = os.path.join(root, cat)
        for subcat in os.listdir(cat_path):
            subcat_path = os.path.join(cat_path, subcat)
            for item in os.listdir(subcat_path):
                item_path = os.path.join(subcat_path, item)

                file_blend = find_blend_in_path(item_path)

                for file in os.listdir(item_path):
                    if is_image(file):
                        img_path = os.path.join(item_path, file)
                        blend_path = os.path.join(item_path, file_blend)
                        if img_path in pcoll:
                            enum_items.append((blend_path, item, file_blend, pcoll[img_path].icon_id, i))
                        else:
                            thumb = pcoll.load(img_path, img_path, 'IMAGE')
                            enum_items.append((blend_path, item, file_blend, thumb.icon_id, i))

                        i = i + 1
                        break

    return enum_items


# Import button
class KAM_ImportObjectButton(bpy.types.Operator):
    bl_idname = "asset_manager.import_object"
    bl_label = "Import Object"
    bl_description = 'Appends object to scene'

    def execute(self, context):
        import_object(context, link=False)
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
        
        return {'FINISHED'}


# Import button
class KAM_LinkToButton(bpy.types.Operator):
    bl_idname = "asset_manager.link_to"
    bl_label = "Go to iMeshh"
    bl_description = 'Imports material to scene'

    def execute(self, context):
        webbrowser.open('https://imeshh.com/')
        return {'FINISHED'}


def select(obj):
    if bpy.app.version < (2, 80, 0):
        obj.select = True
    else:
        obj.select_set(True)


def deselect(obj):
    if bpy.app.version < (2, 80, 0):
        obj.select = False
    else:
        obj.select_set(False)


def get_data_colls():
    if hasattr(bpy.data, "collections"):
        return bpy.data.collections
    elif hasattr(bpy.data, "groups"):
        return bpy.data.groups


# Get the selected file (either a blend or an HDR)
def get_selected_file(context):
    return bpy.data.window_managers["WinMan"].asset_manager_prevs


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


# Import objects into current scene.
def import_object(context, link):
    # active_layer = context.view_layer.active_layer_collection

    for ob in bpy.context.scene.objects:
        deselect(ob)

    bpy.ops.object.select_all(action='DESELECT')

    # 2.79 and 2.80 killing me.
    if bpy.app.version < (2, 80, 0):
        if bpy.context.scene.objects.find('Assets') == -1:
            asset_coll = bpy.data.groups.new('Assets')
            for obj in context.scene.objects:
                asset_coll.objects.link(obj)
        else:
            asset_coll = bpy.data.groups['Assets']
    else:
        if 'Assets' not in bpy.context.scene.collection.children.keys():
            asset_coll = bpy.data.collections.new('Assets')
            context.scene.collection.children.link(asset_coll)
        else:
            asset_coll = bpy.data.collections['Assets']

    blend = get_selected_blend(context)

    if blend:
        append_blend(blend, link)

        # context.view_layer.active_layer_collection = active_layer


# Import blend file
def append_blend(blend_file, link=False):
    asset_coll = get_data_colls()['Assets']

    coll_name = os.path.splitext(os.path.basename(blend_file))[0].title()
    obj_coll = get_data_colls().new(coll_name)

    if bpy.app.version < (2, 80, 0):
        for obj in asset_coll.objects:
            obj_coll.objects.link(obj)
    else:
        asset_coll.children.link(obj_coll)

    objects = []
    if is_blend(blend_file):
        scenes = []
        with bpy.data.libraries.load(blend_file) as (data_from, data_to):
            for name in data_from.scenes:
                scenes.append({'name': name})

        action = bpy.ops.wm.link if link else bpy.ops.wm.append
        action(directory=blend_file + "/Scene/", files=scenes)

        scenes = bpy.data.scenes[-len(scenes):]
        for scene in scenes:
            if bpy.app.version < (2, 80, 0):
                for obj in scene.objects:
                    if obj.name.startswith('Camera'):
                        continue

                    bpy.context.scene.objects.link(obj)
                    objects.append(obj)
            else:
                for coll in scene.collection.children:
                    if coll.name.startswith('Collection'):
                        for object in coll.objects:
                            if object.name.startswith('Camera'):
                                continue
                            obj_coll.objects.link(object)
                            objects.append(object)

                        for sub_coll in coll.children:
                            obj_coll.children.link(sub_coll)
                    else:
                        obj_coll.children.link(coll)

            bpy.data.scenes.remove(scene)

        for obj in objects:
            select(obj)


# Import objects into current scene.
def import_material(context, link):
    active_ob = context.active_object
    for ob in bpy.context.scene.objects:
        deselect(ob)
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

    # Start from a clean slate
    node_tree.nodes.clear()

    node_output = node_tree.nodes.new("ShaderNodeOutputWorld")
    node_background = node_tree.nodes.new("ShaderNodeBackground")
    node_image_tex = node_tree.nodes.new("ShaderNodeTexImage")
    node_mapping = node_tree.nodes.new("ShaderNodeMapping")
    node_tex_coord = node_tree.nodes.new("ShaderNodeTexCoord")

    nodes = [
        node_output,
        node_background,
        node_image_tex,
        node_mapping,
        node_tex_coord
    ]
    x = 600

    for i, node in enumerate(nodes):
        x -= nodes[i].width
        x -= 80
        node.location.x += x

    node_tree.links.new(node_tex_coord.outputs['Generated'], node_mapping.inputs["Vector"])
    node_tree.links.new(node_mapping.outputs["Vector"], node_image_tex.inputs["Vector"])
    node_tree.links.new(node_image_tex.outputs["Color"], node_background.inputs["Color"])
    node_tree.links.new(node_background.outputs["Background"], node_output.inputs["Surface"])

    # Load in the HDR
    hdr_image = bpy.data.images.load(hdr)
    node_image_tex.image = hdr_image

    manager = context.scene.asset_manager

    # Set the strength
    node_background.inputs['Strength'].default_value = manager.hdr_strength

    # Set the environment rotation
    node_mapping.rotation.z = manager.hdr_rotation


preview_collections = {}

# Classes to register
classes = (
    KAM_PrefPanel,
    KAM_MakeFolder,
    KAM_Panel,
    KAM_Popup,
    KAM_OpenBlend,
    KAM_OpenThumbnail,
    KAM_ImportHDR,
    KAM_ImportObjectButton,
    KAM_ImportMaterialButton,
    KAM_LinkToButton,
    KrisAssetManager,
)


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

    WindowManager.asset_manager_prevs = EnumProperty(items=scan_directory)

    pcoll = bpy.utils.previews.new()
    pcoll.asset_manager_prev_dir = ""
    pcoll.asset_manager_prevs = ""

    preview_collections["main"] = pcoll
    bpy.types.Scene.asset_manager = PointerProperty(type=KrisAssetManager)


# Unregister
def unregister():
    addon_updater_ops.unregister()

    del WindowManager.asset_manager_prevs

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)

    preview_collections.clear()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.asset_manager


if __name__ == "__main__":
    register()
