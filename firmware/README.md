# firmware

ATtiny1616 firmware for gLowCost-geiger. CTC-5 / STS-5 and SBM-20 use the same ~400 V setpoint. The tube byte only records which one is fitted.

## Build

```bash
make -C firmware
```

Requires an `avr-gcc` that includes the ATtiny1616 header (Homebrew `osx-cross/avr/avr-gcc@14` does; the `@9` avr-libc does not). The Makefile uses `@14` when it is installed and the `avr-gcc` on `PATH` is too old. Flash with `make -C firmware flash` (pymcuprog / UPDI). The image clears the factory clock prescaler and runs at 20 MHz from the internal oscillator.

## High voltage

PB2 (TCA0 WO2) is 10 kHz. Boot leaves the duty at 0, so the tube stays down until the host sets CTRL bit 0. Enabling starts at 1% and steps one timer count every 10 ms until PA6 is near code 386 (~400 V when VDD is 3.3 V). The hold band is ±8 counts. Duty stops at 400 counts (20%).

- Code 405 (~420 V) clears the duty. It restarts at 1% once the sense falls to 376 (~390 V).
- If duty sits at the 20% ceiling for 200 ms and the sense is still below the setpoint, the loop latches off. An open sense wire or a tube short does this. Write control 0, then 1, to try again.
- Register `TARGET` can move the setpoint. Values are clamped to 200…404 so a host write stays under the trip.
- The 412 kΩ sense leg is sampled slowly (ADC clock /64, longest sample) because that node is high impedance.

There is no enable pin. PB3 is unconnected.

## Pulses

PA2 counts the rising edge on Q1’s collector. A blank of about 200–300 µs drops a second edge from the same pulse. That blank is not a measured tube dead time, and the firmware does not convert counts to dose rate.

## I2C

TWI0 slave on PB1 SDA and PB0 SCL. Pull-ups are R26 and R27. Open straps read `0x2F`. Bridging A0 (PC0), A1 (PC1), or both to ground selects `0x30`, `0x31`, or `0x32`.

Write the register address, then data. A repeated start reads from that address. Multi-byte values are little-endian. Each read transaction copies the live values once, at SLA+R.

| Addr | Name | Access | Contents |
| --- | --- | --- | --- |
| `0x00` | ID | R | `0x47` |
| `0x01` | FW | R | `0x01` |
| `0x02` | STATUS | R | bit0 HV on, bit1 OVP, bit2 in band, bit3 latched fail |
| `0x03` | CTRL | R/W | bit0 `1` run, `0` stop and clear a latch |
| `0x04` | COUNT | R | uint32 pulses since boot or the last clear |
| `0x08` | CPS | R | uint16 pulses in the previous RTC second |
| `0x0A` | HV_ADC | R | uint16 latest PA6 code |
| `0x0C` | DUTY | R | uint16 PWM compare |
| `0x0E` | TARGET | R/W | uint16 PA6 setpoint, default 386 |
| `0x10` | TUBE | R/W | `0` either, `1` CTC-5/STS-5, `2` SBM-20 |
| `0x11` | CMD | W | `0xA5` clears COUNT |

USART0 alternate TX on PA1 still prints the address and a one-second line at 115200 8N1. There is no interrupt pin back to the host.

```python
# Bus 1, open straps. smbus2 or the kernel i2c interface.
bus.write_byte_data(0x2F, 0x03, 0x01)  # HV on
block = bus.read_i2c_block_data(0x2F, 0x04, 6)  # COUNT, CPS
```
