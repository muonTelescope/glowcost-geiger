# HV model

`sim/hv/converter.cir` is an exploratory ngspice deck. The switch is an ideal 2 Ω device, the diodes break at 250 V, and controller current is not included. L1 is 1 mH at 4.5 Ω.

What the deck adds, and the board does not:

- `EN` is the firmware enable bit, modeled as a voltage source.
- The 402 kΩ chain on `ovp` is only in this deck. The sheet regulates from PA6.
- A stuck 20% duty is a fault in the open-loop sweep (~604 V, switch peak ~155 V). Q3 on the sheet is a 240 V TN2404K.

Re-run:

```bash
python3 scripts/simulate.py
python3 scripts/duty_sweep.py
```

Latest tables are [`results.csv`](results.csv) and [`duty-sweep.csv`](duty-sweep.csv). Plots are in [`../images`](../images). The 2026-09-21 suite passed on ngspice 47: 399 V regulated at 3.3 V and 1 µA, switch peak 106 V.
