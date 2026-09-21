# HV simulation notes (ATtiny1616 PWM era)

Model: `sim/hv/converter.cir` — exploratory non-vendor switch/diode SPICE.
Gate drive is behavioral (clock × soft-start × EN × OVP), standing in for
MCU `HV_PWM` → R25 → Q3. Re-run: `python3 scripts/simulate.py`.

## Schematic electrical findings (2026-09-19)

### Fixed
- **Tube anode open:** R20 pad 2 was floating after layout cleanup; reattached to `ANODE` (feeds J2 clips).
- **Tube cathode open:** R21/R22 were not on `CATHODE`; reattached so J3 → R21→GND and R22→BASE→Q1.

### Open / architectural
- **`/OVP` orphan:** only TP20. Hardware OVP comparator (MCP6562) was removed with the ATtiny-only rewrite. Regulation/OV protection must be done in firmware from `SENSE` (PA6). SPICE still models a behavioral OVP clamp — treat that as a firmware requirement, not a board feature.
- **GM1 SparkGap:** `on_board=no` (schematic annotation only). Real tube connections are J2/J3.
- **TTL blanking:** hardware TTL is `COLLECTOR` through R24. SPICE adds EN/HV/OVP blanking behavior that is **not** on the PCB — firmware/host must ignore pulses when EN is low or HV is out of range.
- **PA3, PB4/PB5, PC0–PC3:** intentionally unconnected on U1.
- **Q3 HL2310A is 60 V.** At the 399 V sense-clamp point the model switch peak is 106 V. See the duty sweep.

### Expected probe-only nets
- `UART_TX`, `UPDI` — MCU pin + TP only.

## L1 (2026-09-19)

L1 is **YNR6045-102M** / LCSC C497845 (1 mH, DCR 4.5 Ω, Isat 300 mA, 6×6 mm shielded). SPICE `DCR=4.5`. The sheet note matches that part.

## MCU duty and readback (2026-09-21)

Re-ran `python3 scripts/simulate.py` (suite still PASS, same 399 V regulation) and `python3 scripts/duty_sweep.py`. Divider parts taken from a KiCad 10.0.6 BOM export of `pcb/glowcost-geiger.kicad_sch`.

The stock deck holds the gate off with `Sinhibit` when `SENSE` crosses 1.242 V. That is `1.242 / k = 399 V` on R1–R4 (4 × 33 MΩ) and R5 (412 kΩ), `k = 0.0031115`. The separate 402 kΩ OVP divider (1.242 V → 409 V) only matters after that sense path is opened. Neither comparator is on the PCB.

PWM is TCA0 at 20 MHz, period 2000 (10 kHz). One count is 0.05% / 50 ns. Firmware uses counts 20–400 (1–20%).

Plant with both gate cuts removed, 3.3 V, 1 µA, mean over 340–390 ms (`docs/sim/duty-sweep.csv`):

| Duty | HV | Switch peak |
| --- | --- | --- |
| 1% | 37 V | 10 V |
| 6% | 188 V | 49 V |
| 8% | 250 V | 64 V |
| 12% | 371 V | 95 V |
| 15% | 459 V | 118 V |
| 20% | 604 V | 155 V |

Slope from 2% to 12% is 30.5 V per percent, 1.5 V per timer count. The HL2310A 60 V drain rating is crossed near 7.5% duty, about 233 V on the tube. The firmware window (codes 376 and 405) sits above that rating.

Readback, firmware formula `code = 1023 × Vpin / VDD`:

- 1 count = 1.04 V at the tube when VDD is 3.3 V (400 V → code 386, pin 1.245 V).
- Code 405 = 420 V and code 376 = 390 V at 3.3 V.
- At 3.135 V those codes are 399 V and 370 V. At 3.465 V they are 441 V and 409 V. The reference is VDD, so the trip tracks the rail.
- Worst-case 1% / 0.1% divider stack is about ±4.6 V at 420 V.
- R28/R29 values are 10 kΩ / 10 kΩ into PA7. Against a VDD reference the code stays near 512, so it cannot measure or correct the rail. Both MPNs are FRG2512F3305TS (33 MΩ), which does not match the value.

`docs/images/sim-duty-sweep.png` is the plot.
