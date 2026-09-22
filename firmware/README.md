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
- Enable is firmware. A fault clears the duty. PB3 is not an enable pin
- Pulse count on PA2; status on USART0 alternate TX (PA1)
- Address straps PC0/PC1 select I²C base `0x2F`…`0x32`
- TWI0 is PB1 SDA and PB0 SCL. This bring-up does not start the slave

No hardware OVP comparator on this revision — do not run HV without this
firmware (or equivalent) enforcing the SENSE clamp.
