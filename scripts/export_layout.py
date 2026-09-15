"""Check and publish the unrouted placement study and actual PCB-layer artwork."""
from pathlib import Path
import csv, json, math, shutil, subprocess, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/layout'; OUT.mkdir(exist_ok=True)
rows=json.loads((ROOT/'dist/board/layout/circuit.json').read_text())
schematic=json.loads((ROOT/'dist/board/module/circuit.json').read_text())
source={r['source_component_id']:r for r in rows if r['type']=='source_component'}
pcb=[r for r in rows if r['type']=='pcb_component']
name=lambda r:source[r['source_component_id']]['name']
expected={r['name']:r.get('manufacturer_part_number') for r in schematic if r['type']=='source_component' and r['name'] not in ('U1','U2','GM1')}
assert {name(r):source[r['source_component_id']].get('manufacturer_part_number') for r in pcb}==expected
assert len(pcb)==72
errors=[r for r in rows if r['type'].endswith('_error')]
assert not errors, errors
assert any(r['type']=='pcb_trace' for r in rows)

def bounds(r):
    if 'outline' in r:
        xs=[p['x'] for p in r['outline']];ys=[p['y'] for p in r['outline']]
        return min(xs),min(ys),max(xs),max(ys)
    w,h=r['width'],r['height']; theta=math.radians(r.get('ccw_rotation',0))
    w,h=abs(w*math.cos(theta))+abs(h*math.sin(theta)),abs(w*math.sin(theta))+abs(h*math.cos(theta))
    x,y=r['center']['x'],r['center']['y']
    return x-w/2,y-h/2,x+w/2,y+h/2

courtyards={r['pcb_component_id']:bounds(r) for r in rows if r['type'] in ('pcb_courtyard_rect','pcb_courtyard_outline')}
assert len(courtyards)==len(pcb)
def overlap(a,b):return min(a[2],b[2])-max(a[0],b[0])>1e-6 and min(a[3],b[3])-max(a[1],b[1])>1e-6
for i,a in enumerate(pcb):
    ba=courtyards[a['pcb_component_id']]
    assert ba[0]>-59 and ba[1]>-19 and ba[2]<59 and ba[3]<19, name(a)
    assert not overlap(ba,(-34,-12,-14,12)), f'{name(a)} overlaps controller reserve'
    if name(a) not in ('J2','J3'):
        for reserve in [(-58,-7,-48,7),(48,-7,58,7)]:
            assert not overlap(ba,reserve), f'{name(a)} overlaps clip access reserve'
    for b in pcb[i+1:]:assert not overlap(ba,courtyards[b['pcb_component_id']]), f'Courtyard overlap: {name(a)}, {name(b)}'

holes=[r for r in rows if r['type']=='pcb_plated_hole']
mounts=[r for r in rows if r['type']=='pcb_hole']
assert len(holes)==26 and len(mounts)==4
population={r['Reference']:r['DNP']=='Yes' for r in csv.DictReader((ROOT/'docs/review-bom.csv').open())}
for ref in ('J2','J3'):
    c=next(r for r in pcb if name(r)==ref)
    hh=[r for r in holes if r['pcb_component_id']==c['pcb_component_id']]
    assert len(hh)==2 and all(h['hole_diameter']==2.1 for h in hh)
    assert abs(math.dist((hh[0]['x'],hh[0]['y']),(hh[1]['x'],hh[1]['y']))-7.6)<1e-9
    assert population[ref]
    # Geometry was generated with placement enabled; restore population metadata
    # afterwards so DNP never deletes the four retained footprint holes.
    c['do_not_place']=True
for h in mounts:
    assert h['hole_diameter']==3.2
    for c in pcb:
        b=courtyards[c['pcb_component_id']]
        dx=max(b[0]-h['x'],0,h['x']-b[2]);dy=max(b[1]-h['y'],0,h['y']-b[3])
        assert math.hypot(dx,dy)>3.2, f'{name(c)} overlaps mounting hardware reserve'

# Confirm the cuttable link is the sole copper path into the LED supply branch.
source_ports={r['source_port_id']:r for r in rows if r['type']=='source_port'}
port_labels={r['pcb_port_id']:(source[source_ports[r['source_port_id']]['source_component_id']]['name'],source_ports[r['source_port_id']]['pin_number']) for r in rows if r['type']=='pcb_port'}
sj=next(c for c in pcb if name(c)=='SJ_LED')
bridges=[r for r in rows if r['type']=='pcb_trace' and r.get('pcb_component_id')==sj['pcb_component_id']]
assert len(bridges)==1 and all(p['width']==.375 for p in bridges[0]['route'])
def copper_connected(include_bridge):
    parent={p:p for p in port_labels}
    def find(p):
        while parent[p]!=p:p=parent[p]
        return p
    for t in rows:
        if t['type']!='pcb_trace' or (not include_bridge and t in bridges):continue
        ports=t.get('connectsTo',[])+[p[k] for p in t['route'] for k in ['start_pcb_port_id','end_pcb_port_id'] if p.get(k)]
        ports=[p for p in ports if p in parent]
        for p in ports[1:]:parent[find(p)]=find(ports[0])
    a=next(p for p,v in port_labels.items() if v==('R_LED',1))
    b=next(p for p,v in port_labels.items() if v==('J1',1))
    return find(a)==find(b)
assert copper_connected(True), 'LED supply not connected with bridge intact'
assert not copper_connected(False), 'LED jumper bypassed by another copper path'

warnings=[{'type':r['type'],'message':r.get('message','')} for r in rows if r['type'].endswith('_warning')]
report={'status':'routing study with testpoints; analog control still missing; NOT fabrication signoff','board_mm':[120,40,1.6],
        'placed_footprints':72,'dnp_retained_footprints':['J2','J3'],'mounting_holes':4,'clip_plated_holes':4,'through_hole_testpoints':22,'led_bridge':{'width_mm':.375,'intact_connected':True,'cut_disconnects_supply':True},
        'copper_traces':sum(r['type']=='pcb_trace' for r in rows),'vias':sum(r['type']=='pcb_via' for r in rows),'planes':0,'errors':errors,'checks':['schematic part identity','all courtyards present','courtyard AABB overlap','board bounds','local clip access and controller reserves','mounting hardware reserves','DNP clips and 7.6mm drill spacing'],
        'tube_vertical_clearance':'UNVERIFIED; component height and electrical spacing to tube require measurement',
        'warnings':warnings}
(OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
(OUT/'circuit.json').write_text(json.dumps(rows,indent=2)+'\n')
with (OUT/'placement.csv').open('w') as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(['Reference','X_mm','Y_mm','Rotation_deg','Layer','DNP','MPN'])
    for c in pcb:w.writerow([name(c),c['center']['x'],c['center']['y'],c.get('rotation',0),c['layer'],'Yes' if population[name(c)] else 'No',source[c['source_component_id']].get('manufacturer_part_number','')])

ET.register_namespace('','http://www.w3.org/2000/svg')
svg=ET.parse(ROOT/'dist/board/layout/pcb.svg').getroot()
boundary=next(e for e in svg if e.get('data-type')=='pcb_boundary')
x,y,w,h=(float(boundary.get(k)) for k in ('x','y','width','height'))
scale=w/120
views={
 'placement':None,
 'top-copper':{'pcb_smtpad','pcb_plated_hole','pcb_trace','pcb_via'},
 'bottom-copper':{'pcb_plated_hole','pcb_trace','pcb_via'},
 'bottom-silkscreen':{'pcb_silkscreen_text','pcb_silkscreen_path','pcb_silkscreen_rect'},
 'silkscreen':{'pcb_silkscreen_text','pcb_silkscreen_path','pcb_silkscreen_rect'},
 'drill':{'pcb_plated_hole','pcb_hole','pcb_via'},
 'courtyards':{'pcb_smtpad','pcb_plated_hole','pcb_hole','pcb_keepout'},
}
for view,types in views.items():
    root=ET.fromstring(ET.tostring(svg))
    for e in list(root):
        typ=e.get('data-type')
        if view=='placement' and typ and typ.startswith('pcb_silkscreen') and e.get('data-pcb-layer')=='bottom':
            root.remove(e);continue
        if view in ('silkscreen','bottom-silkscreen') and typ and typ.startswith('pcb_silkscreen') and e.get('data-pcb-layer') != ('bottom' if view=='bottom-silkscreen' else 'top'):
            root.remove(e);continue
        if typ in ('pcb_trace','pcb_smtpad','pcb_via') and view in ('top-copper','bottom-copper') and e.get('data-pcb-layer') not in (None,'through',view.split('-')[0]):
            root.remove(e);continue
        if typ in ('pcb_fabrication_note_text','pcb_fabrication_note_path') or (types is not None and typ and typ not in types|{'pcb_background','pcb_boundary','pcb_board'}):root.remove(e)
    root.set('viewBox',f'{x-8} {y-8} {w+16} {h+16}')
    root.set('width','2000');root.set('height',str(round(2000*(h+16)/(w+16))))
    if view=='courtyards':
        for c in pcb:
            a,b,d,e=courtyards[c['pcb_component_id']]
            ET.SubElement(root,'{http://www.w3.org/2000/svg}rect',{'x':str(x+(a+60)*scale),'y':str(y+(20-e)*scale),'width':str((d-a)*scale),'height':str((e-b)*scale),'fill':'none','stroke':'#66ffff','stroke-width':'0.6'})
    path=OUT/f'{view}.svg'
    path.write_text('\n'.join(l.rstrip() for l in ET.tostring(root,encoding='unicode').splitlines())+'\n')
    subprocess.run(['rsvg-convert','-w','2400',str(path),'-o',str(OUT/f'{view}.png')],check=True)
print(f'PASS: {len(pcb)} footprints, no courtyard overlaps, four DNP clip holes retained; seven layer views exported')

shutil.copyfile(ROOT/'dist/board/layout/3d.png', OUT/'3d.png')

# Audit model coverage separately from 2D placement: generic packages do not
# establish manufacturer body heights or assembled tube clearance.
cad=[r for r in rows if r['type']=='cad_component']
audit={'status':'assembly renders include recovered tube and reconstructed clips; exact interference unverified',
       'generic_package_models':[source[r['source_component_id']]['name'] for r in cad if r.get('footprinter_string')],
       'placeholder_only':[source[r['source_component_id']]['name'] for r in cad if r.get('show_as_bounding_box')],
       'assembly_renderer_models':{'tube':'cad/models/tube.stl','clips':'cad/models/C142864/C142864.stl'},
       'missing_assemblies':['physical analog HV control circuitry','exact J1 body'],
       'required_checks':['manufacturer-specific body heights','tube underside height in C142864 clips','electrical clearance from HV parts to tube body','clip insertion and connector mating access']}
(OUT/'model-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
