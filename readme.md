# gLowCost-geiger

Compact four-wire Geiger module for a Raspberry Pi. It powers a CTC-5 / STS-5
tube from 3.3 V, generates the tube high voltage, exposes raw TTL pulses, and
uses an ATtiny1616 for pulse counting, STEMMA QT / Qwiic I²C telemetry, address
straps, and HV/3V3 readback.

> **Prototype.** The PCB still has known DRC clearance issues. The HV design is
> not bench-qualified. Use appropriate high-voltage procedures.

## Design files

Open [`pcb/glowcost-geiger.kicad_pro`](pcb/glowcost-geiger.kicad_pro) in KiCad.
The schematic and PCB are authoritative.

| Path | Contents |
| --- | --- |
| [`pcb/`](pcb/) | KiCad project, symbols, footprints, 3D models |
| [`firmware/`](firmware/) | ATtiny1616 bring-up (`main.c`, `pins.h`) |
| [`cad/models/`](cad/models/) | Tube / clip mechanical sources |
| [`sim/hv/`](sim/hv/) | ngspice HV deck (`converter.cir`) |
| [`docs/sim/`](docs/sim/) | Latest SPICE metrics and plots |
| [`manufacturing/`](manufacturing/) | Fab notes (Gerbers → GitHub Releases) |
| [`docs/images/`](docs/images/) | README figures |
## Board and schematic

![Board top](docs/images/board-top.png)

![Board bottom](docs/images/board-bottom.png)

![Schematic](docs/images/schematic.png)

## Design summary

- Hardware HV boost, Cockcroft–Walton multiplier, protection, and pulse path
- ATtiny1616-MNR drives `HV_PWM`, counts pulses, serves I2C, reads A0/A1 straps
- Dual STEMMA QT (JST-SH): pin 1 GND, 2 3V3, 3 SDA, 4 SCL
- Horizontal CTC-5 / STS-5 under two DNP Littelfuse C142864 clips
- Target outline about 120 × 32 × 1.6 mm, two-layer, with HV isolation slots

### STEMMA address straps

| A1 | A0 | Address |
| --- | --- | --- |
| open | open | `0x2F` |
| open | bridged | `0x30` |
| bridged | open | `0x31` |
| bridged | bridged | `0x32` |
### MCU pin map

| Net | Pin |
| --- | --- |
| Pulse / collector | PA2 |
| SDA / SCL | PA4 / PA5 |
| HV sense ADC | PA6 |
| 3V3 sense ADC | PA7 |
| A0 / A1 | PB0 / PB1 |
| HV_PWM | PB2 |
| Enable | PB3 |
| UPDI | PA0 |
| UART TX | PA1 |
## Electrical review (2026-09-19)

### Fixed on the schematic

- **Tube anode** — `R20` pad 2 had been left floating after layout cleanup; reattached to `ANODE` (J2 clips).
- **Tube cathode** — `R21` / `R22` were not on `CATHODE`; reattached so J3 → R21→GND and R22→BASE→Q1.

### Still open / firmware-owned

| Issue | Notes |
| --- | --- |
| `/OVP` orphan (TP20 only) | Hardware OVP comparator went away with MCP6562. Board regulation is `SENSE`→PA6; firmware must stop PWM on over-voltage. SPICE still models a behavioral OVP clamp. |
| TTL blanking | PCB TTL is `COLLECTOR` through R24. SPICE blanking (EN / HV-in-range / OVP) is **not** on copper — host/firmware must gate counts. |
| L1 DCR 4.5 Ω | **YNR6045-102M** (LCSC C497845), 6×6 mm shielded, Isat 300 mA. |
| GM1 SparkGap | `on_board=no` annotation only; real tube is J2/J3. |
See also [`docs/sim/NOTES.md`](docs/sim/NOTES.md).

## HV simulation

Exploratory ngspice model in [`sim/hv/converter.cir`](sim/hv/converter.cir)
(ATtiny-PWM era behavioral gate: clock × soft-start × EN × OVP). Controller and
gate-drive supply current are **not** included.

```bash
python3 scripts/simulate.py           # regulated suite
python3 scripts/duty_sweep.py         # HV and switch stress versus PWM duty
python3 scripts/sync_spice_model.py   # refresh sim/hv/model.ts
```

### Nominal (3.3 V, +1 µA HV load)

| Metric | Value |
| --- | --- |
| HV mean (150–190 ms) | 399.2 V |
| HV range | 396–404 V |
| Startup to ~396 V | 30 ms |
| Peak switch node | 106 V |
| Peak inductor | 62 mA |
| Modeled input current | 2.35 mA |

Q3 is an HL2310A (60 V Vds). The 106 V switch peak at this regulated point is above that rating. See the duty sweep below.
### Fault / corner checks (PASS)

| Case | Peak HV | Note |
| --- | --- | --- |
| feedback_open | 413 V | Behavioral OVP holds &lt; 440 V |
| ovp_tolerance | 426 V | Worst-direction divider corner |
| disabled | 1.7 V | No HV when EN stuck low |
| tube_short | current-limited | Front-end survives 1 kΩ anode–cathode |
### Diagrams

![Startup / residual HV](docs/images/sim-startup.png)

![Load sweep](docs/images/sim-load-sweep.png)

![Synthetic pulse → TTL](docs/images/sim-pulse.png)

![Protection / fault overlay](docs/images/sim-protection.png)

![Duty sweep](docs/images/sim-duty-sweep.png)

Full CSV/JSON: [`docs/sim/results.csv`](docs/sim/results.csv),
[`docs/sim/results.json`](docs/sim/results.json),
[`docs/sim/duty-sweep.csv`](docs/sim/duty-sweep.csv).

## MCU control and readback

PB2 is TCA0 WO2. The timer is single-slope at 20 MHz with a period of 2000 counts, so the PWM is 10 kHz and one count is 50 ns (0.05% duty). `firmware/main.c` ramps CMP2 from 20 to 400 (1% to 20%). A fault clears the duty and `EN` until `SENSE` falls back through the recover code.

Divider values are from the schematic netlist (KiCad 10.0.6 BOM export): R1–R4 are 33 MΩ 1% (FRG2512F3305TS) and R5 is 412 kΩ 0.1% (PTFR0603B412KP9).

```
k = 412 kΩ / (132 MΩ + 412 kΩ) = 0.0031115
```

PA6 is a 10-bit conversion with the VDD reference. The firmware scale is `code = 1023 × Vpin / VDD` (0.965 counts per volt at 3.3 V). One count is **1.04 V** at the tube. The tinyAVR 1-series electrical definition uses `VREF/1024` per step; that changes the trip by 0.4 V.

| | Code | HV at 3.135 V | HV at 3.3 V | HV at 3.465 V |
| --- | --- | --- | --- | --- |
| Recover | 376 | 370 V | 390 V | 409 V |
| 400 V | 386 | 380 V | 400 V | 420 V |
| Trip | 405 | 399 V | 420 V | 441 V |

The same codes move ±5% with the 3.3 V rail because that rail is the ADC reference. R28/R29 (values 10 kΩ / 10 kΩ, midpoint on PA7) divide that same rail by two, so the 3V3 code stays near 512 and cannot correct the scale. Both of those MPNs are still FRG2512F3305TS, the 33 MΩ HV part, which does not match the 10 kΩ value.

Worst-case divider stack (all four 33 MΩ at +1% and R5 at −0.1%, or the opposite) moves a 420 V reading by about ±4.6 V. That is a few counts. The VDD reference error is about ±21 V at the trip.

`scripts/duty_sweep.py` (3.3 V, 1 µA, 340–390 ms) is the plant behind those codes:

| Duty | CMP2 | HV, PWM only | Switch peak |
| --- | --- | --- | --- |
| 1% | 20 | 37 V | 10 V |
| 6% | 120 | 188 V | 49 V |
| ~7.5% | ~149 | ~233 V | 60 V (HL2310A limit) |
| 12% | 240 | 371 V | 95 V |
| 20% | 400 | 604 V | 155 V |

Through 2–12% the slope is 30.5 V per percent of duty, **1.5 V per timer count**. The sense switch inside `converter.cir` (1.242 V on this divider, 399 V) flattens the curve once duty can reach it, which is why the regulated suite sits at 399 V with a 106 V switch peak. That switch exists only in the SPICE deck. Firmware holds one window, codes 376 to 405 (390 V to 420 V at exactly 3.3 V). Duty left at 20% with that loop stopped runs to about 604 V in this model, and the switch is already above 60 V at the 399 V clamp.

## Mechanical

Clip CAD (Littelfuse 102071 / LCSC C142864):

- [`pcb/models/C142864.step`](pcb/models/C142864.step)
- [`cad/models/C142864/`](cad/models/C142864/)

Tube body for KiCad 3D: [`pcb/models/tube.step`](pcb/models/tube.step)
(~108 × 11 × 11 mm). Sources: [`cad/models/tube.blend`](cad/models/tube.blend),
[`cad/models/tube.stl`](cad/models/tube.stl). Re-export with FreeCADCmd +
`scripts/export_tube_step.py`.

## Firmware

See [`firmware/`](firmware/). ATtiny1616 drives `HV_PWM`, soft-starts the boost, and enforces **software OVP** from `SENSE` (PA6) — trip ~420 V, recover ~390 V. There is no hardware OVP comparator on this revision.


Build with the Makefile in [`firmware/`](firmware/). Pins are in
`firmware/pins.h`.

## Fabrication

Treat this as a study board until DRC and HV clearance are clean. Order notes
belong under [`manufacturing/`](manufacturing/); release Gerbers via GitHub
Releases rather than committing them here.
