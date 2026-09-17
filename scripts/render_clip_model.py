"""Render the generated clip STL with Blender; units are millimetres."""
import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'cad/models/C142864'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.stl_import(filepath=str(OUT/'C142864.stl'))
o=bpy.context.object
mat=bpy.data.materials.new('Tin');mat.diffuse_color=(.65,.69,.73,1);mat.use_nodes=True
bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.65,.69,.73,1);bs.inputs['Metallic'].default_value=.75;bs.inputs['Roughness'].default_value=.28;o.data.materials.append(mat)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=48
scene.world=bpy.data.worlds.new('World');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.39,.45,1);scene.view_settings.look='AgX - Medium High Contrast'
for loc,power,size in [((8,-12,20),26000,14),((-12,-3,8),20000,12),((0,12,15),30000,12)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(Vector((0,0,4))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(21,-29,19));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,3.5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=23;scene.camera=cam
scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'preview.png');bpy.ops.render.render(write_still=True)
