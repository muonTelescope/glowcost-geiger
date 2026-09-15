"""Check generic pulse-indicator loading with bridge intact and cut."""
from pathlib import Path
import subprocess,tempfile,re,json
root=Path(__file__).resolve().parents[1];deck=(root/'sim/indicator/indicator.cir').read_text();results={}
for mode,resistance in [('enabled','0.01'),('cut','1e12')]:
 with tempfile.TemporaryDirectory() as t:
  p=Path(t)/'indicator.cir';p.write_text(deck.replace('Rbridge vcc led_supply 0.01','Rbridge vcc led_supply '+resistance))
  r=subprocess.run(['ngspice','-b',str(p)],capture_output=True,text=True,check=True)
  results[mode]={k:float(v) for k,v in re.findall(r'^(i_led_on|v_ttl_on|v_ttl_off|i_drive_on)\s*=\s*([\deE+.-]+)',r.stdout,re.M)}
 assert results[mode]['v_ttl_on']>3.2 and abs(results[mode]['v_ttl_off'])<.01
assert 0.0005 < abs(results['enabled']['i_led_on']) < .002
assert abs(results['cut']['i_led_on'])<1e-8
results['limitations']='Generic LED/BJT models, ideal 3.3 V pulse driver, 100 us pulses; no optical visibility or physical U2 validation. Cut modeled as 1 teraohm.'
(root/'docs/indicator-results.json').write_text(json.dumps(results,indent=2)+'\n');print('PASS: enabled LED current, cut isolation and pulse-output levels')
