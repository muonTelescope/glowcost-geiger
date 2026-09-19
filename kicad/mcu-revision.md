# ATtiny1616 / STEMMA QT revision (ATtiny-only)

Schematic rewrite in progress on `kicad/glowcost-geiger.kicad_sch`.
Snapshot before edit: `kicad/.history/glowcost-geiger.kicad_sch.before-attiny-20260918-225646`.
Detail notes: `docs/kicad/attiny-schematic-revision-notes.md`.

## Architecture

- **ATtiny-only:** MCU PWM-drives the HV boost FET and handles pulse count / I2C / ADC.
- **Removed:** TLC555, MCP6562, and behavioral U1/U2 boundary symbols.
- **Kept:** CW multiplier, protection discretes, tube clips, Q1 pulse amp, LED, J1 Pi header.

## Low-voltage / boost block

| Ref | Function | Notes |
|---|---|---|
| U1 | ATtiny1616-MNR, LCSC C507118 | Stock KiCad `ATtiny1616-M` VQFN-20; 3.3 V; UPDI |
| L1 | 1 mH boost inductor | B82442T1105K050, LCSC C2041861 (DCR 9.5 Ω — efficiency risk) |
| Q3 | HL2310A boost FET | LCSC C7420347; SOT-23 1=G 2=S 3=D |
| R25 | Gate series | `HV_PWM` (U1.PB2) → `GATE` → Q3.G |
| J4, J5 | STEMMA QT SM04B-SRSS-TB | LCSC C160404; 1=GND 2=V+ 3=SDA 4=SCL |
| JP2, JP3 | A0/A1 solder bridges | to GND |
| R26, R27 | I2C pull-ups | SDA/SCL to V3V3 |
| R28, R29 | 3V3 sense divider | to PA7 |
| C11 | V3V3 local decap | |
| TP23–25 | V3V3 / UPDI / GND | programming |
| TP28–29 | UART TX / GND | PA1 alternate TX |

Default I2C address `0x2F` (JP2/JP3 select).

## MCU assignments

| Pad | Pin | Net |
|-----|-----|-----|
| 1 | PA2 | COLLECTOR (pulse in) |
| 4 | VCC | V3V3 |
| 5–6 | PA4/PA5 | SDA/SCL |
| 7 | PA6 | SENSE (HV ADC) |
| 8 | PA7 | V3V3_SENSE |
| 11 | PB3 | EN |
| 12 | PB2 | HV_PWM |
| 13–14 | PB1/PB0 | A1/A0 |
| 19 | PA0 | UPDI |
| 20 | PA1 | UART_TX (USART0 alternate) |
| 3/21 | GND/EP | GND |

## Firmware behavior

MCU generates boost PWM, counts pulses, maintains rates/totals, reads HV/3V3 ADC,
exposes I2C at 0x2F, and gates EN. Raw pulse still available on J1 TTL via Q1 path.
