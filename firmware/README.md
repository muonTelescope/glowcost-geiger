# firmware

ATtiny1616 bring-up for gLowCost-geiger.

## Build

```bash
make -C firmware
```

Requires `avr-gcc`. Flash with `make -C firmware flash` (pymcuprog / UPDI).

## Behavior

- **HV_PWM** on PB2 (TCA0 WO2), 10 kHz, soft-start to 20% duty
- **Software OVP** on PA6 `SENSE` — trip ~420 V (ADC 405), recover ~390 V
- **EN** (PB3) cleared for the fault duration
- Pulse count on PA2; status on USART0 alternate TX (PA1)
- Address straps PB0/PB1 select I²C base `0x2F`…`0x32` (host later)

No hardware OVP comparator on this revision — do not run HV without this
firmware (or equivalent) enforcing the SENSE clamp.
