# HV model

`sim/hv/converter.cir` is an exploratory ngspice deck. The switch is an ideal 2 Ω device, the diodes break at 250 V, and controller current is not included. L1 is 1 mH at 4.5 Ω.

D1–D8 on the sheet are BAV21W-7-F (LCSC C155214), catalog 200 V DC reverse. The deck’s 250 V breakdown is a generic diode, not that part. A stuck 20% duty puts about 155 V on the switch node. Per-diode reverse voltage and hot leakage were not remeasured. The ladder stays 10 nF C0G. The X7R voltage-bias warning belongs to that high-voltage chain, not to C11 at 3.3 V.

A 2026-09-15 study quoted 250 µs as a planning dead time, taken from a counter manual’s 190 µs STS-5/SBM-20 figure, and about 5.1 mA for a controller this sheet no longer has. Neither number was remeasured here. This deck’s 2.35 mA excludes the MCU. Dose rate was not calculated.

What the deck adds, and the board does not:

- `EN` is the firmware enable bit, modeled as a voltage source.
- The regulated traces still use a fast clamp at the setpoint, including the 402 kΩ `ovp` chain. That chain is not on the sheet. The sheet regulates from PA6.
- The fault traces delete that clamp. Enable off stays at 1.7 V. An open sense path has no trip, so 20% duty runs to about 705 V with a 179 V switch peak, then the 200 ms ceiling latch drops the duty. A working PA6 divider cuts the duty at about 423 V. A 1 kΩ tube short peaks at about 281 V and then latches the same way. Those ceiling traces start at 20%; the firmware takes about 3.8 s to climb there from 1%, and a real trip restarts at 1% after code 376.
- With the sense divider still connected, the open-loop duty sweep at 20% is about 604 V and the switch peak is about 155 V. Q3 on the sheet is a 240 V TN2404K. The diodes in this deck break at 250 V.

Re-run:

```bash
python3 scripts/simulate.py
python3 scripts/duty_sweep.py
```

Latest tables are [`results.csv`](results.csv) and [`duty-sweep.csv`](duty-sweep.csv). Plots are in [`../images`](../images). The 2026-09-21 suite passed on ngspice 47: 399 V regulated at 3.3 V and 1 µA, switch peak 106 V.
