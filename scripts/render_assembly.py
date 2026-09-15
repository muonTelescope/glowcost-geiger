"""Render current routed JSON with recovered tube and reconstructed clips.
Generic component body heights are illustrative, not collision qualification.
"""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/layout'
rows=json.loads((OUT/'circuit.json').read_text());source={r['source_component_id']:r for r in rows if r['type']=='source_component'}
bpy.ops.wm.read_factory_settings(use_empty=True)
def mat(name,color,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.35;return m
mask=mat('Green soldermask',(.015,.11,.047));gold=mat('Exposed pads',(.6,.42,.12),.7);tin=mat('Tin clips',(.65,.69,.72),.8);ceramic=mat('Generic capacitors',(.45,.40,.28));black=mat('Generic bodies',(.06,.065,.07));tubeMat=mat('Recovered tube metal',(.48,.40,.20),.7);copper=mat('Copper routing under mask',(.025,.19,.075))
def box(name,center,dims,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.name=name;o.dimensions=dims;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(material);return o
board=next(r for r in rows if r['type']=='pcb_board');outline=board['outline'];n=len(outline);verts=[(p['x'],p['y'],z) for z in [-1.6,0] for p in outline];faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
mesh=bpy.data.meshes.new('Board');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('Board',mesh);bpy.context.collection.objects.link(o);o.data.materials.append(mask)
for r in rows:
 if r['type'] in ('pcb_hole','pcb_plated_hole','pcb_via'):
  bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r['hole_diameter']/2,depth=2,location=(r['x'],r['y'],-.8));cut=bpy.context.object;mod=o.modifiers.new('Drill','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
  if r['type']!='pcb_hole':
   ro=r.get('outer_diameter',r.get('outer_diameter',3.5))/2;ri=r['hole_diameter']/2
   v=[(r['x']+radius*math.cos(i*math.tau/32),r['y']+radius*math.sin(i*math.tau/32),.02) for radius in [ri,ro] for i in range(32)];f=[(i,(i+1)%32,(i+1)%32+32,i+32) for i in range(32)];m=bpy.data.meshes.new('Annulus');m.from_pydata(v,[],f);obj=bpy.data.objects.new('Annulus',m);bpy.context.collection.objects.link(obj);obj.data.materials.append(gold)
 if r['type']=='pcb_smtpad':
  pad=box('Pad',(r['x'],r['y'],.02),(r.get('width',.6),r.get('height',.6),.04),gold);pad.rotation_euler.z=math.radians(r.get('ccw_rotation',0))
 if r['type']=='pcb_trace':
  for a,b in zip(r['route'],r['route'][1:]):
   if a['route_type']!='wire' or b['route_type']!='wire' or a['layer']!=b['layer']:continue
   z=.012 if a['layer']=='top' else -1.612
   curve=bpy.data.curves.new('Trace','CURVE');curve.dimensions='3D';curve.bevel_depth=a['width']/2;curve.bevel_resolution=1;sp=curve.splines.new('POLY');sp.points.add(1);sp.points[0].co=(a['x'],a['y'],z,1);sp.points[1].co=(b['x'],b['y'],z,1);obj=bpy.data.objects.new('Trace',curve);bpy.context.collection.objects.link(obj);obj.data.materials.append(copper)
for r in rows:
 if r['type']!='pcb_component':continue
 name=source[r['source_component_id']]['name'];x=r['center']['x'];y=r['center']['y']
 if name in ['J2','J3']:
  bpy.ops.wm.stl_import(filepath=str(ROOT/'cad/models/C142864/C142864.stl'));obj=bpy.context.object;obj.name=name+' datasheet clip';obj.location=(x,y,0);obj.rotation_euler.z=math.radians(r.get('rotation',0));obj.data.materials.append(tin);continue
 w,h=r['width']*.7,r['height']*.6;height=1.2 if name.startswith('C') else .6
 if name=='J1':w,h,height=8.25,4.25,4.25
 obj=box(name+' illustrative body',(x,y,height/2+.05),(w,h,height),ceramic if name.startswith('C') else black)
bpy.ops.wm.stl_import(filepath=str(ROOT/'cad/models/tube.stl'));tube=bpy.context.object;tube.name='Recovered tube - nominal seating';tube.location.z=7.2;tube.data.materials.append(tubeMat)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.world=bpy.data.worlds.new('World');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.1,.12,.15,1)
for loc,power,size in [((0,-60,110),220000,90),((-70,30,70),160000,80),((70,50,60),190000,60)]:
 bpy.ops.object.light_add(type='AREA',location=loc);l=bpy.context.object;l.data.energy=power;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';camera.data.ortho_scale=137;scene.camera=camera
scene.render.resolution_x=1600;scene.render.resolution_y=850;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
for name,loc,visible in [('assembled',(75,-110,95),True),('board-top',(0,-35,140),False),('tube-side',(10,-140,20),True)]:
 camera.location=loc;camera.rotation_euler=(Vector((0,0,3))-camera.location).to_track_quat('-Z','Y').to_euler();tube.hide_render=not visible;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'assembly.blend'))
(OUT/'assembly-models.json').write_text(json.dumps({'tube':'recovered mesh, user-confirmed match','clips':'datasheet-derived approximation','tube_axis_height_mm':7.2,'tube_nominal_underside_mm':1.7,'other_bodies':'illustrative generic boxes; heights not validated','clearance_status':'NOT verified; spring-loaded seating, exact bodies and HV spacing pending'},indent=2)+'\n')
