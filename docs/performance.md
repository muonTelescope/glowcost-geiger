# Dead time, count-rate range and 3.3 V power

**Design estimate, not a calibrated dosimeter specification.** The application is
indoor background monitoring, with beta sensitivity retained. Counts are primary;
µSv values must be labeled approximate. A beta-sensitive, uncompensated tube has
no universal counts-to-dose conversion for arbitrary radiation fields.

## 1. Expected dead time: use 250 µs as a planning allowance

The RH Electronics MyGeiger 3 manual lists **190 µs and 2.9 cps per µSv/h** for
STS-5/SBM-20 at **420 V**. These are that instrument's settings, not a verified
passport for this particular CTC-5 operated at 400 V. We use them as provisional
reference values. [Manufacturer manual, p. 12](https://d3s5r33r268y59.cloudfront.net/datasheets/10827/2017-11-04-21-25-37/MyGeiger-3-English-Manual.pdf).

Three processes must be separated:

1. **Gas recovery:** the tube cannot immediately detect a second event after
   an avalanche. An electrical current-source pulse does not simulate this.
2. **Anode recharge:** a screening estimate is `R = 4.98 MΩ + 100 kΩ = 5.08 MΩ`.
   For a discharged capacitance, `τRC = RC`, and `t90 = ln(10) RC` recovers 90%
   of the voltage excursion. The real quench voltage and stray capacitance matter.
3. **Pulse-circuit recovery:** the NPN and conditioning must return low long
   enough to distinguish the next rising edge. A GPIO/software debounce of 1 ms,
   for example, would make the electronics slower than the tube.

| Assumed tube capacitance | RC time constant | 90% recharge estimate | First tested two-pulse separation resolved |
|---|---:|---:|---:|
| 5 pF, present HV model | 25.4 µs | 58.5 µs | 150 µs |
| 10 pF | 50.8 µs | 117.0 µs | 175 µs |
| 20 pF sensitivity case | 101.6 µs | 233.9 µs | 175 µs |

The paired-pulse test uses two **synthetic 20 µA / 100 µs events**, a stiff 400 V
source, native ngspice Gear integration and ≤0.1 µs steps. Passing means two
rising edges with at least 5 µs low between them. These are sampled test spacings,
not exact minima. The 20 pF case can produce distinct output pulses before full
anode recharge; that does not prove a real tube will detect the second event.

**Expected order of magnitude: 190–250 µs with short tube connections. Plan on
250 µs for now.** This is an engineering allowance, not a guaranteed worst case.
Do not add the three times blindly: the processes overlap. Conversely, taking
their maximum is only a screening model, not proof of tube recovery. Coating,
potting, a cable to the tube, temperature and tube variation can increase it.

![Paired electrical pulses](performance/pulse-pairs.png)

## 2. Maximum rate: accuracy limit versus saturation

For a nonparalyzable planning model, with true event rate `n`, observed rate `m`
and effective dead time `τ`:

```
m = n / (1 + nτ)
n = m / (1 - mτ)
fraction lost = 1 - m/n = mτ
```

A GM tube may behave differently near overload; it can become insensitive and
produce deceptively low counts. Saturation is not a valid dose measurement.
The tube manufacturer's recommended range and circuit behavior must bound the
usable range. [Philips GM tube handbook, dead time and high-dose behavior](https://frank.pocnet.net/other/Philips/elcoma/Philips_ElectronTubes_6_1983-07.pdf).

Using the provisional gamma sensitivity `K = 2.9 cps/(µSv/h)`:

```
approximate gamma µSv/min = corrected cps / (60 K) = corrected cps / 174
approximate gamma µSv/min = corrected CPM / 10440
```

The factor of **60** converts an hourly dose rate to a per-minute dose rate.
It is not valid for retained beta counts or an unknown gamma spectrum without
calibration. The limits below consider **dead-time loss only**, not calibration,
energy response, statistics, supply sag or missed host GPIO events.

| Effective dead time | Uncorrected loss | Observed cps | True cps in this model | Conditional gamma µSv/min |
|---|---:|---:|---:|---:|
| 190 µs reference | 5% | 263.2 | 277.0 | 1.59 |
| 190 µs reference | 10% | 526.3 | 584.8 | 3.36 |
| **250 µs planning** | **1%** | **40.0** | **40.4** | **0.232** |
| **250 µs planning** | **5%** | **200.0** | **210.5** | **1.21** |
| **250 µs planning** | **10%** | **400.0** | **444.4** | **2.55** |

For this background-monitoring design, **200 observed cps is a provisional
5%-dead-time-loss reporting boundary**. The corresponding gamma-only estimate
is ~1.21 µSv/min of true rate under the stated assumptions. Above that, report
“high rate / accuracy reduced” rather than quietly extending the claimed range.
These are planning thresholds, not alarm or personal-safety thresholds.

The mathematical count ceiling `1/250 µs = 4000 cps` would naively display
**22.99 µSv/min** without correction. **That is not a maximum measurable dose
rate**: at that asymptote, inferred true rate diverges and the inversion is
ill-conditioned. There is no defensible absolute maximum µSv/min specification
for the uncalibrated beta-sensitive prototype yet.

![Count loss and conditional dose-rate range](performance/rate-limits.png)

### Is the HV supply the limiting factor?

The synthetic event charge is `20 µA × (100 µs + 1 µs edges) = 2.02 nC`.
At 200 detected events/s this would draw ~0.404 µA; at 400/s, ~0.808 µA.
Those loads are below the separately simulated 5 µA external-load case.
However, actual avalanche charge has not been measured and partially recovered
pulses may draw charge without crossing the discriminator threshold.

Use `Ievents = Qevent × event rate` with measured charge before quoting a supply
limited range. At 5 µA, the 4.98 MΩ anode resistor drops **24.9 V**: measure the
actual tube bias, not only the multiplier rail. The 20 µA low-supply stress case
fails to reach 396 V even at the rail. It is not a validated high-count-rate mode.

## 3. How much current from 3.3 V?

### What the existing SPICE model actually predicts

| Condition at 3.3 V | Modeled supply current |
|---|---:|
| No *additional* HV load; synthetic 50 events/s still present | 2.365 mA |
| 1 µA additional HV load | **2.515 mA** |
| 5 µA additional HV load | 3.123 mA |
| 20 µA additional HV load | 5.323 mA |
| Shorted tube | 6.030 mA |
| Startup, EN rise to first 396 V | **5.774 mA average** |

Native steady figures use 150–190 ms. They include the modeled supply, feedback,
OVP and passive bleeder. They omit the physical oscillator, comparator supply
currents, switching drive and some pulse-logic supply current.

An illustrative **whole-module planning budget** at the 1 µA load point is:

| Contribution | Allowance | Basis |
|---|---:|---|
| Existing SPICE power path | 2.515 mA | Simulated |
| CMOS timer | 0.250 mA | Planning allowance; TI specifies 180 µA typical / 250 µA max at 5 V, 25°C, not a 3.3 V guarantee |
| Two TLV3012B comparators | 0.0062 mA | 2 × 3.1 µA maximum quiescent, reference loading extra |
| Conditioning / blanking logic | 0.100 mA | Allowance; final logic not selected |
| HV BJT base drive | 1.200 mA | 60 mA / forced β10 × 20% duty, assuming pulses every cycle |
| Additional real device losses | 1.000 mA | Engineering margin, not simulated |
| **Illustrative total** | **5.071 mA** | **~16.7 mW at 3.3 V** |

**Plan for roughly 5 mA operating draw, allocate 10 mA continuous and 20 mA for
average startup.** These are design budgets, not guaranteed limits; a physical
controller could change them. At background, controller/drive implementation and
permanent HV loads matter much more than detected-event charge. EN-off current
is not established: holding a CMOS timer in reset is not a complete power cut.

[TI LMC555 supply specifications](https://www.ti.com/lit/ds/symlink/lmc555.pdf)
· [TI TLV3012B specifications](https://www.ti.com/lit/ds/symlink/tlv3012.pdf).

### Power-on inrush is a separate unresolved requirement

The present ideal source applies 3.3 V instantly through 0.5 Ω into a discharged
22 µF capacitor. Thus the model produces **6.6 A at t≈0** (`3.3/0.5`) with an
11 µs input RC constant. This is an idealized hot-plug transient, not an expected
Pi capability or a credible physical current waveform. Wiring, ESR and the Pi's
rail impedance/current limiting are missing.

Input charging requires `Q = CΔV = 72.6 µC`. To limit charging alone to 20 mA,
a linear ramp needs at least **3.63 ms**, plus margin for other loads. Add an
appropriately designed soft-start/current-limited input and verify Pi rail droop.
The 10/20 mA budgets above do not bound an uncontrolled hot-plug spike.

## 4. Background statistics and validation

At the provisional 2.9 cps per µSv/h sensitivity, a gamma field of 0.1 µSv/h
would contribute 0.29 cps, or 17.4 counts/minute. Poisson uncertainty alone would
be about 24% in a minute, before intrinsic background, calibration and beta counts.
For a constant total observed rate of 0.5 cps, 200 s gives ~100 counts (~10%
relative standard deviation), and 800 s gives ~400 counts (~5%). Background
subtraction increases uncertainty. Longer integration is therefore more useful
than dead-time correction for typical background monitoring.

Before assigning an absolute rate specification:

- Measure tube plateau, intrinsic background, pulse-charge distribution and
  two-source/dead-time behavior at the actual 400 V bias.
- Test electrical paired pulses at the connector, including the real Pi input,
  cable capacitance, logic thresholds and host event capture.
- Characterize the gamma response separately from beta sensitivity; retain raw
  counts and calibration metadata alongside approximate µSv values.
- Recheck leakage, capacitance and beta attenuation after coating or potting.
  Do not pot the NOS tube or clips by default; material and process remain open.
- Address overload/fault reporting: the current four-wire circuit blanks PULSE
  on low HV, so a fault can resemble a quiet radiation field. A status encoding
  or other host-side health check is needed before unattended dependable use.

## Reproduce

`bun run analyze:performance` runs 33 short paired-pulse native SPICE cases and
regenerates [results](performance/results.json) and the two charts. It reuses the
unchanged pulse-stage netlist with a stiff HV test source. Existing full-HV runs
are not rerun. Source-current startup metrics use adaptive data when available;
a clean clone falls back to the versioned 10 µs trace and labels that difference.
