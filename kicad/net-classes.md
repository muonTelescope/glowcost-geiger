# Net classes

The PCB uses explicit net classes rather than one global clearance:

| Class | Nets | Width | Clearance | Use |
|---|---|---:|---:|---|
| `PI_SIGNAL` | TTL, EN, DRIVE, LED_*, BASE, COLLECTOR | 0.20 mm | 0.20 mm | Raspberry Pi and low-voltage logic |
| `LV_POWER` | V3V3, GND, SW | 0.30 mm | 0.25 mm | Supply and switch current |
| `HV_SENSE` | SENSE, OVP, DIV1–3, OV1–3, BL1–3 | 0.25 mm | 0.50 mm | High-impedance measurement nodes |
| `HV_SERVICE` | ANODE, ANODE_MID, CATHODE, P1–P4, S1–S4 | 0.40 mm | 1.50 mm | Exposed tube and multiplier nets |

The 1.50 mm rule is a conservative prototype starting point, not a 400 V
clearance certification. Creepage, coating, altitude, pollution degree and the
actual resistor/package working-voltage ratings still need an engineering review.
