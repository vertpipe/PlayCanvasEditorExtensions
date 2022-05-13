import bpy
import json
import os
import os.path

def arrange_nodes():
    for area in bpy.context.screen.areas:
        if area.type == 'NODE_EDITOR':
            for region in area.regions:
                if region.type == 'WINDOW':
                    ctx = bpy.context.copy()
                    ctx['area'] = area
                    ctx['region'] = region
                    bpy.ops.node.button(ctx, "INVOKE_DEFAULT")

'''
code from:https://github.com/CGArtPython/bpy_building_blocks/blob/main/src/bpybb/utils.py
'''
import contextlib

def active_object():
    return bpy.context.active_object

def make_active(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

@contextlib.contextmanager
def editmode():
    # enter editmode
    bpy.ops.object.editmode_toggle()

    yield  # return out of the function in editmode

    # when leaving the context manager scope - exit editmode
    bpy.ops.object.editmode_toggle()


def purge_orphans():
    if bpy.app.version >= (3, 0, 0):
        bpy.ops.outliner.orphans_purge(
            do_local_ids=True, do_linked_ids=True, do_recursive=True
        )
    else:
        # call purge_orphans() recursively until there are no more orphan data blocks to purge
        result = bpy.ops.outliner.orphans_purge()
        if result.pop() != "CANCELLED":
            purge_orphans()

def clean_scene():
    """
    Removing all of the objects, collection, materials, particles,
    textures, images, curves, meshes, actions, nodes, and worlds from the scene
    """
    if bpy.context.active_object and bpy.context.active_object.mode == "EDIT":
        bpy.ops.object.editmode_toggle()

    for obj in bpy.data.objects:
        obj.hide_set(False)
        obj.hide_select = False
        obj.hide_viewport = False
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    collection_names = [col.name for col in bpy.data.collections]
    for name in collection_names:
        bpy.data.collections.remove(bpy.data.collections[name])

    # in the case when you modify the world shader
    world_names = [col.name for col in bpy.data.worlds]
    for name in world_names:
        bpy.data.worlds.remove(bpy.data.worlds[name])
    # create a new world data block
    bpy.ops.world.new()
    bpy.context.scene.world = bpy.data.worlds["World"]

    purge_orphans()

'''
setup function
1 clean up the scene
2 enable some add ons
'''
def setup():
    clean_scene()
    #enable node arrange plugin
    bpy.ops.preferences.addon_enable(module = "node_arrange")

'''
@TODO: unzip file and copy to folder
'''

'''
Get section index from a mesh name
'''
def get_section_id(mesh_name):
    section_id = int(mesh_name.split(".")[0].replace("Mesh_",""))
    return section_id

'''
find a glb file in a mesh path
'''
def find_glb(folder_path):
    glb_files = []
    for f in os.listdir(folder_path):
        if f.endswith(".glb"):
            glb_files.append(os.path.join(folder_path,f))
    return glb_files

'''
get all mesh in children, recursively.
'''
def get_all_mesh(obj, lst):
    if(obj.type == "MESH"):
        lst.append(obj)
        return
    if len(obj.children) > 0:
        for o in obj.children:
            get_all_mesh(o, lst)
    return
    
'''
import a single glb file
create a material 
assign parameter and materials to the nodes
'''
def import_glb(folder_path,glb_file):
    
    # import json file and prepare the materials first
    glb_json_file = glb_file.replace(".glb", ".mapping.json")
    
    if not os.path.exists(glb_json_file):
        print("glb json file is missing!")
        return 
    
    # process glb json file from playcanvas
    f = open(glb_json_file)
    data = json.load(f)
    mappings = data["mapping"]
    section_id = 0
    
    # the list of all the material keys used by the mesh in sequential order
    mesh_mat_keys = []
    for m in mappings:
        mat_json_path = m["path"]
        
        
        print(mat_json_path)
        
        
        mesh_mat_keys.append(mat_json_path)
    
    # create material set
    mats_json_unique = set(mesh_mat_keys)
    # material from json
    mat_dict = {}
    for mat_json in mats_json_unique:
        cur_mat = material_from_json(folder_path,mat_json)
        mat_dict[mat_json] = cur_mat
    
    # import glb file
    bpy.ops.import_scene.gltf(filepath=glb_file)
    obj = bpy.context.active_object
    
    # rename the root_object
    obj.name = os.path.split(glb_file)[1]
    mesh_sections = []
    
    #get all mesh recursively
    get_all_mesh(obj, mesh_sections)
    
    # assgin the materials
    for section in mesh_sections:
        mesh = section.data
        section_id = get_section_id(mesh.name)
        mat_to_assign = mat_dict[mesh_mat_keys[section_id]] # assign material to this section id
        mesh.materials.append(mat_to_assign) # @TODO: append should be OK at the moment? cuz its's newly created


CONST_DEFAULT_TEX_PATH = "G:/WORK/LOD/MaterialMergeWork/common_resources/white.jpg"
CONST_FLAT_NORMAL_PATH = "G:/WORK/LOD/MaterialMergeWork/common_resources/flat.jpg"

KEY_DIFFUSE_MAP = "diffuseMap"
KEY_DIFFUSE_COLOR = "diffuse"
KEY_DIFFUSE_MAP_OFFSET = "diffuseMapOffset"
KEY_DIFFUSE_MAP_TILING = "diffuseMapTiling"

KEY_NORMAL_MAP = "normalMap"
KEY_NORMAL_MAP_OFFSET = "normalMapOffset"
KEY_NORMAL_MAP_TILING = "normalMapTiling"

KEY_AO_MAP = "aoMap"
KEY_AO_MAP_CHANNEL = "aoMapChannel" # r = 0 , g = 1, b = 2
KEY_AO_MAP_TILING = "aoMapTiling"
KEY_AO_MAP_OFFSET = "aoMapOffset"

KEY_EMISSIVE_MAP = "emissiveMap"
KEY_EMISSIVE_COLOR = "emissive"
KEY_EMISSIVE_INTENSITY = "emissiveIntensity"
KEY_EMISSIVE_MAP_OFFSET = "emissiveMapOffset"
KEY_EMISSIVE_MAP_TILING = "emissiveMapTiling"
KEY_EMISSIVE_MAP_CHANNEL = "emissiveMapChannel"


'''
find existing image files otherwise create new image
'''
def find_load_image(image_path):
    image_key = os.path.basename(image_path)
    if image_key not in bpy.data.images:
        return bpy.data.images.load(image_path)
    else:
        bpy.data.images[image_key].reload()
        return bpy.data.images[image_key]
    
    return None

def load_link_normal(mat, normal_map_path, normal_map_offset, normal_map_tiling):
    #load normal map
    image_normal = find_load_image(normal_map_path)
    
    #texture coordinate node  #output 
    uvmap_node = mat.node_tree.nodes.new('ShaderNodeUVMap')
    
    #normal tiling and offset
    normal_mapping_node = mat.node_tree.nodes.new('ShaderNodeMapping')
    normal_mapping_node.vector_type = 'TEXTURE'
    normal_mapping_node.inputs["Location"].default_value = (normal_map_offset[0], normal_map_offset[1], 0)
    normal_mapping_node.inputs["Scale"].default_value = (1.0/normal_map_tiling[0],1.0/normal_map_tiling[1],1)
    
    #normal texture
    normal_tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    normal_tex_node.image = image_normal
    
    normal_map_node = mat.node_tree.nodes.new('ShaderNodeNormalMap')
    
    # Link nodes from left to right
    mat.node_tree.links.new(normal_mapping_node.inputs['Vector'], uvmap_node.outputs['UV'])
    mat.node_tree.links.new(normal_tex_node.inputs['Vector'], normal_mapping_node.outputs['Vector'])
    mat.node_tree.links.new(normal_map_node.inputs['Color'], normal_tex_node.outputs['Color'])
    mat.node_tree.links.new(mat.node_tree.nodes["Principled BSDF"].inputs['Normal'], normal_map_node.outputs["Normal"])
'''
diffuse and ambient occlusion are mul together
'''
def load_link_diffuse_ao(
                        mat,
                        diffuse_image_path,
                        diffuse_color, 
                        diffuse_offset, 
                        diffuse_tiling,
                        ao_image_path,
                        ao_offset,
                        ao_tiling,
                        ):
    # load diffuse image
    image_diffuse = find_load_image(diffuse_image_path)
    
    # texture coordinate node, used both by diffuse and ao
    uvmap_node = mat.node_tree.nodes.new('ShaderNodeUVMap')
    
    # diffuse tiling and offset
    diffuse_mapping_node = mat.node_tree.nodes.new('ShaderNodeMapping')
    diffuse_mapping_node.vector_type = 'TEXTURE'
    diffuse_mapping_node.inputs["Location"].default_value = (diffuse_offset[0], diffuse_offset[1], 0)
    diffuse_mapping_node.inputs["Scale"].default_value = (1.0/diffuse_tiling[0],1.0/diffuse_tiling[1],1)
    
    # diffuse texture
    diffuse_tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    diffuse_tex_node.image = image_diffuse
    
    # diffuse_color
    diffuse_col_node = mat.node_tree.nodes.new("ShaderNodeRGB")
    diffuse_col_node.outputs['Color'].default_value = diffuse_color
    
    # create multiply node diffuse_color * diffuse_tex
    mult_diffuse_node = mat.node_tree.nodes.new('ShaderNodeMixRGB')
    mult_diffuse_node.blend_type = 'MULTIPLY'
    
    # load ao image
    image_ao = find_load_image(ao_image_path)

    # ao tiling and offset
    ao_mapping_node = mat.node_tree.nodes.new('ShaderNodeMapping')
    ao_mapping_node.vector_type = 'TEXTURE'
    ao_mapping_node.inputs["Location"].default_value = (ao_offset[0], ao_offset[1], 0)
    ao_mapping_node.inputs["Scale"].default_value = (1.0/ao_tiling[0],1.0/ao_tiling[1],1)

    # ao texture
    ao_tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    ao_tex_node.image = image_ao
    
    # create multiply node diffuse_color * diffuse_tex
    mult_diffuse_ao = mat.node_tree.nodes.new('ShaderNodeMixRGB')
    mult_diffuse_ao.blend_type = 'MULTIPLY'
    
    # Link diffuse mapping nodes from left to right
    mat.node_tree.links.new(diffuse_mapping_node.inputs['Vector'], uvmap_node.outputs['UV'])
    mat.node_tree.links.new(diffuse_tex_node.inputs['Vector'], diffuse_mapping_node.outputs['Vector'])
    
    # Link ao mapping nodes from left to right
    mat.node_tree.links.new(ao_mapping_node.inputs['Vector'], uvmap_node.outputs['UV'])
    mat.node_tree.links.new(ao_tex_node.inputs['Vector'], ao_mapping_node.outputs['Vector'])
    
    # multiply diffuse color with texture
    mat.node_tree.links.new(mult_diffuse_node.inputs['Color1'], diffuse_tex_node.outputs['Color'])
    mat.node_tree.links.new(mult_diffuse_node.inputs['Color2'], diffuse_col_node.outputs['Color'])
    
    # multiply ao with diffuse
    mat.node_tree.links.new(mult_diffuse_ao.inputs['Color1'], mult_diffuse_node.outputs['Color'])
    mat.node_tree.links.new(mult_diffuse_ao.inputs['Color2'], ao_tex_node.outputs['Color'])
    
    mat.node_tree.links.new(mat.node_tree.nodes["Principled BSDF"].inputs['Base Color'], mult_diffuse_ao.outputs['Color'])

'''
emissive handling
@emissive_map_channel: a color tuple: (1,1,1) for r to be multiplied 
'''
def get_color_channel_mask(channel_string):
    color = (1,1,1,1)
    if channel_string == 'rgb':
        color = (1,1,1,1)
    if channel_string == 'r':
        color = (1,0,0,0)
    if channel_string == 'g':
        color = (0,1,0,0)
    if channel_string == 'b':
        color = (0,0,1,0)
    if channel_string == 'a':
        color = (0,0,0,1)
    return color

'''

@emissive_map_channel: a color tuple: (1,1,1) for r to be multiplied 
'''
def load_link_emissive( mat,
                        emissive_image_path,
                        emissive_color,
                        emissive_tiling , 
                        emissive_offset,
                        emissive_intensity, 
                        emissive_map_channel
                        ):
    # load emissive image
    image_emissive = find_load_image(emissive_image_path)

    # texture coordinate node, used both by emissive and ao
    uvmap_node = mat.node_tree.nodes.new('ShaderNodeUVMap')

    # emissive tiling and offset
    emissive_mapping_node = mat.node_tree.nodes.new('ShaderNodeMapping')
    emissive_mapping_node.vector_type = 'TEXTURE'
    emissive_mapping_node.inputs["Location"].default_value = (emissive_offset[0], emissive_offset[1], 0)
    emissive_mapping_node.inputs["Scale"].default_value = (1.0/emissive_tiling[0],1.0/emissive_tiling[1],1)

    # emissive texture
    emissive_tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    emissive_tex_node.image = image_emissive

    # emissive_color
    emissive_col_node = mat.node_tree.nodes.new("ShaderNodeRGB")
    emissive_col_node.outputs['Color'].default_value = emissive_color

    # emissive map channel
    emissive_channel_node = mat.node_tree.nodes.new("ShaderNodeRGB")
    emissive_channel_node.outputs['Color'].default_value = emissive_map_channel

    # create multiply node emissive_map * emissive map channel
    mult_channel_node = mat.node_tree.nodes.new('ShaderNodeMixRGB')
    mult_channel_node.blend_type = 'MULTIPLY'

    # create multiply node emissive_color * mult_channel_node
    mult_final_emissive = mat.node_tree.nodes.new('ShaderNodeMixRGB')
    mult_final_emissive.blend_type = 'MULTIPLY'

    # emissive_tex_node * emissive_col_node * emissive_channel_node

    # Link emissive mapping nodes from left to right
    mat.node_tree.links.new(emissive_mapping_node.inputs['Vector'], uvmap_node.outputs['UV'])
    mat.node_tree.links.new(emissive_tex_node.inputs['Vector'], emissive_mapping_node.outputs['Vector'])

    # multiply emissive map * emissive channel 
    mat.node_tree.links.new(mult_channel_node.inputs['Color1'], emissive_tex_node.outputs['Color'])
    mat.node_tree.links.new(mult_channel_node.inputs['Color2'], emissive_channel_node.outputs['Color'])

    # multiply mult_channel_node * emissive color 
    mat.node_tree.links.new(mult_final_emissive.inputs['Color1'], mult_channel_node.outputs['Color'])
    mat.node_tree.links.new(mult_final_emissive.inputs['Color2'], emissive_col_node.outputs['Color'])
    
    # final emission output
    mat.node_tree.links.new(mat.node_tree.nodes["Principled BSDF"].inputs['Emission'], mult_final_emissive.outputs['Color'])
    
    # final emission intensity output
    mat.node_tree.nodes["Principled BSDF"].inputs['Emission Strength'].default_value = emissive_intensity


'''
create material and assign parameters
'''
def material_from_json(folder_path, mat_json):
    if mat_json == None:
       return None 
    mat_id = os.path.splitext(mat_json)[0].replace("/", "_")
    mat_pc_obj = parse_material_json(os.path.join(folder_path, mat_json))
    bmat = None
    
    # find or create material
    if mat_id in bpy.data.materials:
        bmat = bpy.data.materials[mat_id]
    else:
        bmat = bpy.data.materials.new(name=mat_id)
    
    bmat.use_nodes = True
    bmat_nodes = bmat.node_tree.nodes
    bmat_links = bmat.node_tree.links
    
    bsdf = bmat_nodes["Principled BSDF"]
    
    # handle diffuse color and diffuse texture
    diffuse_col = (1,1,1,1)
    diffuse_offset = (0,0)
    diffuse_tiling = (1,1)
    diffuse_tex_path = CONST_DEFAULT_TEX_PATH
    
    if KEY_DIFFUSE_COLOR in mat_pc_obj.keys():
        c = mat_pc_obj[KEY_DIFFUSE_COLOR]
        diffuse_col = (c[0], c[1], c[2], 1)
    if KEY_DIFFUSE_MAP in mat_pc_obj.keys():
        diffuse_tex_path = mat_pc_obj[KEY_DIFFUSE_MAP].replace("../","") # remove parent layer
        diffuse_tex_path = os.path.join(folder_path,diffuse_tex_path)
    if KEY_DIFFUSE_MAP_OFFSET in mat_pc_obj.keys():
        diffuse_offset = mat_pc_obj[KEY_DIFFUSE_MAP_OFFSET]
    if KEY_DIFFUSE_MAP_TILING in mat_pc_obj.keys():
        diffuse_tiling = mat_pc_obj[KEY_DIFFUSE_MAP_TILING]
    
    # handle ao texture
    ao_offset = (0,0)
    ao_tiling = (1,1)
    ao_tex_path = CONST_DEFAULT_TEX_PATH
    
    if KEY_AO_MAP in mat_pc_obj.keys():
        ao_tex_path = mat_pc_obj[KEY_AO_MAP].replace("../","") # remove parent layer
        ao_tex_path = os.path.join(folder_path,ao_tex_path)
    if KEY_AO_MAP_OFFSET in mat_pc_obj.keys():
        ao_offset = mat_pc_obj[KEY_AO_MAP_OFFSET]
    if KEY_AO_MAP_TILING in mat_pc_obj.keys():
        ao_tiling = mat_pc_obj[KEY_AO_MAP_TILING]
    
    
    # diffuse and ao nodes creation and linking
    load_link_diffuse_ao(
                        bmat, 
                        diffuse_tex_path, 
                        diffuse_col,
                        diffuse_offset,
                        diffuse_tiling, 
                        ao_tex_path, 
                        ao_offset, 
                        ao_tiling)
    
    # handle normal texture
    normal_map_offset = (0,0)
    normal_map_tiling = (1,1)
    normal_map_path = CONST_FLAT_NORMAL_PATH
    if KEY_NORMAL_MAP in mat_pc_obj.keys():
        normal_map_path = mat_pc_obj[KEY_NORMAL_MAP].replace("../","") # remove parent layer
        normal_map_path = os.path.join(folder_path,normal_map_path)
    if KEY_NORMAL_MAP_OFFSET in mat_pc_obj.keys():
        normal_offset = mat_pc_obj[KEY_NORMAL_MAP_OFFSET]
    if KEY_NORMAL_MAP_TILING in mat_pc_obj.keys():
        normal_tiling = mat_pc_obj[KEY_NORMAL_MAP_TILING]
    
    load_link_normal(bmat, normal_map_path, normal_map_offset, normal_map_tiling)
    
    # handle emission texture
    #@TODO: emissiveMapTint
    emissive_map_offset = (0,0)
    emissive_map_tiling = (1,1)
    emissive_map_path = CONST_DEFAULT_TEX_PATH
    emissive_color = (1,1,1,1)
    emissive_intensity = 1.0
    emissive_map_channel = (1,1,1,1) # default
    
    if KEY_EMISSIVE_MAP in mat_pc_obj.keys():
        emissive_map_path = mat_pc_obj[KEY_EMISSIVE_MAP].replace("../","")
        emissive_map_path = os.path.join(folder_path,emissive_map_path)
    if KEY_EMISSIVE_COLOR in mat_pc_obj.keys():
        c = mat_pc_obj[KEY_EMISSIVE_COLOR]
        emissive_color = (c[0], c[1], c[2], 1)
    if KEY_EMISSIVE_INTENSITY in mat_pc_obj.keys():
        emissive_intensity = mat_pc_obj[KEY_EMISSIVE_INTENSITY]
    if KEY_EMISSIVE_MAP_OFFSET in mat_pc_obj.keys():
        emissive_map_offset = mat_pc_obj[KEY_EMISSIVE_MAP_OFFSET]
    if KEY_EMISSIVE_MAP_TILING in mat_pc_obj.keys():
        emissive_map_tiling = mat_pc_obj[KEY_EMISSIVE_MAP_TILING]
    if KEY_EMISSIVE_MAP_CHANNEL in mat_pc_obj.keys():
        emissive_map_channel = get_color_channel_mask(mat_pc_obj[KEY_EMISSIVE_MAP_CHANNEL])
        
    # and ao nodes creation and linking
    load_link_emissive( bmat,
                        emissive_map_path,
                        emissive_color,
                        emissive_map_tiling , 
                        emissive_map_offset,
                        emissive_intensity, 
                        emissive_map_channel
                        )
    
    #arrange all the nodes
    arrange_nodes()
    
    # @TODO: other parameters
    
    return bmat
        
'''
parse the material json and get parameter object
'''
def parse_material_json(mat_json_path):
    if os.path.exists(mat_json_path):
        f = open(mat_json_path)
        data = json.load(f)
        return data
    return None

'''
parse the mesh folder 
and read glb 
and the corresponding json files
'''    
def load_mesh_folder(folder_path):    
    glb_files = find_glb(folder_path)
    for glb in glb_files:
        import_glb(folder_path,glb)
        

# Playcanvas Bridge UI 
class PlayCanvasBridge(bpy.types.Panel):
    bl_label = "PlayCanvas Bridge"
    bl_idname = "PT_PlayCanvasBridge"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PlayCanvas"
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        row.label(text = "Sample Text", icon = "CUBE")
        row.operator("load playcanvas material")

def register():
    bpy.utils.register_class(PlayCanvasBridge)
    
def unregister():
    bpy.utils.unregister_class(PlayCanvasBridge)
    

if __name__ == "__main__":
    # mesh_list = []
    # get_all_mesh(bpy.context.active_object, mesh_list)
    # print(mesh_list)
    # register()
    # setup()
    # load_mesh_folder("G:/WORK/LOD/MirrorModels")
    # load_mesh_folder("G:/WORK/LOD/MaterialMergeWork/WHOLESCENE")
    load_mesh_folder("G:/WORK/LOD/MaterialMergeWork/FIX_MID9")