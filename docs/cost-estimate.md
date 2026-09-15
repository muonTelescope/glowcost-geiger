# Expected production cost

**Current revision:** J2/J3 C142864 are DNP at JLC. The anode resistors now
require external sourcing; earlier 25/50-board budgets below are historical
baselines pending that quote. The revised five-board allowance is $150–250.
See [part selections](part-selection.md).

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

- **Tube:** user already owns the tubes: **$0 new purchase cost**. They still
  need inspection, dimensional checks and electrical testing.
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

## Five-board prototype batch — tubes already owned

Use **$150–250 for five assembled electronics boards ($30–50 each)**.
Adding provisional clips/cables and one shipping allowance gives **$185–335**
before tax, enclosure, coating and test/assembly labor. Tube purchase cost is $0.
This assumes Economic one-sided SMT is available for the final design.

| Cost for the entire five-board batch | USD |
|---|---:|
| Catalog-priced candidate parts, exact 5-board tier calculation | $49.34 |
| Remaining physical circuitry and external HV parts allowance (unquoted) | $20–50 |
| Purchased excess, attrition minima and pricing reserve | $10–25 |
| Bare PCB allowance, assumed approximately 125 × 35 mm | $10–25 |
| Setup, stencil, additional extended types and SMT placement allowance | $60–85 |
| Calculated electronics total | $149–235 |
| **Rounded electronics budget** | **$150–250** |
| Clips and mating cables, provisional materials reserve | $10–25 |
| Shipping, provisional reserve | $25–60 |
| **Budget including clips/cables and shipping** | **$185–335** |

The candidate subtotal is $9.8686 per board: capacitors $3.1064, diodes $0.3712,
inductor $0.6445, two comparator/references $4.8562, timer $0.3049, switch $0.0404,
pulse transistor $0.0168, Schmitt gate $0.0651, bleeder $0.0704 and connector
$0.3927. Rates come from the stored catalog snapshot; actual component purchase
quantities can be larger than five boards consume. At this batch size, setup and
feeder charges contribute roughly $10–13 per board, so dividing the 50-board
price by ten would significantly underbudget the prototype order.

J2/J3 are DNP and incur no JLC clip procurement/placement charge. If purchased
separately, ten clips for five boards cost approximately $1.90 at the catalog
one-piece price, before vendor pack minima and freight. The existing $10–25
clips/cable reserve includes this; do not add it twice. External anode resistor
prices are not verified, so the $20–50 line is an allowance, not a quote.

### Original open-items list — superseded by current selections

Exact MPN decisions are now recorded in [part-selection.md](part-selection.md).
The following list records why those selections and physical checks were needed.


| Item | What remains |
|---|---|
| Two 2.49 MΩ anode resistors | Exact stocked MPN/footprint; each needs at least 500 V working rating and suitable pulse rating. |
| Eight 33 MΩ divider resistors; 412 kΩ and 402 kΩ bottom legs | Exact MPNs; working voltage, tolerance, temperature/voltage coefficient and leakage must support regulation and OVP accuracy. |
| Reverse base-emitter clamp and remaining passives | Choose exact protection diode and rated capacitors/resistors, including real input bypass and oscillator timing network. |
| Physical U1 HV controller | Complete LMC555 timing, transistor drive and independent regulation/OVP wiring; confirm actual comparator delay and startup behavior. U1 is currently a behavioral block. |
| Physical U2 pulse conditioning | Complete Schmitt/blanking logic, HV-ready detection, enable behavior and unpowered-host protection. U2 is currently behavioral. |
| Input soft-start/current limiting | Select and implement an actual circuit; the existing input capacitor model does not limit power-on inrush. |
| Candidate multiplier diodes and HV switch | Verify reverse stress, leakage, switching loss, drive and safe operating area with the actual circuit. |
| Candidate inductor and HV capacitors | Verify footprint, inductor saturation/DCR and capacitor electrical stress against the final implementation. |
| Tube clips | Measure the owned tube contacts; select clips, retention, spacing and attachment process. A generic fuse clip is not yet qualified. |
| Pi cable and connector footprint | Set cable length/host termination; confirm mating GH contacts/housing, pin order and SMT retention tabs. |

These can be resolved through engineering and part selection; the user-specific
inputs still needed are tube contact dimensions and preferred cable length/host
termination. After this, PCB HV spacing, routing and manufacturing checks remain.
First prototypes must verify current/inrush, HV regulation and discharge, OVP,
pulse voltage, recovery and the owned tube lot's plateau. Those checks establish
whether the design is ready for the later 25–50-board run.

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

## Placement-size update

The basic layout now measures **140 × 60 mm**, superseding the 125 × 35 mm
assumption used in the PCB allowances above. The component estimates are
unchanged; the bare-board and shipping allowances require a new supplier quote.
Do not treat the earlier totals as a quote for this larger board or scale the
entire assembly cost by board area. See [placement documentation](layout.md).
