"""Build an editable, single-sheet KiCad schematic from verified circuit JSON.
Stock KiCad symbol geometry; explicit diode A/K remap to preserve tscircuit pads.
No analog implementation is invented for the two behavioral boundaries.
"""
from pathlib import Path
import json,math,copy,uuid
from kicad_sexpr import *
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'kicad';OUT.mkdir(exist_ok=True)
LIB=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols')
rows=json.loads((ROOT/'dist/board/module/circuit.json').read_text())
comps={r['source_component_id']:r for r in rows if r['type']=='source_component'}
byref={v['name']:v for v in comps.values()}
refmap={r:r for r in byref}
for prefix in ['R','C','D','Q']:
 taken=[int(r[len(prefix):]) for r in byref if r.startswith(prefix) and r[len(prefix):].isdigit()]
 nextnum=max(taken,default=0)+1
 for r in byref:
  if r.startswith(prefix+'_'):
   refmap[r]=prefix+str(nextnum);nextnum+=1
refmap['SJ_LED']='JP1'
ports={r['source_port_id']:r for r in rows if r['type']=='source_port'}
nets={r['source_net_id']:r['name'] for r in rows if r['type']=='source_net'}
parent={p:p for p in set(ports)|set(nets)}
def find(x):
 if parent[x]!=x:parent[x]=find(parent[x])
 return parent[x]
for r in rows:
 if r['type']=='source_trace':
  ps=r['connected_source_port_ids']+r.get('connected_source_net_ids',[])
  for p in ps[1:]:parent[find(p)]=find(ps[0])
netnames={find(k):v for k,v in nets.items()}
explicit=json.loads((ROOT/'build/kicad-node-ports.json').read_text())
for net,selectors in explicit.items():
 for sel in selectors:
  ref,alias=sel.replace('.', '').split(' > ')
  p=next((p for p in ports.values() if comps[p['source_component_id']]['name']==ref and alias in p.get('port_hints',[])),None)
  if p:netnames[find(p['source_port_id'])]=net
pinnets={(comps[p['source_component_id']]['name'],str(p['pin_number'])):netnames[find(k)] for k,p in ports.items()}
# Physical diode pads stay 1=A, 2=K: convert the symbol numbers, not the copper.
A=Atom
E=lambda size=1.27:['effects',['font',['size',size,size]]]
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'glowcost-kicad/'+s))
rootid=uid('sheet');libsyms={};items=[];placed={};pins={};used=set();power_count=0
cache={}
def stock(lib,name):
 if lib not in cache:cache[lib]=parse((LIB/(lib+'.kicad_sym')).read_text())
 s=copy.deepcopy(next(x for x in children(cache[lib],'symbol') if x[1]==name))
 return s
def load(kind):
 if kind in libsyms:return libsyms[kind]
 lib,name=kind.split(':');s=stock(lib,name)
 if name in ['D','LED']:
  for p in walk(s,'pin'):
   n=child(p,'number');n[1]='2' if n[1]=='1' else '1'
  for p in children(s,'property'):
   if p[1]=='Sim.Pins':p[2]='1=A 2=K'
 s[1]='Glowcost:'+name
 libsyms[kind]=s
 return s
def custom(name,definitions,width=10.16):
 s=['symbol','Glowcost:'+name,['pin_names',['offset',1.016]],['in_bom','yes'],['on_board','yes'],['property','Reference','U',['at',0,10.16,0],E()],['property','Value',name,['at',0,-10.16,0],E()]]
 body=['symbol',name+'_0_1',['rectangle',['start',-width,10.16],['end',width,-10.16],['stroke',['width',0],['type','default']],['fill',['type','background']]]]
 part=['symbol',name+'_1_1']
 for n,label,x,y,angle in definitions:
  part.append(['pin','passive','line',['at',x,y,angle],['length',2.54],['name',label,E()],['number',str(n),E()]])
 s.extend([body,part]);libsyms['Custom:'+name]=s
custom('Analog_HV_boundary',[(3,'3V3',-12.7,7.62,0),(4,'EN',-12.7,2.54,0),(5,'FB',-12.7,-2.54,0),(6,'OVP',-12.7,-7.62,0),(1,'SW',12.7,2.54,180),(2,'GND',0,-12.7,90)])
custom('Pulse_logic_boundary',[(1,'IN',-12.7,7.62,0),(5,'EN',-12.7,2.54,0),(6,'HV_READY',-12.7,-2.54,0),(7,'OVP',-12.7,-7.62,0),(2,'OUT',12.7,2.54,180),(3,'3V3',0,12.7,270),(4,'GND',0,-12.7,90)])
def val(ref):
 c=byref.get(ref,{})
 if 'resistance' in c:
  v=c['resistance'];return f'{v/1e6:g} MR' if v>=1e6 else f'{v/1e3:g} kR' if v>=1000 else f'{v:g} R'
 if 'capacitance' in c:
  v=c['capacitance'];return f'{v*1e12:g} pF' if v<1e-9 else f'{v*1e9:g} nF'
 return {'U1':'UNIMPLEMENTED HV','U2':'UNIMPLEMENTED LOGIC','GM1':'CTC-5 / STS-5','J1':'JST GH 4-pin','J2':'C142864 DNP','J3':'C142864 DNP','SJ_LED':'CUT = LED OFF','D_LED':'KT-0805YG'}.get(ref,c.get('manufacturer_part_number',ref))
def kindof(ref):
 if ref.startswith('TP'):return 'Connector:TestPoint'
 if ref.startswith('R'):return 'Device:R_Small_US'
 if ref.startswith('C'):return 'Device:C'
 if ref=='D_LED':return 'Device:LED'
 if ref.startswith('D'):return 'Device:D'
 if ref.startswith('Q'):return 'Transistor_BJT:Q_NPN_BEC'
 return {'SJ_LED':'Jumper:SolderJumper_2_Bridged','J1':'Connector_Generic:Conn_01x04','J2':'Connector_Generic:Conn_01x02','J3':'Connector_Generic:Conn_01x02','GM1':'Device:SparkGap','U1':'Custom:Analog_HV_boundary','U2':'Custom:Pulse_logic_boundary'}[ref]
def put(ref,x,y,angle=0,value=None):
 k=kindof(ref) if ref in byref else ('power:GND' if value=='GND' else 'power:PWR_FLAG' if value=='PWR_FLAG' else 'power:VDD')
 s=libsyms[k] if k in libsyms else load(k)
 c=byref.get(ref,{})
 off=ref in ['U1','U2','GM1'] or ref.startswith('#')
 obj=['symbol',['lib_id',s[1]],['at',x,y,angle],['unit',1],['in_bom','no' if ref.startswith(('TP','SJ','#')) or ref in ['U1','U2'] else 'yes'],['on_board','no' if off else 'yes'],['dnp','yes' if ref in ['J2','J3'] else 'no'],['uuid',uid(ref)]]
 v=value or val(ref)
 displayref=refmap.get(ref,ref)
 # Keep readable fields clear of pins and wires.
 if ref.startswith(('R','C','D')) and angle in [90,180,270]: rx,ry,vx,vy=x,y-5.08,x,y-2.54
 elif ref.startswith(('R','C','Q','D')):rx,ry,vx,vy=x+5.08,y-1.27,x+5.08,y+1.27
 else:rx,ry,vx,vy=x,y-15.24,x,y-12.7
 if ref.startswith('D') and ref!='D_LED' and angle in [90,270]:rx,ry,vx,vy=x+5.08,y-1.27,x+5.08,y+1.27
 if ref=='D_NEG':rx,ry,vx,vy=x,y-5.08,x,y-2.54
 if ref.startswith('TP'):rx,ry,vx,vy=x+5.08,y-3.81,x+5.08,y-1.27
 if ref.startswith('#'):rx,ry,vx,vy=x,y,x,y-3.81 if value!='GND' else y+3.81
 fields=[('Reference',displayref,rx,ry,ref.startswith('#')),('Value',v,vx,vy,False),('Footprint','' if off else 'glowcost:'+ref,x,y,True),('Datasheet',c.get('datasheet_url',''),x,y,True),('MPN',c.get('manufacturer_part_number',''),x,y,True),('LCSC',','.join(c.get('supplier_part_numbers',{}).get('jlcpcb',[])),x,y,True)]
 for name,v,px,py,hide in fields:
  eff=E(1.27 if name=='Reference' or ref.startswith('#') else 1.1)
  if name in ['Value','Reference'] and (ref.startswith(('R','C','Q','D','TP')) and angle==0):eff.append(['justify','left'])
  if hide:eff.append(['hide','yes'])
  obj.append(['property',name,v,['at',px,py,90 if angle in [90,270] else 0],eff])
 coords={}
 for p in walk(s,'pin'):
  n=child(p,'number')[1];at=child(p,'at');a=math.radians(angle);px=float(at[1]);py=float(at[2]);xx=x+px*math.cos(a)-py*math.sin(a);yy=y-(px*math.sin(a)+py*math.cos(a));coords[n]=(round(xx,6),round(yy,6),(float(at[3])+angle)%360)
  obj.append(['pin',n,['uuid',uid(ref+'/pin/'+n)]])
 obj.append(['instances',['project','glowcost-geiger',['path','/'+rootid,['reference',displayref],['unit',1]]]])
 items.append(obj);placed[ref]=(x,y);pins[ref]=coords
 return coords
def wire(a,b):
 a=a[:2];b=b[:2]
 if a==b:return
 net=next((pinnets.get((r,n),'') for r,ps in pins.items() for n,p in ps.items() if p[:2] in [a,b] and (r,n) in pinnets),'')
 color=[120,50,160,1] if net.startswith(('P','S','ANODE','DIV','OV','BL')) and net!='BASE' else [170,40,40,1] if net=='V3V3' else [20,120,120,1] if net=='GND' else [30,135,50,1]
 items.append(['wire',['pts',['xy',*a],['xy',*b]],['stroke',['width',0.1524],['type','default'],['color',*color]],['uuid',uid('wire/'+str(a)+str(b))]])
def join(ref1,p1,ref2,p2):
 assert pinnets[ref1,str(p1)]==pinnets[ref2,str(p2)]
 wire(pins[ref1][str(p1)],pins[ref2][str(p2)]);label(pinnets[ref1,str(p1)],(pins[ref1][str(p1)][0]+1.27 if len(pinnets[ref1,str(p1)])>6 else (pins[ref1][str(p1)][0]+pins[ref2][str(p2)][0])/2,(pins[ref1][str(p1)][1]+pins[ref2][str(p2)][1])/2));used.update([(ref1,str(p1)),(ref2,str(p2))])
def label(net,p,angle=0):
 items.append(['label',net,['at',p[0],p[1],angle],['effects',['font',['size',1.27,1.27]],['justify','left','bottom']],['uuid',uid('label/'+net+str(p)+str(angle))]])
def terminal(ref,n,length=5.08):
 global power_count
 x,y,a=pins[ref][str(n)];net=pinnets[ref,str(n)]
 dx=-math.cos(math.radians(a));dy=math.sin(math.radians(a));end=(round(x+length*dx,6),round(y+length*dy,6))
 if ref=='J1' and net=='GND':
  wire((x,y),(12.7,y));end=(12.7,55.88);wire((12.7,y),end);power_count+=1;put('#PWR'+str(power_count),*end,value='GND');used.add((ref,str(n)));return
 if net in ['GND','V3V3']:
  # Power symbols remain upright regardless of the component orientation.
  wire((x,y),end);power_count+=1
  put('#PWR'+str(power_count),*end,value=net)
 else:
  wire((x,y),end);label(net,end,180 if dx>0.5 else 0)
 used.add((ref,str(n)))
def note(text,x,y,size=1.27,bold=False):
 eff=E(size);eff.append(['justify','left','top'])
 if bold:eff[1].append('bold')
 items.append(['text',text,['at',x,y,0],eff,['uuid',uid('note/'+text)]])
def panel(title,x,y,w,h):
 items.append(['rectangle',['start',x,y],['end',x+w,y+h],['stroke',['width',0.3],['type','default'],['color',35,70,95,1]],['fill',['type','none']],['uuid',uid(title)]])
 note(title,x+3,y+3,1.8,True)
# A3 single sheet. Values and labels are intentionally sparse; detailed notes below.
panel('01  PI INPUT + ANALOG HV BOUNDARY',10,20,108,87)
panel('02  FOUR-STAGE COCKCROFT-WALTON LADDER',118,20,181,87)
panel('03  GREEN 0805 PULSE INDICATOR',302,20,110,87)
panel('04  MAIN HV FEEDBACK',10,110,132,64)
panel('05  INDEPENDENT OVP',142,110,132,64)
panel('06  PASSIVE HV DISCHARGE',277,110,135,64)
panel('07  TUBE + PULSE CONDITIONING',10,177,292,96)
panel('PROTOTYPE / HV SAFETY NOTES',302,177,110,77)
note('GLOWCOST GEIGER  |  3.3 V  |  CTC-5  |  COUNTS-FIRST MONITOR',10,12,2.2,True)
put('J1',30.48,45.72);put('U1',81.28,50.8);put('R_EN',43.18,63.5)
note('J1: 1=3V3  2=GND  3=PULSE  4=EN\nU1 is a functional boundary, not an IC pinout.\n1 mH; 10 kHz; 20 us ON; 22 uF modeled bypass.\nImplement oscillator / driver / feedback / soft-start.',12,84,1.3)
# Ladder horizontal capacitor chains and alternating diode columns.
for i in range(4):
 x=144.78+i*40.64
 put('C'+str(2*i+1),x,43.18,90)
 put('C'+str(2*i+2),x,73.66,270)
 put('D'+str(2*i+1),x-10.16,58.42,270)
 put('D'+str(2*i+2),x+10.16,58.42,90)
 # Use stable named rails to make each stage polarity explicit.
 for ref in ['C'+str(2*i+1),'C'+str(2*i+2),'D'+str(2*i+1),'D'+str(2*i+2)]:
  for n in ['1','2']:terminal(ref,n,3.81)
note('C1-C8: 10 nF C0G / 630 V / 1206.  D1-D8: BAV21W-7-F.\nSW ~106 V peak; S4 ~399 V nominal. Verify diode reverse stress and leakage.',123,95,1.27)
# Dividers: direct series strings, shared bottom shunt capacitor.
for prefix,x,y in [('R',20.32,137.16),('R_OV',154.94,137.16)]:
 for i in range(4):put(prefix+str(i+1),x+20.32*i,y,90)
 for i in range(1,4):join(prefix+str(i),2,prefix+str(i+1),1)
 bottom='R5' if prefix=='R' else 'R_OVBOT';cap='C9' if prefix=='R' else 'C_OV'
 put(bottom,x+81.28,y+10.16);put(cap,x+106.68,y+10.16)
 # top common sense rail / ground bottom rail
 a=pins[prefix+'4']['2'];b=pins[bottom]['1'];c=pins[cap]['1']
 wire(a,(b[0],a[1]));wire((b[0],a[1]),b);wire((b[0],a[1]),(c[0],a[1]));wire((c[0],a[1]),c)
 label('SENSE' if prefix=='R' else 'OVP',(b[0],a[1]))
 used.update([(prefix+'4','2'),(bottom,'1'),(cap,'1')])
 note('399.16 V = 1.242 x (132M + 412k) / 412k\n3.02 uA at 400 V; C9 time constant ~41 us.' if prefix=='R' else '409.06 V = 1.242 x (132M + 402k) / 402k\nSeparate reference required; latch / inhibit driver.',x-8,163,1.2)
for i in range(4):put('R_BL'+str(i+1),294.64+i*30.48,137.16,90)
for i in range(1,4):join('R_BL'+str(i),2,'R_BL'+str(i+1),1)
note('40 MR total: 10 uA, 4 mW at 400 V.\nAlways connected; EN low does not prove discharge.\nModel: ~158 V remains at 100 ms after disable.',282,156,1.3)
# Tube sensing; passives connected by named nodes and local physical wires.
put('R_A1',25.4,200.66,90);put('R_A2',53.34,200.66,90);join('R_A1',2,'R_A2',1)
put('GM1',83.82,200.66,0);join('R_A2',2,'GM1',1)
put('R_K',114.3,220.98);put('R_PROTECT',132.08,200.66,90)
put('Q1',160.02,210.82);put('D_NEG',132.08,228.6,0);put('R_COL',185.42,200.66)
put('U2',231.14,218.44);put('R_OUT',271.78,215.9,90)
join('U2',2,'R_OUT',1)
join('GM1',2,'R_PROTECT',1)
wire((114.3,200.66),pins['R_K']['1']);used.add(('R_K','1'))
items.append(['junction',['at',114.3,200.66],['diameter',0],['color',0,0,0,0],['uuid',uid('cathode-junction')]])
wire(pins['R_PROTECT']['2'],(147.32,200.66));wire((147.32,200.66),(147.32,210.82));wire((147.32,210.82),pins['Q1']['1'])
label('BASE',(147.32,210.82));used.update([('R_PROTECT','2'),('Q1','1')])
put('J2',30.48,231.14);put('J3',68.58,231.14)
note('R_A1/R_A2: 2.49 MR EACH, >=500 V working rating; ~88.4 uA maximum at 440 V.\nJ2/J3: C142864 DNP for JLC, hand-fit clips. Tube supplied by user.\nU2 inverts Q1 and blanks on EN / HV-ready / OVP. No MCU. Physical logic remains unfinished.\nPlan 250 us tube dead time (reference ~190 us); dose conversion is approximate.',12,251,1.25)
# LED default bridge, resistor, LED and buffered sink.
put('SJ_LED',320.04,45.72,0);put('R_LED',345.44,45.72,90);put('D_LED',375.92,45.72,180)
join('SJ_LED',2,'R_LED',1);join('R_LED',2,'D_LED',1)
put('Q_LED',386.08,68.58);put('R_LB',342.9,68.58,90);put('R_LPD',365.76,83.82)
join('R_LB',2,'Q_LED',1)
wire((365.76,68.58),pins['R_LPD']['1']);used.add(('R_LPD','1'))
items.append(['junction',['at',365.76,68.58],['diameter',0],['color',0,0,0,0],['uuid',uid('LED-base-junction')]])
note('Factory copper bridge: cut to disable; solder to restore.\n~1.28 mA LED during pulse. Q_LED buffers DRIVE.\nNo pulse stretching; flashes may be hard to see.',307,94,1.15)
note('400 V present on exposed pads / tube clips.\nDischarge and verify before handling.\nDo not connect ordinary Pi / scope probes to HV.\n\nPreserved routing has unresolved clearances.\nU1/U2 have no physical implementation.\nThis is NOT a fabrication release.\n\n22 plated probe holes; 1 mm drill / 2 mm pads.\nSee README for model limits and DRC report.',307,191,1.3)
# Test points stay with their associated section; spread rows below circuit blocks.
tppos=[(20.32,78.74),(43.18,78.74),(63.5,78.74),(281.94,238.76),(254,238.76),(154.94,243.84),(185.42,243.84),(109.22,243.84),(83.82,243.84),(104.14,78.74),(149.86,86.36),(170.18,86.36),(190.5,86.36),(210.82,86.36),(231.14,86.36),(251.46,86.36),(271.78,86.36),(287.02,86.36),(83.82,157.48),(218.44,157.48),(50.8,243.84),(391.16,157.48)]
for i,(x,y) in enumerate(tppos,1):put('TP'+str(i),x,y,value=pinnets['TP'+str(i),'1'])
for ref in list(placed):
 if ref.startswith('#'):continue
 for n in pins[ref]:
  if (ref,n) not in used:terminal(ref,n,2.54 if ref.startswith('TP') else 5.08)
put('#FLG01',71.12,30.48,value='PWR_FLAG');label('V3V3',(71.12,30.48))
put('#FLG02',96.52,30.48,value='PWR_FLAG');label('GND',(96.52,30.48))
# All atoms are made explicit, with strings only where KiCad expects text.
# Parse generated text via a helper to normalize bare enum atoms below.
def normalize(x):
 if not isinstance(x,list):return x
 out=[]
 for i,v in enumerate(x):
  if isinstance(v,list):out.append(normalize(v))
  elif i==0:out.append(A(v))
  elif isinstance(v,str) and v in ['yes','no','passive','line','default','none','background','left','right','top','bottom','bold']:out.append(A(v))
  else:out.append(v)
 return out
symbols=[normalize(v) for v in libsyms.values()]
sch=normalize(['kicad_sch',['version',20250114],['generator','eeschema'],['uuid',rootid],['paper','User',430,297],['title_block',['title','Glowcost Geiger - prototype conversion'],['rev','KiCad review 1'],['company','muonTelescope'],['comment',1,'U1/U2 unfinished; preserved PCB requires clearance review']],['lib_symbols',*symbols],*items,['embedded_fonts','no']])
(OUT/'glowcost-geiger.kicad_sch').write_text(dump(sch)+'\n')
# Local library avoids missing generated-symbol dependencies on other machines.
local=copy.deepcopy(symbols)
for s in local:s[1]=s[1].split(':')[-1]
(OUT/'Glowcost.kicad_sym').write_text(dump(normalize(['kicad_symbol_lib',['version',20250114],['generator','kicad_symbol_editor'],*local]))+'\n')
(OUT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Glowcost") (type "KiCad") (uri "${KIPRJMOD}/Glowcost.kicad_sym") (options "") (descr "Stock symbols with explicit source pin numbering; prototype boundaries")))\n')
(OUT/'schematic-map.json').write_text(json.dumps({'root_uuid':rootid,'references':refmap,'symbols':{r:uid(r) for r in byref},'nets':{r:{n:net for (rr,n),net in pinnets.items() if rr==r} for r in byref}},indent=2)+'\n')
print('Generated',len(byref),'components /',len(explicit),'nets')

import csv
with (ROOT/'docs/kicad/reference-map.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['tscircuit reference','KiCad reference','footprint'])
 for r,k in refmap.items():w.writerow([r,k,'' if r in ['U1','U2','GM1'] else 'glowcost:'+r])
