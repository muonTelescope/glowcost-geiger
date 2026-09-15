# Basic PCB placement and render review

**Unrouted placement study, not a fabrication release.** This tscircuit layout
reuses the functional schematic's part identities and nets. U1/U2 remain
behavioral blocks; their physical oscillator, comparators, logic and input
soft-start parts still need a complete pin-level schematic and placement.

## Mechanical plan

| Item | Current placement |
|---|---|
| Board | 140 × 60 × 1.6 mm, two copper layers, 2 mm corner chamfers |
| Assembly | All SMT on top; 44 physical footprints |
| Mounting | Four 3.2 mm nonplated holes at (±64, ±24) mm |
| Tube envelope | Assumed 110 × 12 mm, centered at (0, 18) mm |
| Clip centers | 105 mm apart; actual NOS tube contact fit must be measured |
| Tube reserve | 96 × 16 mm central keepout on both sides |
| Controller reserve | 30 × 26 mm centered at (−22, −11) mm |
| J1 | Vertical locking four-pin JST GH SMT connector |
| J2/J3 | C142864, DNP; two plated holes per clip, 7.6 mm pitch |

Coordinates use the board center as origin. The clip holes use 2.1 mm drills and
3.5 mm pads; verify the manufacturer tails, finished-hole tolerance and tube grip
before fabrication. User installation of clips and the owned tube is required.
Chamfers and mounting positions are provisional mechanical choices.

J1 pad geometry follows the [official KiCad JST GH footprint](https://github.com/KiCad/kicad-footprints/blob/master/Connector_JST.pretty/JST_GH_BM04B-GHS-TBT_1x04-1MP_P1.25mm_Vertical.kicad_mod)
and should be checked against the [JST GH drawing](https://www.jst-mfg.com/product/pdf/eng/eGH.pdf).
Clip ratings and source references are in [part selection](part-selection.md).

## Render gallery

![Native 3D placement preview](layout/3d.png)

The native tscircuit 3D preview uses generic passive/semiconductor packages.
It does not include the tube or accurate JST/clip bodies, so it cannot establish
mechanical interference clearance. Red hatching is the tube keepout.

![Top placement](layout/placement.png)

Vector images: [placement](layout/placement.svg), [top copper](layout/top-copper.svg),
[bottom copper](layout/bottom-copper.svg), [silkscreen](layout/silkscreen.svg),
[drill](layout/drill.svg), [courtyards](layout/courtyards.svg).
PNG versions are embedded in the [main README](../README.md#pcb-renders-and-layer-views).
These views filter actual tscircuit PCB artwork; they are not Gerber exports.
Bottom copper contains only plated clip-hole annuli. Drill artwork retains those
annuli for reference. Cyan courtyard boxes bound component assembly space.

## Verification and assembly data

[Automated checks](layout/checks.json) verify 44 part identities against the
schematic, courtyard presence/non-overlap, board bounds, tube/controller reserves,
mounting hardware reserves and DNP clip-hole retention. There are zero traces,
vias and planes. These checks do not verify electrical connections or HV spacing.

[Review coordinates](layout/placement.csv) are for inspection, not production
pick-and-place. [Published circuit JSON](layout/circuit.json) retains the clip
geometry with DNP restored. During geometry generation the DNP flag is temporarily
cleared because this tscircuit version otherwise omits the holes. The
[review BOM](review-bom.csv) excludes both clips from population.

The build retains connector-orientation heuristic warnings, missing schematic
sheet warnings and incomplete pin-attribute warnings, recorded in the check
report. Vertical connector access and actual tube insertion need mechanical
review. No KiCad DRC or complete 3D interference check has been performed.

## Remaining work before fabrication

- Complete and verify the physical U1/U2 circuitry, including soft-start and blanking.
- Measure tube contacts and confirm clip grip, spacing, insertion and enclosure fit.
- Route the converter with short switching loops and local bypassing; keep the
  HV ladder and high-impedance sensing away from Pi signals.
- Establish HV creepage/clearance rules for the actual materials and environment;
  inspect pads, holes, board edges and both copper layers. The current keepout
  and default CAD spacing rules do not establish a safe HV insulation rating.
- Add final silkscreen polarity, pin-one and assembly markings, then review
  fabrication outputs and production BOM/placement rotations.
- Re-quote the larger PCB and qualify protection and Pi rail behavior on hardware.

## Reproduce

From the repository root after installing dependencies:

```sh
bun run build
bun run bom:review
bun run build:layout
bun run render:layout
```

The export script checks placement, writes review data, renders six SVG/PNG
views using `rsvg-convert`, and copies the native tscircuit 3D PNG into `docs/layout`.
