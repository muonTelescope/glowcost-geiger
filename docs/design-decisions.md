# Design decisions and part candidates

This is a tscircuit **functional design and SPICE study**, not an assembly release.
JLC parts are preferred. Parts below are candidates, and U1/U2 in the schematic
are behavioral blocks, not orderable ICs. Pin-level controller implementation,
qualified protection components, PCB routing, ERC/DRC and bench verification remain.

## Requirements

- Supply: **3.3 V**, replacing the initial 5 V request; test supply ±5%.
- Host: Raspberry Pi; 3.3 V pulse output and active-high 3.3 V enable.
- Exactly four external connections: 3V3, GND, PULSE, EN.
- Same CTC-5 / STS-5 (СТС-5) tube as geiger2; ~400 V bias.
- No MCU, firmware, radio, battery, display or external HV/sense connector.
- Provisional connector: 1×4 2.54 mm header, tube mounted beside the circuit.
- Provisional passives: 0603 low voltage; 1206 or larger for HV ratings.
- EN has 100 kΩ pulldown. EN stops switching and blanks pulses; it is not
  galvanic isolation, instant HV discharge, or a zero-current power disconnect.

## JLC catalog review · 2026-09-15

Inventory is a database snapshot, not a reservation. Prefer Basic/Preferred when
an exact part meets ratings; do not substitute similarly named manufacturers.
Parts are not locked until their datasheets and footprints are qualified.

| Function | Candidate MPN | LCSC | Package | Decision |
|---|---|---|---|---|
| CW capacitors, 8×10 nF | TDK C3216C0G2J103JT000N | C342714 | 1206 | C0G, 630 V, ±5%; avoids X7R bias loss |
| CW diodes | Diodes Inc. BAV21W-7-F | C155214 | SOD-123 | 200 V DC catalog rating; verify reverse stress and hot leakage |
| Inductor | TDK B82442T1105K050 | C2041861 | 5.6×5 mm | 1 mH, 9.5 Ω DCR, 150 mA rated, 310 mA catalog saturation; confirmation requested |
| Regulation and separate OVP reference | TI TLV3012BIDBVR | C20345924 | SOT-23-6 | Two separate comparator/reference channels; behavioral models presently |
| Oscillator | TI LMC555CMX/NOPB | C90760 | SOIC-8 | Candidate; actual 10 kHz / 20 µs pulse circuit not implemented |
| HV switch | onsemi MMBTA42LT1G | C94389 | SOT-23 | Candidate; base drive, SOA and switching loss not implemented in ideal switch model |
| Pulse transistor | onsemi MMBT3904LT1G | C81464 | SOT-23 | Generic NPN model presently; current-limited base and grounded emitter |
| 3.3 V pulse conditioning | TI SN74LVC1G14DBVR | C7835 | SOT-23-5 | Candidate only; extra blanking logic required |
| Passive bleeder, 4×10 MΩ | Yageo RC1206FR-0710ML | C275643 | 1206 | Catalog 200 V / 0.25 W / 1%; low catalog stock; qualify alternate |
| Divider, anode resistors, protection diode, connector | TBD | — | — | Exact MPNs remain open |

The previously searched **SN74HCT14 is rejected for this 3.3 V design**: its
recommended supply starts at 4.5 V. The JLC search also confused MΩ with mΩ;
those milliohm results are rejected. The returned 33 MΩ 5% resistor is not locked
for a precision OVP divider. See [original search records](parts-snapshot.json)
and [3.3 V searches](parts-3v3-snapshot.json).

## HV protection and limits

1. **Independent OVP channel:** separate 4×33 MΩ / 402 kΩ divider and reference
   inhibit switching above nominal 409.06 V. A 10 pF sense capacitor gives about
   4.01 µs time constant. This is a nominal behavioral protection study: reference
   accuracy, resistor tolerances, comparator delay and switching energy can raise
   the trip peak. A worst-direction 1% reference / 1% divider corner is simulated;
   temperature, leakage and real comparator delay still need qualification. The same reference must not be shared with the main loop.
2. **Passive discharge:** 4×10 MΩ from HV to ground, independent of enable or
   logic supply. Each leg sees ~100 V, 1 mW at 400 V. Total bleeder draw is 10 µA,
   4 mW. Neither disabling EN nor removing power proves the capacitors discharged.
3. **Tube current limiting:** 2×2.49 MΩ series anode resistors. At 440 V a
   tube short is limited to at most ~88.4 µA before cathode resistance. With one
   resistor shorted, the surviving resistor could see almost all HV: each anode
   resistor must therefore be rated for at least 500 V working voltage and the
   appropriate pulse load. A generic 1206 200 V part is insufficient here.
4. **Pi pulse protection:** 100 kΩ cathode return, 100 kΩ base resistor, grounded
   NPN emitter and reverse base-emitter clamp. There is no intentional HV-to-GPIO
   path. Collector is pulled up to local 3.3 V through 47 kΩ; output has 1 kΩ
   series resistance and a modeled 100 kΩ / 50 pF receiver. This shares ground;
   it is not galvanically isolated. Protect against unpowered-host backfeed in
   the physical logic implementation.
5. **Layout/enclosure:** keep HV and tube terminals physically away from J1 and
   Pi wiring, and cover exposed HV. Establish HV creepage and clearance from
   environment, material and applicable requirements before routing. Ordinary
   JLC minimum trace clearance is not an HV spacing rule. Schematic symbols
   and candidate packages do not constitute a creepage/clearance check.

The modeled faults are open main feedback, tube short and disabled startup.
Unmodeled faults include an OVP-divider open, switch short, clamp failure,
contamination/flashover, anode resistor failure, and external HV injection.
This repository does **not** certify Pi protection or touch safety.

## Primary references

- [ADI CN0536](https://www.analog.com/en/resources/reference-designs/circuits-from-the-lab/cn0536.html): multiplier and tube detection reference.
- [TI TLV3012B](https://www.ti.com/lit/ds/symlink/tlv3012.pdf): supply, reference accuracy and comparator behavior.
- [TI SN74LVC1G14](https://www.ti.com/lit/ds/symlink/sn74lvc1g14.pdf): 3.3 V Schmitt logic candidate.
- [TDK B82442T](https://www.tdk-electronics.tdk.com/inf/30/db/ind_2008/b82442t.pdf): inductor family.
- [onsemi MMBT3904](https://www.onsemi.com/pdf/datasheet/mmbt3904lt1-d.pdf): pulse transistor.
- [Raspberry Pi GPIO guidance](https://pip-assets.raspberrypi.com/categories/685-whitepapers-app-notes-compliance-guides/documents/RP-006553-WP/A-history-of-GPIO-usage-on-Raspberry-Pi-devices-and-current-best-practices): 3.3 V interfaces.

Decision workflow: the user's `~/agent-skills/kicad-bom/SKILL.md` is used for
JLC lookup, packages, rating/derating and exact-part review. Circuit authoring
remains tscircuit as requested; no KiCad project or manufacturing BOM is implied.
