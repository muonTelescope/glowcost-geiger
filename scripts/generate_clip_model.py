"""Generate a datasheet-derived 10207101009 clip (mm); requires FreeCAD Python.
Origin: PCB top, midpoint of the two tails. X: tail pitch / tube axis.
Spring bends and seating envelope approximate; not manufacturer production CAD.
"""
from pathlib import Path
import math,json,hashlib
import FreeCAD as App, Part, MeshPart
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'cad/models/C142864';OUT.mkdir(parents=True,exist_ok=True)
V=App.Vector
# Front-view inner spring profile. R3.2 about z=7.2 is specified;
# transitions to base and flared mouth are reconstructed from the drawing.
profile=[(3.45,0.5),(3.45,1.25),(2.5,2.8)]
for i in range(25):
 a=math.radians(-55+(55+56.85)*i/24)
 profile.append((3.2*math.cos(a),7.2+3.2*math.sin(a)))
profile.extend([(1.75,10.25),(2.25,10.9)])
# Horizontal 0.5 mm offset is an approximation to formed-sheet thickness.
# Keep maximum outer width 7.9 mm and mouth 4.5 mm inner opening.
solids=[]
for sign in [-1,1]:
 points=[V(-3.5,sign*y,z) for y,z in profile]+[V(-3.5,sign*(y+0.5),z) for y,z in reversed(profile)]
 wire=Part.makePolygon(points+[points[0]])
 solids.append(Part.Face(wire).extrude(V(7,0,0)))
solids.append(Part.makeBox(7,7.9,0.5,V(-3.5,-3.95,0)))
for x in [-3.8,3.8]:
 solids.append(Part.makeBox(.5,1.5,4.1,V(x-.25,-.75,-3.6)))
 # Reconstructed bent landing connecting the axial tail to the base.
 solids.append(Part.makeBox(.8,1.5,.5,V(-4.05 if x<0 else 3.25,-.75,0)))
shape=solids[0]
for s in solids[1:]:shape=shape.fuse(s)
shape=shape.removeSplitter();assert shape.isValid() and len(shape.Solids)==1
box=shape.BoundBox
assert abs(box.ZMax-10.9)<1e-6 and abs(box.ZMin+3.6)<1e-6
assert abs(box.YLength-7.9)<1e-6
shape.exportStep(str(OUT/'C142864.step'))
mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.025,AngularDeflection=.15,Relative=False);mesh.write(str(OUT/'C142864.stl'))
doc=App.newDocument('C142864');obj=doc.addObject('PartDesign::Feature','Clip');obj.Label='10207101009 — datasheet approximation';obj.Shape=shape;doc.recompute();doc.saveAs(str(OUT/'C142864.FCStd'))
# Reopen STEP to check serialization, not just in-memory geometry.
check=Part.Shape();check.read(str(OUT/'C142864.step'));assert check.isValid() and len(check.Solids)==1
report={'part':'Littelfuse 10207101009 / C142864','units':'mm','origin':'PCB top at tail midpoint','axes':'X tail pitch and tube axis; Z up','source':'datasheet.pdf, 102071 drawing, revised 2015-02-16','source_sha256':hashlib.sha256((OUT/'datasheet.pdf').read_bytes()).hexdigest(),'dimensions':{'pin_pitch':7.6,'tail_section':[.5,1.5],'tail_below_board':3.6,'height_above_board':10.9,'body_axial_width':7,'base_transverse_width':7.9,'inner_radius':3.2,'radius_center_height':7.2,'mouth_inner_width':4.5,'throat_inner_width':3.5},'bounds_mm':[box.XLength,box.YLength,box.ZLength],'checks':{'valid_solid':True,'solid_count':1,'step_roundtrip_valid':True},'approximations':['formed-sheet sidewall uses horizontal 0.5 mm offset rather than constant normal thickness','undimensioned spring transitions, flare heights, landing bends and bend radii','omits embossing, edge rounds, stamping details and spring deflection'],'usage':'placement visualization only; actual loaded seating and electrical clearances require validation','assembly':'DNP at JLC, fitted by user'}
(OUT/'model.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['checks']))
