# Selected parts and assembly policy

2026-09-15. Selection follows the user's [BOM skill](/Users/sawaiz/agent-skills/kicad-bom/SKILL.md): exact MPNs, package/rating checks, C0G for precision capacitors, thin-film sensing resistors, and Basic parts where appropriate. User authorized choosing remaining packages/parts. Catalog records are in [selected-parts-snapshot.json](selected-parts-snapshot.json).

## Tube clips: selected, DNP

**J2 and J3: Littelfuse 10207101009 / C142864, two per board, DNP at JLC.**
Each clip has two solder tails connected to the same electrode. J2 is ANODE;
J3 is CATHODE. GM1 remains the owned tube's electrical representation.

The [manufacturer drawing](https://www.littelfuse.com/assetdocs/fuse-clip-520-521-and-102071-datasheet?assetguid=d82d8702-e379-43c1-b009-e03f91ba79c0)
specifies a 6.3 mm contact diameter, 7.6 mm pin spacing, 0.5 × 1.5 mm tails and
500 V rating for 102071. The JLC catalog's 250 V field conflicts with this;
use the manufacturer specification for review. This does not establish the
assembled board's insulation rating or confirm fit on a particular NOS tube.

Source footprint uses 7.6 mm spacing, 2.1 mm finished drill and 3.5 mm copper
diameter. Final drill tolerance, courtyard and actual tube-end fit require
mechanical review. DNP is encoded in `parts.tubeClip.doNotPlace` and the
generated [review inventory](review-bom.csv), not merely a printed note.
The functional schematic build disables PCB output. The separate placement study
retains clip holes/pads by generating their geometry before restoring DNP in the
published circuit JSON. The tscircuit `doNotPlace` flag otherwise skips placement.
The review inventory remains authoritative for population; J2/J3 must be excluded
from assembly procurement and placement. See [layout notes](layout.md).

DNP means the delivered JLC assembly lacks these clips. User installation is
required before the tube can be connected. Do not silently order or populate them.

## Parts instantiated in the functional schematic

| References | Selection | Reason |
|---|---|---|
| R1–R4, R_OV1–R_OV4 | FOJAN FRG2512F3305TS, C5126202; 33 MΩ, 1%, 2512 | 15,269 catalog stock; conservatively use 200 V working rating, versus about 100 V per leg. |
| R5 | RESI PTFR0603B412KP9, C47115896; 412 kΩ, 0.1%, 25 ppm/°C, 0603 | Thin-film precision feedback sensing; 1,163 stock. |
| R_OVBOT | Yageo RT0603BRD07402KL, C705774; 402 kΩ, 0.1%, 25 ppm/°C, 0603 | Thin-film precision cutoff sensing; 3,226 stock. |
| R_A1, R_A2 | Vishay CRHV1206AF2M49FKEF; 2.49 MΩ, 1%, 1206 | High-voltage exception to JLC preference; preserves existing 4.98 MΩ model. |
| R_EN, R_K, R_PROTECT | UNI-ROYAL 0603WAF1003T5E, C25803; 100 kΩ, 0603 | Basic, >23 million catalog stock; adequate for modeled low-voltage nodes. |
| R_COL | UNI-ROYAL 0603WAF4702T5E, C25819; 47 kΩ, 0603 | Basic, >2 million stock. |
| R_OUT | UNI-ROYAL 0603WAF1001T5E, C21190; 1 kΩ, 0603 | Basic, >24 million stock. |
| C9 | Samsung CL10C101JB8NNNC, C14858; 100 pF, 50 V C0G, 0603 | Basic; stable feedback capacitance. |
| C_OV | Samsung CL10C100JB8NNNC, C1634; 10 pF, 50 V C0G, 0603 | Basic; stable cutoff capacitance. |
| D_NEG | Semtech 1N4148W, C81598, SOD-123 | Basic reverse base-emitter clamp; ST(Semtech) is not STMicroelectronics. |

Retain the existing TDK 630 V C0G multiplier capacitors, BAV21W diodes, 10 MΩ
bleeders, onsemi pulse transistor and genuine JST GH connector.

### HV resistor decisions and limits

The [FOJAN FRG family datasheet](https://datasheet.lcsc.com/lcsc/2411071710_FOJAN-FRG0805J276-TS_C42372202.pdf)
supports the high-resistance family and 2512 dimensions. Thin-film 33 MΩ parts
meeting stock requirements were not found; the stocked thick-film selection is
an exception to the thin-film preference. At 400 V, each upper divider resistor
dissipates about 0.30 mW. Temperature coefficient is 200 ppm/°C: allow up to
approximately 0.56% ratio drift for a 25°C change relative to a 25 ppm/°C bottom
leg before other effects. Voltage coefficient and contamination leakage still
need qualification; selecting 0.1% bottom resistors does not make the entire
divider accurate to 0.1%.

The [Vishay CRHV datasheet](https://www.vishay.com/docs/68002/crhv.pdf) gives the
1206 family 0.30 W and a 1500 V ceiling, subject to the lower power-derived
working voltage. For 2.49 MΩ, sqrt(0.30 × 2.49 MΩ) is about **864 V** at full
rated power, still above the required 500 V. At 440 V across one surviving
resistor, dissipation is about 78 mW. Apply temperature derating and verify
pulse stress. JLC searches found only 200 V 2.49 MΩ candidates; those were
rejected. No JLC code or verified distributor inventory is assigned to the
Vishay part. External sourcing/consignment or local fitting must be quoted
before purchasing; it is a selected electrical part, not procurement-ready.

## Parts selected for the physical controller implementation

[implementation-parts.ts](../board/implementation-parts.ts) records these choices.
They are **not yet wired into U1/U2**, and are excluded from the generated
functional schematic inventory. The existing SPICE results still describe the
original behavioral controller and 22 µF ideal input model.

- Retain LMC555CMX/NOPB / C90760, MMBTA42LT1G / C94389 and TDK
  B82442T1105K050 / C2041861 for the oscillator, HV switch and 1 mH inductor.
  This retains the starting topology; drive/timing networks and switching loss
  must be resolved in the physical circuit.
- Retain **two separate TLV3012BIDBVR / C20345924** reference/comparator ICs.
  Their cost is accepted to preserve independent regulation and cutoff references.
- Use TI SN74LVC1G14DBVR / C7835, SN74LVC1G08DBVR / C7666 and
  SN74LVC1G32DBVR / C10096 for Schmitt conditioning and enable/fault gating.
  Actual gate quantities and HV-ready comparator wiring follow the final logic.
  Do not claim that an Ioff-capable gate alone protects every Pi power sequence.
- Use **TPS22918TDBVRQ1 / C2653760** for controlled input slew, SOT-23-6,
  3,540 stock, rather than the smaller fixed-slew TPS22919. The
  [TI datasheet](https://www.ti.com/lit/ds/symlink/tps22918-q1.pdf) gives a
  configurable ramp. Start with Murata GRM1885C1H103JA01D / C85973,
  **10 nF C0G 0603** on CT: typical 10–90% rise is about 17.5 ms at 3.3 V.
  This is **not a current limiter** and does not provide short-circuit or reverse
  current protection. It is selected for capacitive-inrush reduction.
- Select Murata GRM32ER61C476KE15L / C77101, **47 µF / 16 V X5R / 1210**
  behind the slew switch. Require at least 22 µF effective after DC bias,
  tolerance, aging and temperature; check manufacturer curves before release.
  Do not substitute nominal 47 µF into the existing simulation and call it
  validated. At 47 µF nominal and a 17.5 ms 10–90% ramp, capacitor charging
  current is approximately 47 µF × 2.64 V / 17.5 ms = **7.1 mA**, plus load;
  this is typical arithmetic, not a guaranteed startup-current limit.
- Use Samsung CL10B105KB8NQNC / C5199872, 1 µF / 50 V X7R / 0603 for
  input bypass (use enough parallel parts to meet TI's 1 µF effective minimum
  after derating), and Yageo CC0603KRX7R9BB104 / C14663, 100 nF / 50 V X7R /
  0603 at each IC. Bypass in front of the slew switch still causes a smaller
  hot-plug transient and must be included in rail-droop testing.

## Release boundary

All previously drawn passive parts now have exact selections. Remaining work is
physical circuit implementation, anode-resistor sourcing, clip-fit verification,
PCB layout, and bench qualification. The choices above do not turn behavioral
blocks into a production-ready circuit. No new HV performance claims are made.
