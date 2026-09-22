#!/usr/bin/env python3
"""Run ngspice HV transients for the ATtiny-PWM boost + CW ladder model.

Decks live in sim/hv/converter.cir. Plots and metrics land in docs/sim/.
"""
"""Run real ngspice transients; preserve decks, logs, sampled data and metrics."""
from pathlib import Path
import argparse, csv, hashlib, json, os, re, subprocess
os.environ.setdefault('MPLCONFIGDIR', '/tmp/geiger2-matplotlib')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/sim'; BUILD=ROOT/'build/hv'; OUT.mkdir(parents=True,exist_ok=True); BUILD.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,'grid.alpha':.18,'figure.facecolor':'#f8fafc','axes.facecolor':'#f8fafc','savefig.facecolor':'#f8fafc'})
parser=argparse.ArgumentParser(); parser.add_argument('--reuse',action='store_true'); args=parser.parse_args()
base=(ROOT/'sim/hv/converter.cir').read_text()
cases=[(f'v{v:g}_load{i:g}',{'VBAT':v,'ILOAD':i*1e-6}) for v in (3.135,3.3,3.465) for i in (0,1,5,20)]
cases += [('enable_off',{'VBAT':3.3,'ILOAD':1e-6}),('sense_open',{'VBAT':3.3,'ILOAD':1e-6}),('sense_trip',{'VBAT':3.3,'ILOAD':1e-6}),('tube_short',{'VBAT':3.3,'ILOAD':1e-6})]
metrics=[]; waves={}
for name,params in cases:
    deck=base
    for key,value in params.items(): deck=re.sub(rf'\b{key}=\S+',f'{key}={value:g}',deck,count=1)
    if name in ('enable_off','sense_open','sense_trip','tube_short'):
        # The 402 kΩ chain and the sense switch are not on the sheet.
        # Fault traces follow the firmware: duty 0 until enabled, a PA6
        # trip, and a 200 ms latch once duty is already at the 20% ceiling.
        deck=deck.replace('Sinhibit enable 0 sense 0 HYST OFF\n','')
        deck=deck.replace('*(v(ovp)<1.242)','')
        deck=deck.replace('Bgate gate 0 V={v(clock)*(v(delayed)>0.5)*(v(en)>2)*(v(ovp)<1.242)}','Bgate gate 0 V={v(clock)*(v(delayed)>0.5)*(v(en)>2)}')
        for line in ('Rovp1 hv ov1 33Meg\n','Rovp2 ov1 ov2 33Meg\n','Rovp3 ov2 ov3 33Meg\n','Rovp4 ov3 ovp 33Meg\n','Rovpbot ovp 0 402k\n','Covp ovp 0 10p\n'):
            deck=deck.replace(line,'')
        deck=deck.replace('* Separate HV divider/reference channel: nominal 409.02 V shutdown.\n','Vovp ovp 0 0\n')
    if name=='enable_off': deck=deck.replace('PULSE(0 3.3 5m 1u 1u 195m 500m)','0')
    if name in ('sense_open','tube_short'):
        # Already at the 20% ceiling. Firmware latches off 200 ms later
        # because PA6 is still below the setpoint.
        deck=deck.replace('PULSE(0 3.3 5m 1u 1u 195m 500m)','PULSE(0 3.3 0 1u 1u 200m 1)')
    if name=='sense_open': deck=deck.replace('Rtop1 hv div1 33Meg','Rtop1 hv div1 1e12')
    if name=='sense_trip':
        deck=deck.replace('PULSE(0 3.3 5m 1u 1u 195m 500m)','DC 3.3')
        deck=deck.replace('Bgate gate 0 V={v(clock)*(v(delayed)>0.5)*(v(en)>2)}',
            'Bgate gate 0 V={v(clock)*(v(delayed)>0.5)*(v(en)>2)*(v(run)>0.5)}\n'
            '* Code 405 at 3.3 V is 1.306 V on the PA6 divider. Duty stays off after that.\n'
            'Bfwrun run 0 V={v(sense)>1.306 ? 0 : v(runlag)}\n'
            'Rfw run runlag 10k\n'
            'Cfw runlag 0 50n ic=1')
    if name=='tube_short': deck=deck.replace('Ctube anode cathode 5p','Ctube anode cathode 5p\nRfault anode cathode 1k')
    work=BUILD/name; work.mkdir(exist_ok=True)
    if args.reuse:
        assert (work/'converter.cir').read_text()==deck, f'{name}: stale deck; rerun without --reuse'
    if not args.reuse:
        (work/'converter.cir').write_text(deck)
        subprocess.run(['ngspice','-b','-o','run.log','converter.cir'],cwd=work,check=True,stdout=subprocess.DEVNULL,timeout=180)
    log=(work/'run.log').read_text()
    if any(s in log.lower() for s in ('timestep too small','fatal error','error:')): raise RuntimeError(f'{name}: {log[-2000:]}')
    x=np.loadtxt(work/'wave.txt',skiprows=1); t=x[:,0]
    if t[-1]<.29999 or not np.isfinite(x).all(): raise RuntimeError(f'{name}: incomplete data')
    waves[name]=x; y=x[(t>=.15)&(t<.19)]; duration=y[-1,0]-y[0,0]
    avg=lambda v:float(np.trapezoid(v,y[:,0])/duration)
    # Linearized data is for visualization only. Exact adaptive samples are used
    # for peak stress and energy metrics via the second export below.
    raw=np.loadtxt(work/'metrics.txt',skiprows=1); tail=raw[(raw[:,0]>=.15)&(raw[:,0]<.19)]; dt=tail[-1,0]-tail[0,0]
    avg_raw=lambda v:float(np.trapezoid(v,tail[:,0])/dt)
    hit=np.flatnonzero(raw[:,1]>=396)
    metrics.append(dict(case=name,vbat=params['VBAT'],load_uA=params['ILOAD']*1e6,hv_mean=avg_raw(tail[:,1]),hv_min=float(tail[:,1].min()),hv_max=float(tail[:,1].max()),ripple_pp=float(np.ptp(tail[:,1])),startup_ms=float(raw[hit[0],0]*1e3) if len(hit) else None,peak_hv_V=float(raw[:,1].max()),peak_switch_v=float(raw[:,2].max()),peak_inductor_mA=float(raw[:,3].max()*1e3),input_mA=avg_raw(-tail[:,4])*1e3,ovp_peak_V=float(raw[:,10].max()),ttl_min_V=float(raw[:,6].min()),ttl_max_V=float(raw[:,6].max()),base_peak_V=float(raw[:,11].max()),hv_at_300ms_V=float(raw[-1,1]),within_360_440=bool(tail[:,1].min()>=360 and tail[:,1].max()<=440)))
    print(name,json.dumps(metrics[-1]),flush=True)
    # Compressed trace preserves time steps without committing 100 MB text files.
    np.savez_compressed(work/f'{name}.npz',wave=x,columns=np.array(['time_s','hv_V','switch_V','inductor_A','input_A','enable_V','ttl_V','cathode_V','anode_V','gate_V','ovp_V','base_V','collector_V']))
    del raw
(OUT/'results.json').write_text(json.dumps({'model':'exploratory non-vendor switch/diode model; no controller or gate-drive supply current','measurement_window_s':[.15,.19],'netlist_sha256':hashlib.sha256(base.encode()).hexdigest(),'ngspice':subprocess.check_output(['ngspice','--version'],text=True).splitlines()[1],'cases':metrics},indent=2)+'\n')
with (OUT/'results.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=metrics[0],lineterminator="\n"); w.writeheader(); w.writerows(metrics)
def save(fig,name):
    fig.savefig(ROOT/'docs/images'/f'sim-{name}.png',dpi=180,bbox_inches='tight'); plt.close(fig)

fig,ax=plt.subplots(2,1,figsize=(10,7),layout='constrained')
for v in (3.135,3.3,3.465):
    x=waves[f'v{v:g}_load1']; ax[0].plot(x[:,0]*1000,x[:,1],label=f'{v:g} V input'); ax[1].plot(x[:,0]*1000,x[:,5])
ax[0].axhspan(390,420,alpha=.15,color='green'); ax[0].legend(); ax[0].set(ylabel='Tube voltage (V)',title='Startup and residual HV · supply ±5%, 1 µA')
ax[1].set(ylabel='Firmware enable (V)',xlabel='Time (ms)',title='Enable is a firmware bit in the model. It drops at 200 ms'); save(fig,'startup')
fig,ax=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for v in (3.135,3.3,3.465):
    m=[r for r in metrics[:12] if r['vbat']==v]; ax[0].errorbar([r['load_uA'] for r in m],[r['hv_mean'] for r in m],yerr=[[r['hv_mean']-r['hv_min'] for r in m],[r['hv_max']-r['hv_mean'] for r in m]],marker='o',label=f'{v:g} V'); ax[1].plot([r['load_uA'] for r in m],[r['input_mA'] for r in m],'-o',label=f'{v:g} V')
ax[0].set(xlabel='Additional HV load (µA)',ylabel='HV (V)',title='150–190 ms range'); ax[1].set(xlabel='Additional HV load (µA)',ylabel='Modeled supply current (mA)',title='Controller / output-driver power excluded'); ax[0].legend(); ax[1].legend(); save(fig,'load-sweep')
x=waves['v3.3_load1']; fig,ax=plt.subplots(2,1,figsize=(10,6),layout='constrained'); mask=(x[:,0]>.0999)&(x[:,0]<.1004)
ax[0].plot(x[mask,0]*1000,x[mask,7]); ax[0].set(ylabel='Cathode (V)',title='Synthetic 20 µA / 100 µs event · assumed detector threshold')
ax[1].plot(x[mask,0]*1000,x[mask,6]); ax[1].set(ylabel='TTL output (V)',xlabel='Time (ms)'); save(fig,'pulse')
nominal=next(r for r in metrics if r['case']=='v3.3_load1'); assert nominal['within_360_440'], 'Nominal HV outside target window'
assert x[:,6].max()>3.0, 'No TTL output'
assert abs(x[x[:,0]>.201,9]).max()<1e-6, 'Switch active while disabled'
assert abs(x[x[:,0]>.201,6]).max()<1e-6, 'TTL active while disabled'
print('PASS: nominal regulation, pulse output, disabled startup and shutdown blanking')

off=next(r for r in metrics if r['case']=='enable_off')
opened=next(r for r in metrics if r['case']=='sense_open')
trip=next(r for r in metrics if r['case']=='sense_trip')
short=next(r for r in metrics if r['case']=='tube_short')
assert off['peak_hv_V']<5, 'Enable-off case produced HV'
assert opened['peak_hv_V']>500, 'Open sense was still clamped by the removed divider'
assert opened['hv_at_300ms_V']<opened['peak_hv_V']*0.6, 'Open-sense ceiling did not latch off'
assert 400<trip['peak_hv_V']<520, 'PA6 trip did not cut near the firmware threshold'
assert trip['hv_at_300ms_V']<trip['peak_hv_V']*0.6, 'PA6 trip did not shut the converter off'
assert short['peak_hv_V']<400 and short['hv_at_300ms_V']<short['peak_hv_V']*0.6, 'Tube short did not leave the ceiling'
labels={'enable_off':'Enable off','sense_open':'Sense open, 20% then latch','sense_trip':'PA6 trip, then off','tube_short':'Tube short, 20% then latch'}
fig,ax=plt.subplots(figsize=(10,4.8),layout='constrained')
for name,label in labels.items():
    z=waves[name]; ax.plot(z[:,0]*1000,z[:,1],label=label)
ax.axhline(420,color='green',ls='--',lw=1,label='PA6 trip, about 420 V')
ax.legend(); ax.set(xlabel='Time (ms)',ylabel='Tube voltage (V)',title='Firmware faults: enable off, open sense, PA6 trip, tube short')
save(fig,'protection')
print('PASS: firmware enable, PA6 trip, and 20% ceiling latch')