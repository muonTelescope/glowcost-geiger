# Expected production cost

Budget dated 2026-09-15, USD. **Allow $14–19 per assembled electronics board at
25 units, or $12–16 at 50 units.** This is a planning estimate, not a supplier
quote. It excludes the NOS tube, clips, mating cable, enclosure, coating/potting,
shipping, tax/duty, engineering, calibration and functional-test labor.

The design still contains behavioral controller blocks. A price obtained by
counting only the drawn components would omit essential physical circuitry.

## Catalog-priced candidate parts

Prices use the quantity of each part in the entire batch, before assembly attrition.
The source snapshot includes MPNs, stock, tier quantities and supplier links in
[cost-parts.json](cost-parts.json). Catalog pricing may differ from JLC PCBA checkout.

| Part / function | Per board | Cost/board, 25 boards | Cost/board, 50 boards |
|---|---:|---:|---:|
| TDK 10 nF / 630 V C0G, C342714 | 8 | $2.3232 | $2.3232 |
| BAV21W multiplier diode, C155214 | 8 | $0.3040 | $0.3040 |
| TDK 1 mH inductor, C2041861 | 1 | $0.5224 | $0.4606 |
| TLV3012B comparator + reference, C20345924 | 2 | $4.3680 | $3.8700 |
| LMC555 oscillator, C90760 | 1 | $0.3049 | $0.2455 |
| MMBTA42 HV switch, C94389 | 1 | $0.0404 | $0.0404 |
| MMBT3904 pulse transistor, C81464 | 1 | $0.0168 | $0.0168 |
| SN74LVC1G14 Schmitt gate, C7835 | 1 | $0.0651 | $0.0651 |
| 10 MΩ bleeder, C26119 | 4 | $0.0704 | $0.0704 |
| JST GH locking SMT connector, C161692 | 1 | $0.3927 | $0.3404 |
| **Candidate subtotal** | **28** | **$8.4079** | **$7.7364** |

These are candidate quantities, not an orderable production BOM. In particular,
the two independent reference channels must remain independent if the OVP
architecture is retained. The Schmitt gate alone does not implement blanking.

## Completion and manufacturing allowances

The following amounts are engineering allowances, not researched part quotes:

| Additional cost per board | 25 boards | 50 boards |
|---|---:|---:|
| Remaining resistors/capacitors, HV-rated anode resistors, clamps, blanking logic, input soft-start and driver support | $1.50–3.50 | $1.50–3.50 |
| Purchased excess/attrition and price variation | $0.50–1.20 | $0.45–1.10 |
| Bare two-layer PCB | $0.80–2.00 | $0.60–1.50 |
| Economic SMT assembly, setup and feeder allowance | $2.10–2.90 | $1.10–1.70 |
| **Calculated assembled electronics estimate** | **$13.31–18.01** | **$11.39–15.54** |
| **Rounded working budget** | **$14–19** | **$12–16** |
| **Batch working budget** | **$350–475** | **$600–800** |

PCB allowance assumes a simple approximately 125 × 35 mm two-layer FR-4 board,
one-sided SMT, ordinary finish and no special fabrication. Dimensions are a
costing assumption, not an approved layout. The 110 mm tube prevents assuming
the promotional 100 × 100 mm board price. Final HV spacing and clips can enlarge it.

Assembly uses approximately 120–180 solder joints and 12–18 distinct extended
part numbers: $8.18 setup + $1.53 stencil + $3.07 per extended type, plus
$0.0016 per SMT joint. That gives about $51–72 per batch at 25 boards and
$56–79 at 50, before any checkout-specific adjustments. The fee is per distinct
extended part number, not per placement; eight identical HV capacitors use one
feeder. These published charges are from [JLC's assembly price schedule](https://jlcpcb.com/help/article/pcb-assembly-price).

Economic assembly eligibility, exact feeder count, attrition minima, tooling
rails, panelization and potential additional handling must be checked on the
final design. Standard assembly may cost more. No promotional discounts are
assumed. The excess allowance is a budget reserve, not JLC's attrition formula.

## Costs outside the electronics board

- **Tube:** excluded; use actual landed cost of the intended NOS lot. No
  qualified tube supplier/lot price has been established. Existing tubes have
  zero new purchase cost but still need inspection and testing.
- **Clips and mating Pi cable:** carry a separate provisional **$2–5 per unit**
  materials reserve until exact clips, cable length and terminations are chosen.
  This is not a vendor quote and excludes fitting/crimping labor.
- **Shipping:** carry **$25–60 per shipment** as a provisional reserve only;
  destination and service are not specified. Taxes and import duties are extra.
- Enclosure, coating/potting, assembly of the tube, HV checks, plateau testing,
  count-response checks and any calibration require separate budgets.

For example, a 50-board electronics order plus the clips/cable reserve and one
shipping reserve would be **$725–1,110**, before tubes, enclosure, labor and tax.
Two separately shipped prototype/production orders incur separate setup and freight.

## Where cost reduction matters

1. The two reference/comparator ICs cost $3.87–4.37 per board. Investigate a
   lower-cost implementation while preserving two independent references,
   input leakage limits, accuracy, startup behavior and protection. Savings are
   not included until the replacement circuit is qualified.
2. The eight selected capacitors cost $2.32 per board at both batch sizes.
   At 50 boards, buying 500 instead of 400 at the quoted 500-piece tier costs
   $126.80 versus $116.16: more cash despite the lower unit price. Do not buy
   excess merely to claim a cheaper per-capacitor figure.
3. Basic/Preferred substitutes save feeder charges. Eliminating one extended
   type saves about $0.123 per board at 25 or $0.061 at 50. Qualify substitutions;
   HV working voltage and leakage take priority over these small savings.
4. Keep assembly on one side and install tubes after reflow/cleaning. Retain
   the requested locking SMT connector; its material cost is only $0.34–0.39.

The next accurate pricing milestone is a pin-complete BOM plus routed board,
followed by JLC's actual fabrication/assembly quote. This document does not
authorize purchasing or establish that the hardware is ready for manufacture.
