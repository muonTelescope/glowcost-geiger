"""Add real implementation footprints/models for former U1/U2 boundaries."""
from pathlib import Path
import copy
from kicad_sexpr import *
ROOT=Path(__file__).resolve().parents[1]
pcb=parse((ROOT/'kicad/glowcost-geiger.kicad_pcb').read_text())
fpdir=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
def stock(lib,name): return parse((fpdir/(lib+'.pretty')/(name+'.kicad_mod')).read_text())
def add(name,lib,ref,x,y,model,mpn,lcsc):
 f=stock(lib,name);f[1]='glowcost:'+ref
 for v in children(f,'property'):
  if v[1]=='Reference':v[2]=ref
  elif v[1]=='Value':v[2]=mpn
  elif v[1]=='Footprint':v[2]='glowcost:'+ref
 f.extend([['property','MPN',mpn,['at',0,0],['hide','yes'],['effects',['font',['size',1,1]]]],['property','LCSC',lcsc,['at',0,0],['hide','yes'],['effects',['font',['size',1,1]]]]])
 f.append(['at',x,y,0]);f.append(['path','/'+ref]);f.append(['attr','smd'])
 f.append(['model','${KIPRJMOD}/models/'+model,['offset',['xyz',0,0,0]],['scale',['xyz',1,1,1]],['rotate',['xyz',0,0,0]]])
 pcb.append(f)
def normalize(x):
 if isinstance(x,list):
  enums={'yes','no','smd','thru_hole','roundrect','rect','circle','solid','default','none','F.Cu','B.Cu','F.Mask','F.Paste','F.SilkS','F.Fab','F.CrtYd','board_only'}
  return [Atom(v) if isinstance(v,str) and (i==0 or v in enums) else normalize(v) for i,v in enumerate(x)]
 return x
add('SOIC-8_3.9x4.9mm_P1.27mm','Package_SO','U1',-24,-13,'SOIC-8_3.9x4.9mm_P1.27mm.step','TLC555IDR','C6987')
add('MSOP-8-1EP_3x3mm_P0.65mm_EP1.68x1.88mm','Package_SO','U2',-24,13,'MSOP-8-1EP_3x3mm_P0.65mm_EP1.68x1.88mm.step','MCP6562T-E/MS','C625560')
(ROOT/'kicad/glowcost-geiger.kicad_pcb').write_text(dump(normalize(pcb))+'\n')
print('Added U1 and U2 footprints/models')
