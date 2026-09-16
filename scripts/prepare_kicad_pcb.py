"""Repair native tscircuit export metadata without moving copper or pads."""
from pathlib import Path
import json,copy,shutil
from kicad_sexpr import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'kicad'
x=parse((ROOT/'dist/docs/layout/kicad/layout.kicad_pcb').read_text())
m=json.loads((OUT/'schematic-map.json').read_text());refs=m['references']
netcodes={n[2]:n[1] for n in children(x,'net')}
# Use hierarchical net names to match KiCad's local schematic labels.
for n in children(x,'net'):
 if n[2] and n[2] not in ['GND','V3V3']:n[2]='/'+n[2]
lib=OUT/'glowcost.pretty';lib.mkdir(exist_ok=True)
# KiCad library geometry is copied locally for portability.
MODELS=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/3dmodels')
modelmap={}
def model(source):
 src=MODELS/source;dest=OUT/'models'/src.name
 shutil.copy2(src,dest);return '${KIPRJMOD}/models/'+src.name
for typ,source in {
 '0603R':'Resistor_SMD.3dshapes/R_0603_1608Metric.step',
 '1206R':'Resistor_SMD.3dshapes/R_1206_3216Metric.step',
 '2512R':'Resistor_SMD.3dshapes/R_2512_6332Metric.step',
 '0603C':'Capacitor_SMD.3dshapes/C_0603_1608Metric.step',
 '1206C':'Capacitor_SMD.3dshapes/C_1206_3216Metric.step',
 'SOD':'Diode_SMD.3dshapes/D_SOD-123.step',
 'SOT':'Package_TO_SOT_SMD.3dshapes/SOT-23.step',
 'LED':'LED_SMD.3dshapes/LED_0805_2012Metric.step',
 'JST':'Connector_JST.3dshapes/JST_GH_BM04B-GHS-TBT_1x04-1MP_P1.25mm_Vertical.step',
}.items():modelmap[typ]=model(source)
shutil.copy2(ROOT/'cad/models/C142864/C142864.step',OUT/'models/C142864.step')
def atomtree(x):
 if isinstance(x,list):return [Atom(v) if i==0 and isinstance(v,str) else atomtree(v) for i,v in enumerate(x)]
 return x
for idx,fp in enumerate(children(x,'footprint')):
 fp[:]=[v for v in fp if not(isinstance(v,list) and v and v[0]=='model')]
 properties=children(fp,'property');prop={p[1]:p for p in properties}
 if 'Reference' not in prop:
  fp.extend(parse('(property "Reference" "H'+str(idx-71)+'" (at 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1))))') for _ in [0])
  fp.append(parse('(property "Value" "MountingHole_3.2mm" (at 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1))))'))
  prop={p[1]:p for p in children(fp,'property')}
 old=prop['Reference'][2]
 if old not in refs:
  # Four mounting holes are board-only, with no schematic part.
  name=old; new=old
 else:name=old;new=refs[old]
 fp[1]='glowcost:'+name
 prop['Reference'][2]=new
 if old in refs:
  fp.append([Atom('path'),'/'+m['root_uuid']+'/'+m['symbols'][old]])
  fp.append([Atom('sheetname'),'']);fp.append([Atom('sheetfile'),'glowcost-geiger.kicad_sch'])
  # Value follows the rendered schematic exactly.
  sch=parse((OUT/'glowcost-geiger.kicad_sch').read_text())
  sym=next(s for s in children(sch,'symbol') if child(s,'uuid')[1]==m['symbols'][old])
  prop['Value'][2]=next(p[2] for p in children(sym,'property') if p[1]=='Value')
 for p in children(fp,'fp_text'):
  if p[1]=='reference':p[2]=new
  elif p[1]=='value':p[2]=prop['Value'][2]
 for pad in children(fp,'pad'):
  n=child(pad,'net')
  if n and n[2] and n[2] not in ['V3V3','GND']:n[2]='/'+n[2]
  # JST hold-down pads have no electrical pin number.
  if old=='J1' and pad[1] in ['5','6']:pad[1]=''
 if old=='SJ_LED':
  # The autorouter interchanged internally connected jumper pins.
  # Keep their physical locations, restore logical numbering, and represent
  # the factory copper bridge as a proper KiCad net tie graphic.
  for pad in children(fp,'pad'):
   n=child(pad,'net')
   if pad[1]=='1':pad[1]='2';n[1:]=[netcodes['LED_SUPPLY'],'/LED_SUPPLY']
   elif pad[1]=='2':pad[1]='1';n[1:]=[netcodes['V3V3'],'V3V3']
  fp.append([Atom('net_tie_pad_groups'),'1,2'])
  fp.append(parse('(fp_line (start -0.52 0) (end 0.52 0) (stroke (width 0.375) (type solid)) (layer "F.Cu"))'))
 attr=child(fp,'attr')
 if attr is None:attr=[Atom('attr')];fp.append(attr)
 if old in ['J2','J3']:attr.append(Atom('dnp'))
 if old.startswith('TP') or old=='SJ_LED' or old not in refs:attr.extend([Atom('exclude_from_bom'),Atom('exclude_from_pos_files')])
 if old not in refs:attr.append(Atom('board_only'))
 path=None;rz=0;ox=oy=oz=0
 if old in ['J2','J3']:path='${KIPRJMOD}/models/C142864.step'
 elif old=='J1':path=modelmap['JST'];rz=0
 elif old=='D_LED':path=modelmap['LED'];rz=180 # stock model pin 1=K; source pin 1=A
 elif old.startswith('D'):path=modelmap['SOD'];rz=180
 elif old.startswith('Q'):path=modelmap['SOT']
 elif old.startswith('R'):
  pad=children(fp,'pad')[0];w=float(child(pad,'size')[1]);typ='2512R' if old in ['R1','R2','R3','R4','R_OV1','R_OV2','R_OV3','R_OV4'] else '1206R' if old.startswith(('R_A','R_BL')) else '0603R';path=modelmap[typ]
 elif old.startswith('C'):path=modelmap['0603C' if old in ['C9','C_OV'] else '1206C']
 if path:fp.append(parse(f'(model "{path}" (offset (xyz {ox} {oy} {oz})) (scale (xyz 1 1 1)) (rotate (xyz 0 0 {rz})))'))
 # Export one source-preserving footprint per reference. This deliberately does
 # not replace pads with nominal stock patterns, which would invalidate routes.
 local=copy.deepcopy(fp);local[1]=name
 local[:]=[v for v in local if not(isinstance(v,list) and v and v[0] in ['path','sheetname','sheetfile','uuid','at'])]
 for p in children(local,'property'):
  if p[1]=='Reference':p[2]='REF**'
 for t in children(local,'fp_text'):
  if t[1]=='reference':t[2]='REF**'
 for pad in children(local,'pad'):pad[:]=[p for p in pad if not(isinstance(p,list) and p and p[0]=='net')]
 (lib/(name+'.kicad_mod')).write_text(dump(local)+'\n')
# Remove only the exporter's unnetted bridge track; exact same copper now in JP1.
for seg in list(children(x,'segment')):
 a=child(seg,'start');b=child(seg,'end')
 if abs(float(a[1])-53.75)<1e-5 and abs(float(b[1])-54.79)<1e-5 and abs(float(a[2])-84)<1e-5:
  x.remove(seg)
 # Route branch from physical left bridge pad to R_LED is LED_SUPPLY.
 elif child(seg,'net')[1]==netcodes['V3V3']:
  # Native JSON source_trace pins locate the two branch segments precisely.
  pa=(float(a[1]),float(a[2]));pb=(float(b[1]),float(b[2]))
  branch=[((53,84),(51.825,84)),((51.825,84),(49,86.825))]
  def close(p,q):return abs(p[0]-q[0])+abs(p[1]-q[1])<1e-4
  if any((close(pa,u) and close(pb,v)) or (close(pa,v) and close(pb,u)) for u,v in branch):child(seg,'net')[1]=netcodes['LED_SUPPLY']
# Native exporter preserves the reserve only as graphics: add copper keepout.
x.append(parse('(zone (net 0) (net_name "") (layers "F.Cu" "B.Cu") (hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) (keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) (copperpour not_allowed) (footprints allowed)) (fill (thermal_gap 0.3) (thermal_bridge_width 0.3)) (polygon (pts (xy 66 88) (xy 86 88) (xy 86 112) (xy 66 112))))'))
# Tube model only, excluded from BOM, no invented electrical pads.
x.append(parse('(footprint "glowcost:Tube_Assembly_Model" (layer "F.Cu") (at 100 100) (property "Reference" "MECH1" (at 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1)))) (attr board_only exclude_from_pos_files exclude_from_bom) (model "${KIPRJMOD}/models/tube.wrl" (offset (xyz 0 0 7.2)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0))))'))
(OUT/'glowcost-geiger.kicad_pcb').write_text(dump(x)+'\n')
(OUT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "glowcost") (type "KiCad") (uri "${KIPRJMOD}/glowcost.pretty") (options "") (descr "Preserved tscircuit land patterns and models")))\n')
print('PCB prepared: same pads / track geometry; corrected jumper net tie; local libraries')
