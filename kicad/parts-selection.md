# KiCad implementation parts

These are the selected JLC candidates for replacing the two behavioral blocks.

| Function | Selected part | LCSC | Package | Key reason |
|---|---|---:|---|---|
| HV oscillator / enable | TLC555IDR (Texas Instruments) | C6987 | SOIC-8 | 3–15 V operation; 3.3 V compatible; reset pin provides EN |
| Dual feedback / pulse comparator | MCP6562T-E/MS (Microchip) | C625560 | MSOP-8 | 1.8–5.5 V, rail-to-rail I/O, push-pull output, 100 µA/channel |
| Boost inductor | B82442T1105K050 (TDK) | C2041861 | 5.6 × 5 mm SMD | 1 mH, 150 mA rated, 310 mA saturation, 9.5 Ω DCR |
| HV switch | HL2310A | C7420347 | SOT-23 | 60 V VDS, 3 A, 125 mΩ at 4.5 V |

The TLC555IDR is the lowest-voltage 555 candidate found in the JLC database; do
not substitute the 4.5 V TLC555 variants. The TDK inductor is intentionally a
larger power package than the low-cost 1812 alternatives because its current and
saturation margin are much better for the modeled 59 mA peak current.

All four parts require datasheet pinout confirmation against the local KiCad
symbols before fabrication. The project records the LCSC IDs and MPNs in the
schematic fields; the BOM must be generated from the schematic, never hand-edited.
