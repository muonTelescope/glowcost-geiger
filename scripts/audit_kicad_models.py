"""Read STEP shapes with FreeCAD; no manufacturing/assembly output generated."""
from pathlib import Path
import json,hashlib
import FreeCAD,Part
root=Path(__file__).resolve().parents[1];out=[]
for p in sorted((root/'kicad/models').glob('*.step')):
 s=Part.Shape();s.read(str(p));b=s.BoundBox
 assert not s.isNull() and s.isValid(),p
 out.append({'file':str(p.relative_to(root)),'valid':True,'solids':len(s.Solids),'bounds_mm':[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(root/'docs/kicad/model-audit.json').write_text(json.dumps({'models':out,'tube':'tube.wrl uses recovered STL, divided by 2.54 for KiCad units; Z offset 7.2 mm','limitations':'Nominal geometry; no tolerance or spring-loaded tube seating qualification. Stock LED/package models are envelopes, not exact manufacturer solids.'},indent=2)+'\n')
print('Valid STEP models:',len(out))
