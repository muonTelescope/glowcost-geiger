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
| [`cad/models/`](cad/models/) | Tube / clip mechanical sources (Blend, STL, STEP) |
| [`sim/`](sim/) | SPICE decks for the HV chain |
| [`manufacturing/`](manufacturing/) | Fab notes (Gerbers go in GitHub Releases) |
| [`docs/images/`](docs/images/) | README figures |

## Board and schematic

![Board top](docs/images/board-top.png)

![Board bottom](docs/images/board-bottom.png)

![Schematic](docs/images/schematic.png)

## Design summary

- Hardware HV boost, Cockcroft–Walton multiplier, protection, and pulse path
- ATtiny1616-MNR drives `HV_PWM`, counts pulses, serves I²C, reads A0/A1 straps
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

UPDI pads for programming; UART TX on PA1 for debug. Keep programming and
address pads on the low-voltage side.

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

## Mechanical

Clip CAD (Littelfuse 102071 / LCSC C142864):

- [`pcb/models/C142864.step`](pcb/models/C142864.step)
- [`cad/models/C142864/`](cad/models/C142864/) (FreeCAD, STL, datasheet)

Tube body for KiCad 3D: [`pcb/models/tube.step`](pcb/models/tube.step)
(~108 × 11 × 11 mm, from the project STL/Blend). Sources:
[`cad/models/tube.blend`](cad/models/tube.blend), [`cad/models/tube.stl`](cad/models/tube.stl).
Re-export: `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd scripts/export_tube_step.py`.

A reference Inventor part [`cad/models/SBM-20-reference.ipt`](cad/models/SBM-20-reference.ipt)
is kept for history; the board STEP above is what KiCad uses.

## Firmware

Build with the Makefile in [`firmware/`](firmware/). Pins are in
`firmware/pins.h` and match the table above.

## Simulation

```bash
python3 scripts/simulate.py
```

Optional: `python3 scripts/sync_spice_model.py` then re-run.

## Fabrication

Treat this as a study board until DRC and HV clearance are clean. Order notes
belong under [`manufacturing/`](manufacturing/); release Gerbers via GitHub
Releases rather than committing them here.
