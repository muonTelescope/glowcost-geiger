# ATtiny-only schematic revision notes

Date: 2026-09-18 (ET)

## Architecture
- Removed behavioral U1 Analog_HV_boundary and U2 Pulse_logic_boundary.
- U1 is now ATTINY1616-MNR (stock KiCad `ATtiny1616-M` VQFN-20, LCSC C507118).
- MCU PWM-drives HV boost FET; MCU also does pulse count, I2C, ADC. No TLC555 / MCP6562.
- Keep CW multiplier, protection discretes, tube clips, Q1 pulse amp, LED, J1 Pi header.

## New power / I2C parts
| Ref | Part | LCSC | Role |
|-----|------|------|------|
| U1 | ATTINY1616-MNR | C507118 | MCU |
| L1 | B82442T1105K050 1 mH | C2041861 | Boost inductor (DCR 9.5 Ω — efficiency risk) |
| Q3 | HL2310A | C7420347 | Boost FET SOT-23 (1=G,2=S,3=D) |
| R25 | gate series | — | U1 PB2 `HV_PWM` → `GATE` → Q3.G |
| J4/J5 | SM04B-SRSS-TB | C160404 | Dual STEMMA QT (1=GND,2=V+,3=SDA,4=SCL) |
| JP2/JP3 | A0/A1 straps | — | to GND |
| R26/R27 | I2C pullups | — | SDA/SCL to V3V3 |
| R28/R29 | 3V3 sense divider | — | |
| C11 | local V3V3 decap | — | |

## Pin map (U1)
| Pad | Pin | Net |
|-----|-----|-----|
| 1 | PA2 | COLLECTOR (pulse in) |
| 4 | VCC | V3V3 |
| 5 | PA4 | SDA |
| 6 | PA5 | SCL |
| 7 | PA6 | SENSE (HV ADC) |
| 8 | PA7 | V3V3_SENSE |
| 11 | PB3 | EN |
| 12 | PB2 | HV_PWM → R25 → GATE |
| 13 | PB1 | A1 |
| 14 | PB0 | A0 |
| 19 | PA0 | UPDI |
| 20 | PA1 | UART_TX (USART0 alternate; default TX is PB2) |
| 3/21 | GND/EP | GND |
| 2,9,10,15–18 | unused | no_connect |

## Netlist checks (kicad-cli)
- `/HV_PWM`: U1.12 + R25.1
- `/GATE`: R25.2 + Q3.1
- `/SW`: L1.2 + Q3.3 + C1
- `/SDA`: U1.5 + J4.3 + J5.3 + R26.2
- `/SENSE`: U1.7 + existing HV divider

## Snapshot
`kicad/.history/glowcost-geiger.kicad_sch.before-attiny-20260918-225646`

## Still open
- ERC: many legacy TP/`#PWR` pin_not_connected (pre-existing clutter / label churn); new ATtiny block nets are connected.
- Off-grid placement warnings on Conn/jumper pins — tidy in Eeschema.
- PCB: place new footprints, clear ~79 DRC clearances — out of schematic-first scope.
- Docs to sync: `kicad/mcu-revision.md`, `kicad/parts-selection.md`, `docs/GROKBOT_HANDOFF.md`, `firmware/pins.h`.
