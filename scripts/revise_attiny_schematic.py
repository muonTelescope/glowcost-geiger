#!/usr/bin/env python3
"""ATtiny-only schematic revision: remove U1/U2 boundaries, add MCU + boost + STEMMA."""
from __future__ import annotations
import copy, json, shutil, uuid
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kicad_sexpr import parse, dump, Atom, children, child, walk

ROOT = Path(__file__).resolve().parents[1]
KICAD = ROOT / "kicad"
SCH = KICAD / "glowcost-geiger.kicad_sch"
SYM = KICAD / "Glowcost.kicad_sym"
SYMDIR = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")
E = lambda size=1.27: ["effects", ["font", ["size", size, size]]]
A = Atom

def uid(s: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "glowcost-attiny/" + s))

def extract_symbol(lib_path: Path, name: str) -> list:
    text = lib_path.read_text()
    pat = f'(symbol "{name}"'
    idx = text.find(pat)
    if idx < 0:
        raise KeyError(name)
    i, depth = idx, 0
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return parse(text[idx : i + 1])
        i += 1
    raise ValueError(name)

def resolve_extends(lib_path: Path, name: str) -> list:
    """Return fully materialized symbol (inlines extends parent pins/geometry)."""
    chain = []
    n = name
    while n:
        block = extract_symbol(lib_path, n)
        chain.append(block)
        ext = child(block, "extends")
        n = ext[1] if ext else None
    # base is last; overlays are earlier (more derived)
    base = copy.deepcopy(chain[-1])
    # strip extends from result and set name
    base = [x for x in base if not (isinstance(x, list) and x and x[0] == "extends")]
    base[1] = name
    # apply property overrides from derived (chain[0] is most derived)
    if len(chain) > 1:
        derived = chain[0]
        props = {p[1]: p for p in children(derived, "property")}
        out_props = []
        seen = set()
        for p in children(base, "property"):
            if p[1] in props:
                out_props.append(copy.deepcopy(props[p[1]]))
                seen.add(p[1])
            else:
                out_props.append(p)
        for k, p in props.items():
            if k not in seen:
                out_props.append(copy.deepcopy(p))
        # rebuild base with new properties
        head = [base[0], base[1]]
        rest = [x for x in base[2:] if not (isinstance(x, list) and x and x[0] == "property")]
        # insert props after common header keys
        base = head + out_props + rest
    # rename nested unit symbol names if needed
    for s in walk(base, "symbol"):
        if isinstance(s[1], str) and s[1].startswith(chain[-1][1]):
            s[1] = s[1].replace(chain[-1][1], name, 1)
    return base

def set_prop(sym: list, key: str, value: str, hide=False):
    for p in children(sym, "property"):
        if p[1] == key:
            p[2] = value
            return
    prop = ["property", key, value, ["at", 0, 0, 0], E()]
    if hide:
        prop.append(A("hide"))
        # KiCad 10 uses (hide yes)
        prop[-1] = ["hide", A("yes")]
    sym.append(prop)

def make_mosfet_symbol() -> list:
    """HL2310A-compatible: pin1=G, pin2=S, pin3=D for SOT-23."""
    name = "HL2310A"
    s = [
        "symbol",
        name,
        ["pin_names", ["offset", 1.016]],
        ["in_bom", A("yes")],
        ["on_board", A("yes")],
        ["property", "Reference", "Q", ["at", 5.08, 1.27, 0], E()],
        ["property", "Value", name, ["at", 5.08, -1.27, 0], E()],
        ["property", "Footprint", "Package_TO_SOT_SMD:SOT-23", ["at", 0, 0, 0], ["hide", A("yes")], E()],
        ["property", "Datasheet", "", ["at", 0, 0, 0], ["hide", A("yes")], E()],
        ["property", "Description", "N-ch MOSFET HL2310A SOT-23 1=G 2=S 3=D", ["at", 0, 0, 0], ["hide", A("yes")], E()],
        ["property", "LCSC", "C7420347", ["at", 0, 0, 0], ["hide", A("yes")], E()],
        ["property", "MPN", "HL2310A", ["at", 0, 0, 0], ["hide", A("yes")], E()],
    ]
    body = [
        "symbol",
        f"{name}_0_1",
        ["polyline", ["pts", ["xy", 0.254, 1.905], ["xy", 0.254, -1.905]], ["stroke", ["width", 0.254], ["type", A("default")]], ["fill", ["type", A("none")]]],
        ["polyline", ["pts", ["xy", 0.254, 0], ["xy", -2.54, 0]], ["stroke", ["width", 0], ["type", A("default")]], ["fill", ["type", A("none")]]],
        ["polyline", ["pts", ["xy", 0.762, -1.905], ["xy", 2.54, -1.905], ["xy", 2.54, 0], ["xy", 0.762, 0]], ["stroke", ["width", 0], ["type", A("default")]], ["fill", ["type", A("none")]]],
        ["polyline", ["pts", ["xy", 0.762, 1.905], ["xy", 2.54, 1.905]], ["stroke", ["width", 0], ["type", A("default")]], ["fill", ["type", A("none")]]],
    ]
    part = [
        "symbol",
        f"{name}_1_1",
        ["pin", A("input"), A("line"), ["at", -5.08, 0, 0], ["length", 2.54], ["name", "G", E()], ["number", "1", E()]],
        ["pin", A("passive"), A("line"), ["at", 2.54, -5.08, 90], ["length", 3.175], ["name", "S", E()], ["number", "2", E()]],
        ["pin", A("passive"), A("line"), ["at", 2.54, 5.08, 270], ["length", 3.175], ["name", "D", E()], ["number", "3", E()]],
    ]
    s.extend([body, part])
    return s

def make_instance(lib_id: str, ref: str, value: str, x: float, y: float, rot: int, pins: list[str], *,
                  footprint: str = "", lcsc: str = "", mpn: str = "", in_bom=True, extras=None) -> list:
    inst = [
        "symbol",
        ["lib_id", lib_id],
        ["at", x, y, rot],
        ["unit", 1],
        ["exclude_from_sim", A("no")],
        ["in_bom", A("yes") if in_bom else A("no")],
        ["on_board", A("yes")],
        ["dnp", A("no")],
        ["uuid", uid(f"inst/{ref}")],
        ["property", "Reference", ref, ["at", x, y - 7.62, 0], E()],
        ["property", "Value", value, ["at", x, y - 5.08, 0], E(1.1)],
        ["property", "Footprint", footprint, ["at", x, y, 0], ["effects", ["font", ["size", 1.1, 1.1]], ["hide", A("yes")]]],
        ["property", "Datasheet", "", ["at", x, y, 0], ["effects", ["font", ["size", 1.1, 1.1]], ["hide", A("yes")]]],
        ["property", "MPN", mpn, ["at", x, y, 0], ["effects", ["font", ["size", 1.1, 1.1]], ["hide", A("yes")]]],
        ["property", "LCSC", lcsc, ["at", x, y, 0], ["effects", ["font", ["size", 1.1, 1.1]], ["hide", A("yes")]]],
    ]
    if extras:
        for k, v in extras.items():
            inst.append(["property", k, v, ["at", x, y, 0], ["effects", ["font", ["size", 1.1, 1.1]], ["hide", A("yes")]]])
    for p in pins:
        inst.append(["pin", p, ["uuid", uid(f"pin/{ref}/{p}")]])
    inst.append(["instances", ["project", "glowcost-geiger", ["path", "/d2461aa9-a983-5642-a7cd-b477e2812911", ["reference", ref], ["unit", 1]]]])
    return inst

def label(name: str, x: float, y: float, rot: int = 0) -> list:
    return ["label", name, ["at", x, y, rot], ["effects", ["font", ["size", 1.27, 1.27]], ["justify", A("left"), A("bottom")]], ["uuid", uid(f"lbl/{name}/{x}/{y}")]]

def wire(x1, y1, x2, y2, color=None) -> list:
    w = ["wire", ["pts", ["xy", x1, y1], ["xy", x2, y2]], ["stroke", ["width", 0.1524], ["type", A("default")]]]
    if color:
        w[2].append(["color", *color])
    w.append(["uuid", uid(f"wire/{x1}/{y1}/{x2}/{y2}")])
    return w

def text_note(txt: str, x: float, y: float, size=1.27) -> list:
    return ["text", txt, ["at", x, y, 0], ["effects", ["font", ["size", size, size]], ["justify", A("left"), A("top")]], ["uuid", uid(f"txt/{x}/{y}/{txt[:20]}")]]

def rect(x1, y1, x2, y2, stroke_w=0.1524) -> list:
    return [
        "rectangle",
        ["start", x1, y1],
        ["end", x2, y2],
        ["stroke", ["width", stroke_w], ["type", A("default")], ["color", 0, 0, 0, 1]],
        ["fill", ["type", A("none")]],
        ["uuid", uid(f"rect/{x1}/{y1}/{x2}/{y2}")],
    ]

def main():
    # --- update symbol library ---
    lib = parse(SYM.read_text())
    # remove old boundary symbols if present; keep others
    keep = []
    for item in lib:
        if isinstance(item, list) and item and item[0] == "symbol" and item[1] in ("Analog_HV_boundary", "Pulse_logic_boundary"):
            continue
        keep.append(item)
    lib = keep

    # add ATtiny1616-M materialized from stock
    attiny_lib = SYMDIR / "MCU_Microchip_ATtiny.kicad_sym"
    attiny = resolve_extends(attiny_lib, "ATtiny1616-M")
    # ensure value/fields
    for p in children(attiny, "property"):
        if p[1] == "Value":
            p[2] = "ATtiny1616-MNR"
        if p[1] == "Footprint" and (not p[2] or "VQFN" in str(p[2])):
            p[2] = "Package_DFN_QFN:VQFN-20-1EP_3x3mm_P0.4mm_EP1.7x1.7mm"
    # add LCSC/MPN if missing
    prop_keys = {p[1] for p in children(attiny, "property")}
    if "LCSC" not in prop_keys:
        attiny.append(["property", "LCSC", "C507118", ["at", 0, 0, 0], ["hide", A("yes")], E()])
    if "MPN" not in prop_keys:
        attiny.append(["property", "MPN", "ATTINY1616-MNR", ["at", 0, 0, 0], ["hide", A("yes")], E()])
    # rename to Glowcost local name without path issues
    existing = {s[1] for s in children(lib, "symbol")}
    if "ATtiny1616-M" not in existing:
        lib.append(attiny)
    if "HL2310A" not in existing:
        lib.append(make_mosfet_symbol())
    # Inductor from Device
    if "L" not in existing:
        L = extract_symbol(SYMDIR / "Device.kicad_sym", "L")
        lib.append(L)
    if "R_Small_US" not in existing:
        # already in Glowcost typically
        pass

    SYM.write_text(dump(lib))
    print("Updated", SYM)

    # --- schematic ---
    sch = parse(SCH.read_text())
    # Remove U1/U2 instances
    new_sch = []
    removed = []
    for item in sch:
        if isinstance(item, list) and item and item[0] == "symbol":
            ref = None
            for p in children(item, "property"):
                if p[1] == "Reference":
                    ref = p[2]
            lib_id = child(item, "lib_id")
            lib_id_s = lib_id[1] if lib_id else ""
            if ref in ("U1", "U2") or "Analog_HV_boundary" in lib_id_s or "Pulse_logic_boundary" in lib_id_s:
                removed.append(ref or lib_id_s)
                continue
        new_sch.append(item)
    sch = new_sch
    print("Removed:", removed)

    # Rename DRIVE labels → COLLECTOR so TTL path ties to pulse node without U2
    drive_renames = 0
    for item in sch:
        if isinstance(item, list) and item and item[0] == "label" and item[1] == "DRIVE":
            item[1] = "COLLECTOR"
            drive_renames += 1
    print("DRIVE→COLLECTOR labels:", drive_renames)

    # Placement origin for new MCU block (reuse old U1 area)
    ox, oy = 70.0, 45.0

    additions = []
    # Title note
    additions.append(text_note(
        "ATtiny-only revision: MCU PWM drives boost; pulse count + I2C + ADC.\\n"
        "USART0 must use alternate TX=PA1 (PB2 is HV_PWM). Default I2C addr 0x2F.",
        ox - 10, oy - 25, 1.1))
    additions.append(rect(ox - 15, oy - 30, ox + 95, oy + 55))

    # U1 ATtiny1616
    attiny_pins = [str(i) for i in range(1, 22)]
    additions.append(make_instance(
        "Glowcost:ATtiny1616-M", "U1", "ATTINY1616-MNR / C507118",
        ox + 40, oy + 15, 0, attiny_pins,
        footprint="Package_DFN_QFN:VQFN-20-1EP_3x3mm_P0.4mm_EP1.7x1.7mm",
        lcsc="C507118", mpn="ATTINY1616-MNR",
    ))

    # Pin coordinates for ATtiny406-M style symbol (from stock layout)
    # Approximate from typical KiCad tinyAVR VQFN-20 symbol — use labels near chip with short wires
    # We'll place hierarchical-style local labels around the chip body based on known pin sides:
    # From ATtiny406-M: left PA2,PA3,GND,VCC,PA4..; right side etc.
    # Safer: place labels with net names and short stubs using documented pin positions from SVG export after first place.
    # For v1: put floating labels + wires to a connector strip of labels at known offsets.

    # Net labels around MCU (label-only wiring to existing named nets)
    mcu_labels = [
        # leftish / function
        ("COLLECTOR", ox + 10, oy + 5),   # PA2 pulse
        ("SDA", ox + 10, oy + 15),
        ("SCL", ox + 10, oy + 20),
        ("SENSE", ox + 10, oy + 25),
        ("V3V3_SENSE", ox + 10, oy + 30),
        ("HV_PWM", ox + 70, oy + 5),
        ("A0", ox + 70, oy + 12),
        ("A1", ox + 70, oy + 18),
        ("EN", ox + 70, oy + 24),  # HV_EN_IN
        ("UPDI", ox + 70, oy + 30),
        ("UART_TX", ox + 70, oy + 36),
        ("V3V3", ox + 40, oy - 5),
        ("GND", ox + 40, oy + 40),
    ]
    for n, x, y in mcu_labels:
        additions.append(label(n, x, y))

    # Explicit pin-associated labels via junction notes (text)
    additions.append(text_note(
        "U1 map: PA2=COLLECTOR PA4=SDA PA5=SCL PA6=SENSE PA7=V3V3_SENSE\\n"
        "PB0=A0 PB1=A1 PB2=HV_PWM PB3=EN PA0=UPDI PA1=UART_TX EP=GND",
        ox - 10, oy + 45, 1.0))

    # Boost: L1 + Q_HV + R_GATE near existing SW net
    bx, by = 115.0, 30.0
    additions.append(rect(bx - 10, by - 15, bx + 55, by + 25))
    additions.append(text_note("Boost (was inside U1)", bx - 8, by - 12, 1.1))
    additions.append(make_instance(
        "Glowcost:L", "L1", "1 mH / C2041861",
        bx + 10, by, 0, ["1", "2"],
        footprint="Inductor_SMD:L_1210_3225Metric",
        lcsc="C2041861", mpn="B82442T1105K050",
    ))
    additions.append(label("V3V3", bx + 10, by - 5.08))
    additions.append(label("SW", bx + 10, by + 5.08))
    additions.append(wire(bx + 10, by - 3.81, bx + 10, by - 5.08))
    additions.append(wire(bx + 10, by + 3.81, bx + 10, by + 5.08))

    additions.append(make_instance(
        "Glowcost:HL2310A", "Q3", "HL2310A / C7420347",
        bx + 35, by + 5, 0, ["1", "2", "3"],
        footprint="Package_TO_SOT_SMD:SOT-23",
        lcsc="C7420347", mpn="HL2310A",
    ))
    additions.append(make_instance(
        "Glowcost:R_Small_US", "R25", "220 R",
        bx + 22, by + 5, 0, ["1", "2"],
        footprint="glowcost:R1",  # reuse 0603-ish from project if present
        lcsc="C17577", mpn="0603WAF2200T5E",
    ))
    additions.append(label("HV_PWM", bx + 15, by + 5))
    additions.append(label("SW", bx + 35, by - 2))
    additions.append(label("GND", bx + 35, by + 12))
    additions.append(text_note("Q3:1=G 2=S 3=D  R25 gate", bx + 15, by + 18, 1.0))

    # STEMMA J4 / J5
    sx, sy = 20.0, 100.0
    additions.append(rect(sx - 5, sy - 20, sx + 80, sy + 45))
    additions.append(text_note("STEMMA QT / Qwiic (JST SH) 1=GND 2=V+ 3=SDA 4=SCL", sx, sy - 18, 1.1))
    for ref, x in (("J4", sx + 15), ("J5", sx + 50)):
        additions.append(make_instance(
            "Glowcost:Conn_01x04", ref, "SM04B-SRSS-TB / C160404",
            x, sy, 0, ["1", "2", "3", "4"],
            footprint="glowcost:J1",
            lcsc="C160404", mpn="SM04B-SRSS-TB(LF)(SN)",
        ))
        additions.append(label("GND", x - 8, sy + 2.54))
        additions.append(label("V3V3", x - 8, sy + 0))
        additions.append(label("SDA", x - 8, sy - 2.54))
        additions.append(label("SCL", x - 8, sy - 5.08))
        # wires from connector pins (Conn_01x04 pins on left at -5.08)
        additions.append(wire(x - 5.08, sy + 2.54, x - 8, sy + 2.54))
        additions.append(wire(x - 5.08, sy + 0.0, x - 8, sy + 0.0))
        additions.append(wire(x - 5.08, sy - 2.54, x - 8, sy - 2.54))
        additions.append(wire(x - 5.08, sy - 5.08, x - 8, sy - 5.08))

    # Address straps JP2/JP3
    additions.append(make_instance(
        "Glowcost:SolderJumper_2_Bridged", "JP2", "A0 open=1",
        sx + 15, sy + 30, 0, ["1", "2"],
        footprint="glowcost:SJ_LED",
    ))
    # Actually address straps should be OPEN by default — use note; bridged symbol is ok with DNP or document open
    additions.append(label("A0", sx + 5, sy + 30))
    additions.append(label("GND", sx + 25, sy + 30))
    additions.append(make_instance(
        "Glowcost:SolderJumper_2_Bridged", "JP3", "A1 open=1",
        sx + 50, sy + 30, 0, ["1", "2"],
        footprint="glowcost:SJ_LED",
    ))
    additions.append(label("A1", sx + 40, sy + 30))
    additions.append(label("GND", sx + 60, sy + 30))
    additions.append(text_note("JP2/JP3: leave OPEN for 0x2F; bridge to GND for addr bit low", sx, sy + 38, 1.0))

    # I2C pullups
    additions.append(make_instance(
        "Glowcost:R_Small_US", "R26", "4.7 kR",
        sx + 20, sy - 30, 0, ["1", "2"], footprint="glowcost:R1", lcsc="C23162", mpn="0603WAF4701T5E",
    ))
    additions.append(make_instance(
        "Glowcost:R_Small_US", "R27", "4.7 kR",
        sx + 35, sy - 30, 0, ["1", "2"], footprint="glowcost:R1", lcsc="C23162", mpn="0603WAF4701T5E",
    ))
    additions.append(label("V3V3", sx + 20, sy - 36))
    additions.append(label("SDA", sx + 20, sy - 24))
    additions.append(label("V3V3", sx + 35, sy - 36))
    additions.append(label("SCL", sx + 35, sy - 24))
    additions.append(text_note("R26/R27: populate only one bus segment", sx + 45, sy - 30, 1.0))

    # Decoupling
    additions.append(make_instance(
        "Glowcost:C", "C11", "100 nF",
        ox + 55, oy - 15, 0, ["1", "2"], footprint="glowcost:C1", lcsc="C14663", mpn="CL10B104KB8NNNC",
    ))
    additions.append(label("V3V3", ox + 55, oy - 20))
    additions.append(label("GND", ox + 55, oy - 10))

    # 3V3 sense divider (simple)
    additions.append(make_instance(
        "Glowcost:R_Small_US", "R28", "10 kR",
        ox + 75, oy - 15, 0, ["1", "2"], footprint="glowcost:R1",
    ))
    additions.append(make_instance(
        "Glowcost:R_Small_US", "R29", "10 kR",
        ox + 75, oy - 5, 0, ["1", "2"], footprint="glowcost:R1",
    ))
    additions.append(label("V3V3", ox + 75, oy - 20))
    additions.append(label("V3V3_SENSE", ox + 85, oy - 10))
    additions.append(label("GND", ox + 75, oy + 2))

    # UPDI / UART test points
    tpx, tpy = 200.0, 100.0
    additions.append(rect(tpx - 5, tpy - 15, tpx + 70, tpy + 40))
    additions.append(text_note("Programming / debug", tpx, tpy - 12, 1.1))
    for ref, net, x in (
        ("TP23", "V3V3", tpx + 10),
        ("TP24", "UPDI", tpx + 30),
        ("TP25", "GND", tpx + 50),
        ("TP28", "UART_TX", tpx + 10),
        ("TP29", "GND", tpx + 30),
    ):
        y = tpy if ref.startswith("TP2") and ref <= "TP25" else tpy + 20
        if ref in ("TP28", "TP29"):
            y = tpy + 20
        additions.append(make_instance(
            "Glowcost:TestPoint", ref, net,
            x, y, 0, ["1"], footprint="glowcost:TP1",
        ))
        additions.append(label(net, x + 5, y))

    additions.append(text_note(
        "Removed U1 Analog_HV_boundary + U2 Pulse_logic_boundary.\\n"
        "DRIVE net merged into COLLECTOR (Q1 pulse → TTL via R_OUT).",
        tpx, tpy + 35, 1.0))

    # Update title block comment if present
    for item in sch:
        if isinstance(item, list) and item and item[0] == "title_block":
            for c in children(item, "comment"):
                if len(c) >= 3 and str(c[1]) in ("1", 1) or (isinstance(c[1], list) and False):
                    pass
            # KiCad format: (comment (number "1") (value "..."))
            for c in children(item, "comment"):
                num = child(c, "number")
                val = child(c, "value")
                if num and str(num[1]) == "1" and val is not None:
                    val[1] = "ATtiny-only: MCU PWM boost + pulse/I2C; STEMMA J4/J5; no 555/MCP6562"
                if num and str(num[1]) == "2" and val is not None:
                    val[1] = "Wire U1 pins to labels in Eeschema; verify PORTMUX UART alt=PA1"

    # Append additions before sheet_instances / embedded if any
    insert_at = len(sch)
    for i, item in enumerate(sch):
        if isinstance(item, list) and item and item[0] in ("sheet_instances", "embedded_fonts", "symbol_instances"):
            insert_at = i
            break
    sch = sch[:insert_at] + additions + sch[insert_at:]

    SCH.write_text(dump(sch))
    print("Wrote", SCH)
    print("Additions", len(additions))

if __name__ == "__main__":
    main()
