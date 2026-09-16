# ATtiny1616 / STEMMA QT revision

This is the implementation specification for the next KiCad revision. It keeps
the existing HV analog front end and moves only the Pi-facing timing and
telemetry functions into the ATtiny1616.

## New low-voltage block

| Ref | Function | Notes |
|---|---|---|
| U3 | ATtiny1616-MNR, LCSC C507118 | 3 x 3 mm QFN-20; 3.3 V; UPDI |
| J4, J5 | JST-SH-4 STEMMA QT/Qwiic | Parallel SDA/SCL/3V3/GND pass-through |
| JP2, JP3 | A0/A1 solder bridges | Open = pull-up/high; bridged = low |
| TP23, TP24, TP25 | UPDI VCC/DATA/GND | Pogo-pad programming footprint |
| TP28, TP29 | UART TX/RX | 3.3 V diagnostic serial pads; 115200 8-N-1 |
| R_I2C | 4.7 kΩ selectable pull-ups | Populate one bus segment only |
| R_HV1/R_HV2, C_HVADC | Protected HV ADC divider/filter | HV-service clearance applies |
| R_3V3, C_3V3 | 3.3 V monitor divider/filter | Optional if rail is already measured at U3 |

Suggested address base is `0x36`; JP2/JP3 select `0x36`–`0x39`.

## MCU assignments

- `PA2`: raw comparator pulse input; timer/Event System count source.
- `PA3`: firmware pulse output to Pi-facing TTL net.
- `PA4/PA5`: SDA/SCL.
- `PA6`: HV ADC sense.
- `PA7`: 3.3 V ADC sense.
- `PB0/PB1`: A0/A1 solder links.
- `PB2`: HV enable watchdog gate.
- `UPDI`: dedicated programming pad.

Pin assignments are provisional until the ATtiny symbol and final package
pinout are locked in the schematic.

## Parts removed or made optional

- Remove the Pi-output-only pulse-stretch RC if firmware generates `PULSE_OUT`.
- Keep comparator input filtering and any HV pulse/noise filtering in hardware.
- Remove a separate digital counter or timer IC if added during the analog-only study.
- Make I²C pull-ups selectable; do not populate duplicate pull-ups on every bus node.
- Keep the hardware HV disable path and protection clamps independent of firmware.

## Firmware behavior

The MCU counts raw pulses in hardware, produces a configurable 5–500 µs output
pulse, maintains one-second and sixty-second rates, stores total counts, reads
HV/3V3 ADC channels, and disables HV on watchdog or out-of-range conditions.
The I²C register map and calibration constants must be frozen before production.
