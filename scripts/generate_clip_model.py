"""Generate a sheet-metal reconstruction of Littelfuse 10207101009."""
from pathlib import Path
import math, json, hashlib
import FreeCAD as App, Part, MeshPart
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'cad/models/C142864'; OUT.mkdir(parents=True,exist_ok=True); V=App.Vector
def offset_path(path,d):
    out=[]
    for i,(y,z) in enumerate(path):
        if i==0: dy,dz=path[1][0]-y,path[1][1]-z
        elif i==len(path)-1: dy,dz=y-path[i-1][0],z-path[i-1][1]
        else: dy,dz=path[i+1][0]-path[i-1][0],path[i+1][1]-path[i-1][1]
        L=math.hypot(dy,dz) or 1; out.append((y-d*dz/L,z+d*dy/L))
    return out
def side(sign):
    p=[(3.70,.50),(3.70,1.05),(3.35,2.20),(2.85,3.45)]
    for i in range(19):
        a=math.radians(-58+103*i/18); p.append((3.2*math.cos(a),7.2+3.2*math.sin(a)))
    p += [(2.05,10.25),(2.25,10.81697)]
    a=offset_path(p,.25); b=offset_path(p,-.25)
    q=[V(-3.5,sign*y,z) for y,z in a]+[V(-3.5,sign*y,z) for y,z in reversed(b)]
    return Part.Face(Part.makePolygon(q+[q[0]])).extrude(V(7,0,0))
solids=[side(-1),side(1),Part.makeBox(7,7.9,.5,V(-3.5,-3.95,0))]
for x in (-3.8,3.8):
    solids += [Part.makeBox(.5,1.5,3.6,V(x-.25,-.75,-3.6)),Part.makeBox(.8,1.5,.5,V(-4.05 if x<0 else 3.25,-.75,0))]
shape=solids[0]
for s in solids[1:]: shape=shape.fuse(s)
shape=shape.removeSplitter(); assert shape.isValid() and len(shape.Solids)==1
box=shape.BoundBox; print('bounds',box.XLength,box.YLength,box.ZMin,box.ZMax); assert abs(box.ZMin+3.6)<1e-6 and abs(box.ZMax-10.9)<1e-3
shape.exportStep(str(OUT/'C142864.step'))
MeshPart.meshFromShape(Shape=shape,LinearDeflection=.025,AngularDeflection=.15,Relative=False).write(str(OUT/'C142864.stl'))
doc=App.newDocument('C142864'); o=doc.addObject('PartDesign::Feature','Clip'); o.Label='10207101009 - formed sheet clip (datasheet envelope)'; o.Shape=shape; doc.recompute(); doc.saveAs(str(OUT/'C142864.FCStd'))
check=Part.Shape(); check.read(str(OUT/'C142864.step')); assert check.isValid() and len(check.Solids)==1
report={'part':'Littelfuse 10207101009 / C142864','units':'mm','origin':'PCB top at tail midpoint','axes':'X axial width; Y transverse; Z up','source':'datasheet.pdf and supplied 102071 drawing','source_sha256':hashlib.sha256((OUT/'datasheet.pdf').read_bytes()).hexdigest(),'datasheet_dimensions':{'pin_pitch':7.6,'tail_width':.5,'tail_length':1.5,'tail_below_board':3.6,'height_above_board':10.9,'body_axial_width':7.0,'base_transverse_width':7.9,'inner_radius':3.2,'radius_center_height':7.2,'mouth_inner_width':4.5,'throat_inner_width':3.5,'hole_diameter':2.0,'hole_tolerance':.1},'bounds_mm':[box.XLength,box.YLength,box.ZLength],'checks':{'valid_solid':True,'solid_count':1,'step_roundtrip_valid':True},'approximations':['0.5 mm sheet thickness is applied normal to the reconstructed spring centreline','undimensioned transition, flare, landing bends and radii are approximated','embossing, edge rounds, stamping marks and spring deflection omitted'],'usage':'placement and enclosure visualization only; validate loaded seating and HV clearances with production clips','assembly':'DNP at JLC, fitted by user'}
(OUT/'model.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report['checks']))
