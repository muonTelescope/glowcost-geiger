"""Place implementation parts for the next routing pass; deliberately no routing."""
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[1]
board=pcbnew.LoadBoard(str(ROOT/'kicad/glowcost-geiger.kicad_pcb'))
board.SetThickness(0.8)
j1=board.FindFootprintByReference('J1')
if j1:
 j1.SetPosition(pcbnew.VECTOR2I(int(4.5*1e6),int(100*1e6)))
 j1.SetOrientationDegrees(90)
 j1.SetLocked(False)
lib=ROOT/'kicad/glowcost.pretty'
for ref,fn,x,y,mpn,lcsc,model in [
 ('U1','U1.kicad_mod',-24,-13,'TLC555IDR','C6987','SOIC-8_3.9x4.9mm_P1.27mm.step'),
 ('U2','U2.kicad_mod',-24,13,'MCP6562T-E/MS','C625560','MSOP-8-1EP_3x3mm_P0.65mm_EP1.68x1.88mm.step')]:
 if board.FindFootprintByReference(ref): continue
 f=pcbnew.FootprintLoad(str(lib),fn.replace('.kicad_mod',''))
 f.SetReference(ref);f.SetValue(mpn);f.SetPosition(pcbnew.VECTOR2I(int(x*1e6),int(y*1e6)));f.SetLayer(pcbnew.F_Cu)
 board.Add(f)
pcbnew.SaveBoard(str(ROOT/'kicad/glowcost-geiger.kicad_pcb'),board)
print('Placed U1 at -24,-13 and U2 at -24,13; no tracks added')
