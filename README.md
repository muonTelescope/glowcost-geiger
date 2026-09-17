# Glowcost Geiger

Compact Raspberry Pi Geiger counter for the CTC-5 / STS-5 tube. The board takes
3.3 V, ground, power-enable, and pulse/I²C connections. HV generation and pulse
shaping are hardware based; an ATtiny1616 option provides counting, diagnostics,
and an I²C sensor interface.

> **Prototype:** the KiCad routing has known DRC clearance errors. The HV design
> is not bench-qualified or approved for fabrication. Use suitable HV procedures.

## Design summary

- Hardware HV oscillator, switch, multiplier, protection, and comparator.
- TTL pulse output plus green 0805 pulse LED with cuttable enable bridge.
- Horizontal CTC-5 / STS-5 tube under two DNP C142864 clips.
- Two STEMMA QT / SparkFun Qwiic connectors in parallel for I²C daisy chaining.
- ATtiny1616 option for pulse counting, HV/3.3 V readback, fault flags, and I²C slave registers.
- Two solder-selectable address pads on leftover MCU GPIOs.
- 120 x 32 x 1.6 mm, two-layer compact PCB.

## STEMMA QT and address selection

STEMMA QT and Qwiic use the same JST-SH 4-pin bus: GND, 3.3 V, SDA, and SCL.
The two connectors are parallel pass-through ports. Enable only one pull-up set on
each bus segment.

Address links are two-pad bridges. Open is logic-high through the ATtiny1616
internal pull-up; bridged is logic-low:

| A1 | A0 | Address |
|---:|---:|---:|
| open | open | `0x2F` |
| open | bridged | `0x30` |
| bridged | open | `0x31` |
| bridged | bridged | `0x32` |

The default `0x2F` is intentionally outside the common addresses called out by
Adafruit; firmware may later store another address. The ATtiny1616 uses UPDI
programming pads (VCC, DATA, GND), not legacy six-wire AVR ISP. UART is exposed
as through-hole debug pads only. All programming and address pads stay on the
low-voltage side.

## Mechanical design

The supplied Littelfuse 102071 drawing and local datasheet agree on the
dimensioned values: 7.6 mm tail pitch, 7.9 mm base width, 10.9 mm height,
R3.2 spring radius, 7.2 mm radius-centre height, 3.6 mm tail extension, and
2.0 +/- 0.1 mm holes. C142864 is DNP at JLC and fitted after assembly.

- [Clip datasheet](kicad/models/C142864-datasheet.pdf)
- [Clip STEP](kicad/models/C142864.step)
- [Clip STL](cad/models/C142864/C142864.stl)
- [FreeCAD source](cad/models/C142864/C142864.FCStd)
- [Annotated comparison](docs/kicad/C142864-annotated-comparison.png)

The STEP is a formed-sheet reconstruction. Bend transitions, stamping,
spring deflection, and tail-hole stamping remain approximate.

## KiCad files

- [Schematic](kicad/glowcost-geiger.kicad_sch)
- [PCB](kicad/glowcost-geiger.kicad_pcb)
- [Project](kicad/glowcost-geiger.kicad_pro)
- [Footprints](kicad/glowcost.pretty)
- [Parts selection](kicad/parts-selection.md) · [net classes](kicad/net-classes.md)
- [ATtiny1616 / STEMMA QT revision specification](kicad/mcu-revision.md)
- [Firmware bring-up and diagnostic tools](firmware/README.md)

The study retains the routed HV prototype and 72 placements. Reroute the known
clearance violations before ordering.

## Render gallery

### Board views

![Top](docs/renders/board/top.png)
![Bottom](docs/renders/board/bottom.png)
![Front](docs/renders/board/front.png)
![Back](docs/renders/board/back.png)
![Left](docs/renders/board/left.png)
![Right](docs/renders/board/right.png)

### Assembly and clip

![Assembled tube and clips](docs/layout/assembled.png)
![Tube-side view](docs/layout/tube-side.png)
![Clip preview](cad/models/C142864/preview.png)

Additional views: [board-top](docs/layout/board-top.png),
[placement](docs/layout/placement.png), [top copper](docs/layout/top-copper.png),
[bottom copper](docs/layout/bottom-copper.png), [courtyards](docs/layout/courtyards.png),
[schematic PNG](docs/kicad/schematic.png), and [schematic PDF](docs/kicad/schematic.pdf).

Renders are for review, not Gerber approval. Generic component bodies are
illustrative; tube seating and HV clearance remain unverified.

## Electrical and sourcing notes

The tube is biased near 400 V. The protected HV divider scales the sense node to
0–3.3 V for the MCU ADC; never connect an MCU pin directly to the tube supply.
Keep HV service nets away from STEMMA QT and Pi wiring.

ATtiny1616-MNR (LCSC C507118) is the preferred MCU: QFN-20, 3 x 3 mm, 16 KB
Flash, 2 KB SRAM, 10-bit ADC, I²C/TWI, timers, Event System, and UPDI. Current
LCSC pricing is typically about $0.90–1.10. See [cost-parts.json](docs/cost-parts.json)
and [review-bom.csv](docs/review-bom.csv) for the cost study.

## Reproduce outputs

```sh
npm run build:kicad
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
  /Applications/FreeCAD.app/Contents/Resources/bin/python scripts/generate_clip_model.py
blender --background --python scripts/render_clip_model.py
blender --background --python scripts/render_assembly.py
kicad-cli pcb render -o docs/renders/board/top.png \
  kicad/glowcost-geiger.kicad_pcb --side top --quality high
```

Before fabrication: integrate and lock the ATtiny schematic/layout, define the
I²C register map, verify address links, reroute DRC errors, confirm HV creepage,
and test the loaded tube assembly.
