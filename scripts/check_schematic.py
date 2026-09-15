"""Validate schematic's exposed electrical nets against the SPICE module boundaries."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'dist/board/module/circuit.json').read_text())
assert not [r for r in rows if 'error' in r['type']]
comps={r['source_component_id']:r for r in rows if r['type']=='source_component'}
ports={r['source_port_id']:r for r in rows if r['type']=='source_port'}
net_ids={r['source_net_id'] for r in rows if r['type']=='source_net'}
parent={p:p for p in set(ports)|net_ids}
def find(p):
    if parent[p]!=p:parent[p]=find(parent[p])
    return parent[p]
for r in rows:
    if r['type']=='source_trace':
        ps=r['connected_source_port_ids']+r.get('connected_source_net_ids',[])
        for p in ps[1:]:parent[find(p)]=find(ps[0])
actual={}
for p,r in ports.items():actual.setdefault(find(p),set()).add((comps[r['source_component_id']]['name'],r['pin_number']))
expected={}
def add(net,name,pin):expected.setdefault(net,set()).add((name,pin))
refmap={'Rtop1':'R1','Rtop2':'R2','Rtop3':'R3','Rtop4':'R4','Rbottom':'R5','Csense':'C9','Ra1':'R_A1','Ra2':'R_A2','Rk':'R_K','Ren':'R_EN','Rprotect':'R_PROTECT','Rout':'R_OUT','Rprotect':'R_PROTECT','Rcollector':'R_COL','Dnegative':'D_NEG','Rovp1':'R_OV1','Rovp2':'R_OV2','Rovp3':'R_OV3','Rovp4':'R_OV4','Rovpbot':'R_OVBOT','Covp':'C_OV','Rbleed1':'R_BL1','Rbleed2':'R_BL2','Rbleed3':'R_BL3','Rbleed4':'R_BL4'}
for line in (root/'sim/hv/converter.cir').read_text().splitlines():
    f=line.split()
    if not f:continue
    ref=f[0]
    if ref in refmap or (ref[0] in 'CD' and ref[1:].isdigit() and 1<=int(ref[1:])<=8):
        pins=[2,1] if ref[0]=='C' and ref[1:].isdigit() and int(ref[1:])%2==0 else [1,2]
        for net,pin in zip(f[1:3],pins):add('battery' if net=='vin' else net,refmap.get(ref,ref),pin)
# Collapse only the modeled input source resistance into the driver boundary.
for name,nets in {'J1':['battery','0','ttl','en'],'U1':['sw','0','battery','en','sense','ovp'],'U2':['collector','drive','battery','0','en','hv','ovp'],'Q1':['base','0','collector'],'GM1':['anode','cathode']}.items():
    for pin,net in enumerate(nets,1):add(net,name,pin)
a={frozenset(s) for s in actual.values()};e={frozenset(s) for s in expected.values()}
assert a==e, {'missing':[sorted(s) for s in e-a], 'extra':[sorted(s) for s in a-e]}
expected_values={'R1':33e6,'R2':33e6,'R3':33e6,'R4':33e6,'R5':412e3,'R_A1':2.49e6,'R_A2':2.49e6,'R_K':1e5,'R_EN':1e5,'R_PROTECT':1e5,'R_OUT':1000,'R_COL':47000,**{f'R_OV{i}':33e6 for i in range(1,5)},**{f'R_BL{i}':10e6 for i in range(1,5)},'R_OVBOT':402e3}
for c in comps.values():
    if c['name'] in expected_values:assert c['resistance']==expected_values[c['name']]
    if c['name'].startswith('C'):assert abs(c['capacitance']-(100e-12 if c['name']=='C9' else (10e-12 if c['name']=='C_OV' else 10e-9)))<1e-16
print(f'PASS: {len(comps)} components, {len(e)} nets; four-pin interface, ladder polarities and passive values verified')
