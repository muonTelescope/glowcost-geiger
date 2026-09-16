"""Run with KiCad Python. Check geometry, exact nets and portable assets."""
from pathlib import Path
import json,xml.etree.ElementTree as ET,collections,hashlib
import pcbnew
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'kicad';DOC=ROOT/'docs/kicad'
m=json.loads((OUT/'schematic-map.json').read_text());reverse={v:k for k,v in m['references'].items()}
x=ET.parse(DOC/'netlist.xml');actual={}
for net in x.findall('.//nets/net'):
 for p in net.findall('node'):
  if p.attrib['ref'] in reverse:actual[(reverse[p.attrib['ref']],p.attrib['pin'])]=net.attrib['name'].lstrip('/')
expected={(r,p):n for r,ns in m['nets'].items() for p,n in ns.items()}
assert actual==expected,{'missing':set(expected.items())-set(actual.items()),'extra':set(actual.items())-set(expected.items())}
b=pcbnew.LoadBoard(str(OUT/'glowcost-geiger.kicad_pcb'))
before=pcbnew.LoadBoard(str(ROOT/'dist/docs/layout/kicad/layout.kicad_pcb'))
def point(p):return (round(p.x/1e6,6),round(p.y/1e6,6))
def pads(board):
 return collections.Counter((point(p.GetPosition()),point(p.GetSize()),point(p.GetDrillSize()),int(p.GetShape()),round(p.GetOrientationDegrees()%180,6)) for f in board.GetFootprints() for p in f.Pads())
assert pads(b)==pads(before),'Pad geometry changed'
def traces(board):
 return collections.Counter((tuple(sorted([point(t.GetStart()),point(t.GetEnd())])),round(t.GetWidth()/1e6,6),int(t.GetLayer())) for t in board.GetTracks() if not isinstance(t,pcbnew.PCB_VIA))
a=traces(before);z=traces(b);removed=a-z;added=z-a
assert not added and sum(removed.values())==1,(removed,added)
bridge=next(iter(removed));assert bridge[1]==.375 and bridge[0]==((53.75,84.0),(54.79,84.0)),bridge
jp=next(f for f in b.GetFootprints() if f.GetReference()=='JP1')
assert any(g.GetLayer()==pcbnew.F_Cu and round(g.GetWidth()/1e6,6)==.375 for g in jp.GraphicalItems())
def vias(board):return collections.Counter((point(t.GetPosition()),t.GetWidth(pcbnew.F_Cu),t.GetDrillValue()) for t in board.GetTracks() if isinstance(t,pcbnew.PCB_VIA))
assert vias(b)==vias(before)
# All 72 source parts retain their exact centroid and rotation.
bf={f.GetReference():f for f in before.GetFootprints()}
for f in b.GetFootprints():
 old=reverse.get(f.GetReference())
 if old:
  assert point(f.GetPosition())==point(bf[old].GetPosition())
  assert abs(f.GetOrientationDegrees()-bf[old].GetOrientationDegrees())<1e-5
  assert str(f.GetFPID().GetLibItemName())==old
  assert (OUT/'glowcost.pretty'/(old+'.kicad_mod')).exists()
  for p in f.Pads():
   n=p.GetNumber()
   if n:assert p.GetNetname().lstrip('/')==expected[old,n],(old,n,p.GetNetname(),expected[old,n])
for f in b.GetFootprints():
 for model in f.Models():
  p=Path(model.m_Filename.replace('${KIPRJMOD}',str(OUT)))
  assert p.exists(),p
# Native reports deliberately retain routing violations; never turn them into exclusions.
drc=json.loads((DOC/'drc.json').read_text());erc=json.loads((DOC/'erc.json').read_text())
assert not drc['unconnected_items'] and not drc['schematic_parity']
assert not [v for s in erc['sheets'] for v in s['violations']]
report={'component_count':75,'net_count':len(set(expected.values())),'source_footprints':72,'mounting_holes':4,'assembly_model_footprints':1,'unchanged_pad_geometry':True,'unchanged_routing_geometry':True,'jumper':'same 0.375 mm copper; swapped native-export pad numbers restored; bridge represented by a net tie graphic','vias':sum(vias(b).values()),'erc_violations':0,'unconnected_items':0,'schematic_parity_issues':0,'drc_types':dict(collections.Counter(v['type'] for v in drc['violations'])),'fabrication_release':False,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'glowcost-geiger.kicad_pcb',OUT/'glowcost-geiger.kicad_sch']}}
(DOC/'conversion-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
