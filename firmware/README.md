# gLowCost-geiger firmware

Open-source ATtiny1616 bring-up firmware for the low-voltage revision. The
firmware is intentionally conservative: HV is disabled until the watchdog and
ADC paths are initialized, raw pulses are counted in hardware, and UART output
is available before the I²C protocol is enabled.

## Open-source toolchain

- `avr-gcc` and `avr-binutils` for compilation
- `avr-libc` for device headers and startup code
- `pymcuprog` with a UPDI adapter for programming
- `avrdude` may be used with a compatible UPDI backend

Install on macOS with Homebrew:

```sh
brew install avr-gcc avrdude
python3 -m pip install pymcuprog
```

Build:

```sh
make
```

The output is `build/gLowCost-geiger.elf`, `.hex`, and `.lst`.

## Bring-up pads and provisional pin map

| Signal | ATtiny1616 | PCB label | Purpose |
|---|---|---|---|
| `PULSE_IN` | PA2 | TP23 | Raw comparator pulse; timer/event counter input |
| `PULSE_OUT` | PA3 | TP24 | Reserved; Pi TTL remains raw hardware pulse |
| `SDA` | PA4 | J4/J5 SDA | STEMMA QT/Qwiic I²C |
| `SCL` | PA5 | J4/J5 SCL | STEMMA QT/Qwiic I²C |
| `HV_SENSE` | PA6/ADC | TP25 | Protected HV divider |
| `V3V3_SENSE` | PA7/ADC | TP26 | 3.3 V monitor divider |
| `ADDR_A0` | PB0 | JP2 | Address strap, internal pull-up |
| `ADDR_A1` | PB1 | JP3 | Address strap, internal pull-up |
| `HV_ENABLE` | PB2 | TP27 | Watchdog-safe HV enable |
| `UART_TX` | PB3 | TP28 | 3.3 V diagnostic UART output |
| `UART_RX` | PB4 | TP29 | 3.3 V diagnostic UART input |
| `UPDI` | UPDI | TP30 | Programming/debug data |
| `3V3/GND` | VDD/VSS | TP31/TP32 | Programming and scope reference |

The pin mux and exact package pad numbers must be checked against the final
ATtiny1616 symbol before the native KiCad schematic is released.

## Diagnostic protocol

UART is 115200 8-N-1. On reset the firmware prints an identification line,
address strap state, raw pulse count, HV ADC code, and 3.3 V ADC code once per
second. Commands are intentionally simple:

- `i` - identification and pin map
- `c` - clear counters
- `h` - toggle requested HV enable (hardware watchdog still applies)
- `r` - print the current diagnostic record

The planned I²C slave register map is documented in `kicad/mcu-revision.md`.
The first bring-up image leaves I²C in a safe disabled state until the final
address and pin mux are verified on hardware.

## Safety behavior

- HV enable starts low.
- Watchdog resets the MCU if the main loop stops servicing it.
- ADC values are telemetry only; they do not replace the resistor-chain and
  clamp protection.
- The Pi-facing pulse remains a raw hardware comparator signal; the MCU does not
  stretch it in firmware.
