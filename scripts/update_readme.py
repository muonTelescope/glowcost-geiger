"""Publish only metrics from the current model, with explicit measurement windows."""
from pathlib import Path
import json,re,hashlib
r=Path(__file__).resolve().parents[1]
a=json.loads((r/'docs/hv/results.json').read_text())
assert a['netlist_sha256']==hashlib.sha256((r/'sim/hv/converter.cir').read_bytes()).hexdigest()
b=json.loads((r/'docs/hv/tsci-results.json').read_text())
assert b['netlist_sha256']==a['netlist_sha256']
lines=['| Supply / 1 µA added load | Mean HV | HV range | First 396 V after EN | Modeled input |','|---|---:|---:|---:|---:|']
for c in a['cases']:
    if c['case'] in ('v3.135_load1','v3.3_load1','v3.465_load1'):
        lines.append(f"| {c['vbat']:g} V | {c['hv_mean']:.2f} V | {c['hv_min']:.2f}–{c['hv_max']:.2f} V | {c['startup_ms']-5:.2f} ms | {c['input_mA']:.3f} mA |")
n=next(c for c in a['cases'] if c['case']=='v3.3_load1');f=next(c for c in a['cases'] if c['case']=='feedback_open');t=next(c for c in a['cases'] if c['case']=='ovp_tolerance')
lines += ['',f"Native: {len(a['cases'])} cases. Open-feedback peak: **{f['peak_hv_V']:.2f} V**;",f"worst-direction 1% OVP reference/divider corner peak: **{t['peak_hv_V']:.2f} V**.",f"Nominal HV remains **{n['hv_at_300ms_V']:.1f} V at 300 ms**, about 100 ms after EN falls.",f"WASM: {b['points']:,} points over {b['duration_s']*1000:.0f} ms; mean HV **{b['hv_mean']:.2f} V**."]
p=r/'README.md';p.write_text(re.sub(r'<!-- RESULTS START -->.*?<!-- RESULTS END -->','<!-- RESULTS START -->\n'+'\n'.join(lines)+'\n<!-- RESULTS END -->',p.read_text(),flags=re.S))
