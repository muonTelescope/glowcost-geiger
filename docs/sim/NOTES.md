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
- **L1 DCR ~9.5 Ω** (B82442T1105K050): efficiency / heating risk at high duty.
- **PA3, PB4/PB5, PC0–PC3:** intentionally unconnected on U1.

### Expected probe-only nets
- `UART_TX`, `UPDI` — MCU pin + TP only.
