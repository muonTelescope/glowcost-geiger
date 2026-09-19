# gLowCost-geiger handoff

## Current intent
Production logic is the ATtiny1616-MNR (LCSC C507118) at 3.3 V. It counts raw Geiger pulses in hardware, exposes an I2C slave over two parallel JST SH STEMMA QT/Qwiic ports, reads address solder bridges, provides HV and 3V3 diagnostics, and leaves raw TTL available to the Raspberry Pi.

## Current repository
- Path: `/Users/sawaiz/gLowCost-geiger`
- Git history is preserved in `.git`.
- Canonical user documentation: `README.md`.
- KiCad source: `kicad/glowcost-geiger.kicad_sch`, `.kicad_pcb`, `.kicad_pro`.
- Firmware scaffold: `firmware/`.

## Completed decisions
- 3.3 V Pi supply/control.
- CTC-5 / STS-5 tube; user supplies tube.
- C142864 tube clips are DNP and hand fitted.
- STEMMA QT connector: JST SM04B-SRSS-TB(LF)(SN), LCSC C160404, 1.0 mm pitch.
- Two 1 mm HV isolation slots.
- Default I2C address 0x2F; solder straps select 0x2F–0x32.
- 1.6 mm PCB thickness.
- 0805 green pulse LED with cuttable default-bridged enable jumper.

## Required next work
1. ~~Replace U1/U2 boundaries with ATtiny1616 + STEMMA + boost FET~~ — schematic symbols/nets in place (see `docs/kicad/attiny-schematic-revision-notes.md`). Tidy off-grid placement in Eeschema; scrub leftover TP ERC.
2. Place new footprints on the PCB (U1, L1, Q3, J4/J5, straps, pullups).
3. Re-run DRC and resolve HV clearance violations (~79 clearance errors historically).
4. Inspect the corrected tube VRML model: `kicad/models/tube.wrl`.
5. Keep HV creepage, discharge, and human review deterministic; semantic tools may rank options only.

## Jev
Run with a Keychain-loaded `TYPESAFE_API_KEY` and UTF-8 locale:
`PYTHONUTF8=1 LC_ALL=C.UTF-8 LANG=C.UTF-8 python scripts/jev_pcb_review.py`
Jev is advisory; KiCad DRC and HV rules remain authoritative.
