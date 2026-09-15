"""Extract the user-confirmed tube mesh; run with Blender --background --python."""
import bpy, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'cad/reference/wirelessGeigerCounter/cad/blender/transmitter.blend'))
o=bpy.data.objects['SBM-20']
# Legacy geometry uses approximately 10.8 units for a 108 mm tube.
# Convert to millimetres, preserve proportions, orient longest axis along X.
mesh=o.to_mesh();verts=[o.matrix_world @ v.co for v in mesh.vertices]
lo=Vector([min(v[i] for v in verts) for i in range(3)]);hi=Vector([max(v[i] for v in verts) for i in range(3)])
center=(lo+hi)/2
xyz=[((v.z-center.z)*10,(v.x-center.x)*10,(v.y-center.y)*10) for v in verts]
faces=[tuple(p.vertices) for p in mesh.polygons]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
m=bpy.data.meshes.new('RecoveredTube');m.from_pydata(xyz,[],faces);m.update();obj=bpy.data.objects.new('Recovered SBM-20 tube',m);bpy.context.collection.objects.link(obj);obj.select_set(True);bpy.context.view_layer.objects.active=obj
out=ROOT/'cad/models';out.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.stl_export(filepath=str(out/'tube.stl'),export_selected_objects=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'tube.blend'))
(out/'tube.json').write_text(json.dumps({'source_object':'SBM-20','source_file':'cad/reference/wirelessGeigerCounter/cad/blender/transmitter.blend','user_confirmed_tube_match':True,'legacy_units_to_mm':10,'dimensions_mm':[max(v[i] for v in xyz)-min(v[i] for v in xyz) for i in range(3)],'origin':'body bounding-box center; long axis X','installed_height':'not established; requires clip seating geometry'},indent=2)+'\n')
