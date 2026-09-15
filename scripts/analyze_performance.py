"""Reproducible planning calculations and paired-pulse front-end SPICE tests.
No radiation transport or gas-discharge model; dose conversion is conditional.
"""
from pathlib import Path
import json, os, subprocess
os.environ.setdefault('MPLCONFIGDIR','/tmp/glowcost-matplotlib')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]; O=R/'docs/performance'; B=R/'build/pulse-pairs'
O.mkdir(exist_ok=True); B.mkdir(parents=True,exist_ok=True)
source=(R/'sim/hv/converter.cir').read_text()
front=source[source.index('Ra1 '):source.index('.control')]
front=front.replace('Bevent anode cathode I={20u*v(event)*max(0,min(1,v(hv)/360))}', 'Bevent anode cathode I={20u*min(1,v(event)+v(event2))}')
front=front.replace('100m 1u 1u 100u 20m','1m 1u 1u 100u 100m')
results=[]
for cap in (5,10,20):
    for sep in (100,110,125,150,175,190,200,225,250,300,400):
        path=B/f'c{cap}_s{sep}';path.mkdir(exist_ok=True)
        deck='Paired synthetic pulse test - NO tube dead-time model\nVhv hv 0 400\nVvin vin 0 3.3\nVen en 0 3.3\n'+front.replace('Ctube anode cathode 5p',f'Ctube anode cathode {cap}p')
        deck+=f'Vevent2 event2 0 PULSE(0 1 {0.001+sep*1e-6:.8f} 1u 1u 100u 100m)\n'
        deck+='''.options method=gear reltol=0.0001
.control
set wr_singlescale
set wr_vecnames
tran 0.1u 2m 0 0.1u
wrdata wave.txt v(ttl) v(cathode) v(anode) v(collector)
quit
.endc
.end
'''
        (path/'test.cir').write_text(deck)
        subprocess.run(['ngspice','-b','-o','run.log','test.cir'],cwd=path,check=True,stdout=subprocess.DEVNULL,timeout=30)
        log=(path/'run.log').read_text().lower()
        assert 'error' not in log and 'timestep too small' not in log
        x=np.loadtxt(path/'wave.txt',skiprows=1); assert np.isfinite(x).all() and x[-1,0]>=.001999
        high=x[:,1]>1.65; edges=np.flatnonzero(np.diff(high.astype(int))==1)+1; edges=edges[x[edges,0]>.0009]
        falls=np.flatnonzero(np.diff(high.astype(int))==-1)+1; falls=falls[x[falls,0]>.0009]
        gap=float((x[edges[1],0]-x[falls[0],0])*1e6) if len(edges)==2 and len(falls) else 0
        results.append({'capacitance_pF':cap,'event_separation_us':sep,'output_rising_edges':len(edges),'low_gap_us':gap,'resolved_with_5us_low':bool(len(edges)==2 and gap>=5)})
        if sep in (125,190):np.savez_compressed(O/f'pair-{cap}pF-{sep}us.npz',wave=x)
minimum={str(c):next((a['event_separation_us'] for a in results if a['capacitance_pF']==c and a['resolved_with_5us_low']),None) for c in (5,10,20)}
k=2.9 # cps / (uSv/hour), reference instrument setting, NOT calibration of this tube
limits=[]
for tau in (190e-6,250e-6):
    for loss in (.01,.05,.1):
        measured=loss/tau; true=measured/(1-loss)
        limits.append(dict(deadtime_us=tau*1e6,loss_fraction=loss,observed_cps=measured,true_cps=true,conditional_uSv_min=true/(60*k)))
current=json.loads((R/'docs/hv/results.json').read_text())['cases']
nominal=next(c for c in current if c['case']=='v3.3_load1')
# Adaptive source-current data is optional after a fresh clone; checked compact trace fallback is labeled.
p=R/'build/hv/v3.3_load1/metrics.txt'
x=np.loadtxt(p,skiprows=1) if p.exists() else np.load(R/'docs/hv/v3.3_load1.npz')['wave']
sel=(x[:,0]>=.005)&(x[:,0]<=nominal['startup_ms']/1000)
startup_mA=float(np.trapezoid(-x[sel,4],x[sel,0])/(x[sel,0][-1]-x[sel,0][0])*1000)
metrics={'reference_deadtime_us':190,'planning_deadtime_us':250,'conditional_cps_per_uSv_h':k,'reference_condition':'RH Electronics MyGeiger 3 manual: STS-5/SBM-20 at 420 V; our tube at 400 V remains uncalibrated','front_end_pair_minimum_us':minimum,'pair_test_criteria':'Two rising edges separated by >=5 us low; only synthetic electrical events, no intrinsic tube model','rc_90pct_us':{str(c):float(np.log(10)*5.08e6*c*1e-12*1e6) for c in (5,10,20)},'loss_limits':limits,'ideal_nonparalyzable_asymptote_cps':4000,'asymptotic_display_uSv_min_not_range':4000/(60*k),'synthetic_event_charge_nC':2.02,'nominal_converter_mA':nominal['input_mA'],'startup_average_mA':startup_mA,'startup_source_data':'adaptive' if p.exists() else '10us sampled','source_peak_mA':float((-x[:,4]).max()*1000),'current_budget':{'timer_mA':.25,'two_comparators_mA':.0062,'logic_allowance_mA':.1,'switch_drive_allowance_mA':1.2,'additional_losses_allowance_mA':1.0,'continuous_reservation_mA':10,'startup_reservation_mA':20},'pair_tests':results}
metrics['illustrative_total_mA']=nominal['input_mA']+sum(metrics['current_budget'][n] for n in ('timer_mA','two_comparators_mA','logic_allowance_mA','switch_drive_allowance_mA','additional_losses_allowance_mA'))
(O/'results.json').write_text(json.dumps(metrics,indent=2)+'\n')
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.2})
fig,ax=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
true=np.linspace(0,2500,600)
for tau in (190e-6,250e-6):
    obs=true/(1+true*tau); ax[0].plot(true,obs,label=f'{tau*1e6:.0f} us'); ax[1].plot(true/(60*k),100*true*tau/(1+true*tau),label=f'{tau*1e6:.0f} us')
ax[0].plot(true,true,'--',color='gray',label='No dead time');ax[0].set(xlabel='True event rate (cps)',ylabel='Observed count rate (cps)',title='Nonparalyzable planning model');ax[0].legend()
ax[1].set(xlabel='Conditional dose rate (uSv/min)',ylabel='Uncorrected count loss (%)',ylim=(0,50),title='Assumed K = 2.9 cps per uSv/h');ax[1].axhline(5,ls='--',color='orange');ax[1].axhline(10,ls='--',color='red');ax[1].legend()
fig.savefig(O/'rate-limits.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(3,1,figsize=(10,8),layout='constrained')
for ax,c in zip(axs,(5,10,20)):
    for sep in (125,190):
        z=np.load(O/f'pair-{c}pF-{sep}us.npz')['wave'];mask=(z[:,0]>.00095)&(z[:,0]<.0015);ax.plot((z[mask,0]-.001)*1e6,z[mask,1],label=f'{sep} us event spacing')
    ax.set(ylabel='PULSE (V)',title=f'Assumed tube capacitance {c} pF; intrinsic tube dead time excluded');ax.legend()
axs[-1].set(xlabel='Time from first event (us)');fig.savefig(O/'pulse-pairs.png',dpi=180);plt.close(fig)
print(json.dumps({k:v for k,v in metrics.items() if k!='pair_tests'},indent=2))
