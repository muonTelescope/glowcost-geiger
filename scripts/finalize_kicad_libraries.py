"""Run with KiCad's Python: normalize local footprint orientation and UUIDs."""
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'kicad/glowcost-geiger.kicad_pcb'
b=pcbnew.LoadBoard(str(p))
for f in b.GetFootprints():
 # KiCad's writer correctly transforms all local geometry during normalization.
 local=pcbnew.FOOTPRINT(f)
 local.SetPosition(pcbnew.VECTOR2I(0,0));local.SetOrientationDegrees(0)
 local.SetReference('REF**')
 for pad in local.Pads():pad.SetNetCode(0)
 pcbnew.FootprintSave(str(ROOT/'kicad/glowcost.pretty'),local)
pcbnew.SaveBoard(str(p),b)
print('Saved normalized project footprints and schematic fields')
