#!/usr/bin/env python3
"""Validate and plot the actual compressed tsci simulate output."""
import gzip,json,os,hashlib
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/geiger2-matplotlib')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];O=R/'docs/hv'
p=R/'build/tsci/hv-table.txt.gz'
with gzip.open(p,'rt') as f:
    header=f.readline().split()
    wanted=['time','v(hv_out)','v(hv_sense)','v(switch)','i(vsimulation_voltage_source_0)','v(ttl)']
    cols=[header.index(name) for name in wanted]
    x=np.loadtxt(f,usecols=cols)
assert np.isfinite(x).all() and x[-1,0]>=.119999, 'Incomplete/nonfinite CLI result'
t=x[:,0]; final=x[(t>=.08)&(t<.12)]
avg=lambda y:float(np.trapezoid(y,final[:,0])/(final[-1,0]-final[0,0]))
hit=np.flatnonzero(x[:,1]>=396)
assert len(hit), 'HV never reached 396 V'
metrics={'netlist_sha256':hashlib.sha256((R/'sim/hv/converter.cir').read_bytes()).hexdigest(),'engine':'tsci simulate analog / WebAssembly ngspice','tscircuit':json.loads((R/'node_modules/tscircuit/package.json').read_text())['version'],'eecircuit_engine':'CLI-selected (see pinned tscircuit dependency)' ,'points':len(x),'duration_s':float(t[-1]),'ttl_max_V':float(x[:,5].max()),'measurement_window_s':[.08,.12],'startup_396_ms':float(t[hit[0]]*1000),'hv_mean':avg(final[:,1]),'hv_min':float(final[:,1].min()),'hv_max':float(final[:,1].max()),'peak_switch_v':float(x[:,3].max()),'input_mA':avg(-final[:,4])*1000,'limitations':'Generic switch/diodes; behavioral controller; no controller or drive supply current. See README.'}
ref=np.load(O/'v3.3_load1.npz')['wave']; refhit=np.flatnonzero(ref[:,1]>=396)
metrics['native_startup_396_ms']=next(c['startup_ms'] for c in json.loads((O/'results.json').read_text())['cases'] if c['case']=='v3.3_load1')
metrics['startup_difference_ms']=abs(metrics['startup_396_ms']-(metrics['native_startup_396_ms']-5))
assert 390<metrics['hv_mean']<410 and metrics['hv_min']>=360 and metrics['hv_max']<=440,metrics
assert metrics['startup_difference_ms']<5,metrics
assert 3.0<metrics['ttl_max_V']<3.6,metrics
(O/'tsci-results.json').write_text(json.dumps(metrics,indent=2)+'\n')
# Keep an evenly sampled trace for plotting, all adaptive metrics calculated above.
out_t=np.linspace(0,t[-1],12001); out=np.column_stack([out_t]+[np.interp(out_t,t,x[:,i]) for i in range(1,x.shape[1])])
np.savez_compressed(O/'tsci-trace.npz',wave=out,columns=np.array(wanted))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2,'figure.facecolor':'#f8fafc','axes.facecolor':'#f8fafc','svg.hashsalt':'geiger2'})
fig,axs=plt.subplots(2,1,figsize=(10,7),layout='constrained')
axs[0].plot(out[:,0]*1000,out[:,1],color='#7c3aed',label='tsci simulate / WASM');axs[0].plot(ref[:,0]*1000-5,ref[:,1],'--',color='#059669',label='Native ngspice / Gear',alpha=.8);axs[0].set(xlim=(0,120),ylabel='HV output (V)',xlabel='Time (ms)',title='Same topology · 3.3 V input / 1 µA external load');axs[0].legend()
sel=out[:,0]>=.1;axs[1].plot(out[sel,0]*1000,out[sel,1],color='#7c3aed');axs[1].set(ylabel='HV output (V)',xlabel='Time (ms)',title='tscircuit regulation · final 20 ms (sampled at 10 µs)')
fig.suptitle('glowcost-geiger / tscircuit analog simulation',fontsize=16,fontweight='bold')
fig.savefig(O/'tsci-comparison.png',dpi=180,bbox_inches='tight');fig.savefig(O/'tsci-comparison.svg',bbox_inches='tight',metadata={'Date':None});plt.close(fig)
p=O/'tsci-comparison.svg';p.write_text('\n'.join(z.rstrip() for z in p.read_text().splitlines())+'\n')
print(json.dumps(metrics,indent=2))
