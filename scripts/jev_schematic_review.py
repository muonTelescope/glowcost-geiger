#!/usr/bin/env python3
"""Semantic schematic-layout decision helper for gLowCost-geiger.

Deterministic code extracts sheet facts + ERC summary and enumerates legal
layout policies. Jev ranks those policies; this script never edits the .kicad_sch.
Apply winners in a separate pass, then verify with SVG/netlist/ERC.
"""
from __future__ import annotations
import json, os, re, sys
from pathlib import Path
from collections import Counter

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("LANG", "C.UTF-8")
os.environ.setdefault("LC_ALL", "C.UTF-8")

ROOT = Path(__file__).resolve().parents[1]
SCH = ROOT / "kicad/glowcost-geiger.kicad_sch"
ERC = ROOT / "build/kicad/attiny-erc.rpt"
OUT = ROOT / "docs/kicad/jev-schematic-review.json"


def parse_refs(text: str) -> dict[str, str]:
    """Return {ref: lib_id} for top-level symbol instances (heuristic)."""
    refs = {}
    # Split roughly on "(symbol" that have lib_id + Reference property nearby
    for m in re.finditer(
        r'\(symbol\s+\(lib_id\s+"([^"]+)"\).*?\(property\s+"Reference"\s+"([^"]+)"',
        text,
        re.S,
    ):
        lib, ref = m.group(1), m.group(2)
        if ref.startswith("#"):
            continue
        refs[ref] = lib
    return refs


def erc_summary(path: Path) -> dict:
    if not path.exists():
        return {"missing": True}
    t = path.read_text(errors="replace")
    types = Counter(re.findall(r"^\[([^\]]+)\]", t, re.M))
    m = re.search(r"ERC messages:\s*(\d+)\s+Errors\s+(\d+)\s+Warnings\s+(\d+)", t)
    return {
        "messages": int(m.group(1)) if m else sum(types.values()),
        "errors": int(m.group(2)) if m else None,
        "warnings": int(m.group(3)) if m else None,
        "by_type": dict(types),
    }


def facts() -> dict:
    text = SCH.read_text(errors="replace")
    refs = parse_refs(text)
    labels = sorted(set(re.findall(r'\(label\s+"([^"]+)"', text)))
    blocks = {
        "mcu": sorted(r for r in refs if r == "U1" or r.startswith("TP2")),
        "boost": sorted(r for r in refs if r in {"L1", "Q3", "R25", "C11", "R28", "R29"}),
        "stemma": sorted(r for r in refs if r in {"J4", "J5", "JP2", "JP3", "R26", "R27"}),
        "pi": sorted(r for r in refs if r == "J1"),
        "hv_front": sorted(
            r
            for r in refs
            if r.startswith(("R_", "C_", "D_", "Q1", "Q2", "J2", "J3"))
            or r in {"GM1"}
            or re.match(r"R\d+$", r)
            or re.match(r"C\d+$", r)
        ),
    }
    return {
        "board": "gLowCost-geiger",
        "goal": "clean, correct, easy-to-read single-sheet schematic after ATtiny-only rewrite",
        "constraints": [
            "preserve nets HV_PWM->R25->GATE->Q3, SW=L1+Q3.D+C1, STEMMA pinout 1=GND 2=V+ 3=SDA 4=SCL",
            "PA1 = UART TX alternate (PB2 is HV_PWM)",
            "do not change electrical connectivity without netlist proof",
            "Jev ranks policies only; never edits the schematic file",
            "HV creepage/clearance remains human-reviewed",
        ],
        "symbol_count": len(refs),
        "refs_sample": sorted(refs)[:40],
        "has_attiny": any("ATtiny" in v or "ATTINY" in v.upper() for v in refs.values())
        or "U1" in refs,
        "labels_count": len(labels),
        "key_labels_present": [
            n
            for n in [
                "HV_PWM",
                "GATE",
                "SW",
                "SDA",
                "SCL",
                "COLLECTOR",
                "SENSE",
                "V3V3",
                "GND",
            ]
            if n in labels
        ],
        "blocks": blocks,
        "erc": erc_summary(ERC),
        "known_warnings": [
            "endpoint_off_grid on many legacy pins",
            "unconnected_wire_endpoint stubs",
            "footprint_link_issues for Package_DFN_QFN / Inductor_SMD / Package_TO_SOT_SMD not in project fp-lib-table",
        ],
    }


def candidates() -> dict:
    return {
        "block_layout": [
            {
                "id": "left_to_right",
                "summary": "STEMMA+MCU left, boost top-center, HV ladder right, Pi header bottom-right",
                "why": "signal flow pulse/I2C left; power conversion center; HV kept visually separate",
            },
            {
                "id": "power_top_signal_bottom",
                "summary": "All power/boost on top rail; digital/STEMMA mid; HV sensing bottom",
                "why": "classic power-top readability; longer vertical runs for HV sense",
            },
            {
                "id": "compact_quadrants",
                "summary": "Four tight quadrants with short label stubs; minimize sheet whitespace",
                "why": "fits denser review screenshots; risk of overlapping properties",
            },
        ],
        "wiring_style": [
            {
                "id": "labels_for_long_nets",
                "summary": "Local wires for pullups/decap next to IC; net labels for cross-block nets",
                "why": "matches KiCad schematic skill; keeps MCU pins readable",
            },
            {
                "id": "wires_everywhere",
                "summary": "Draw continuous wires between blocks; labels only at TPs",
                "why": "maximum visual continuity; sheet gets busy on ATtiny pin farm",
            },
            {
                "id": "power_symbols_plus_labels",
                "summary": "Use +3V3/GND power symbols at sources; labels for signal nets only",
                "why": "power polarity obvious; fewer V3V3/GND label collisions",
            },
        ],
        "probe_policy": [
            {
                "id": "cluster_edge",
                "summary": "Keep all TPs but cluster them on a dedicated probe strip at sheet edge",
                "why": "debug remains easy; declutter main blocks",
            },
            {
                "id": "keep_near_nets",
                "summary": "Keep TPs adjacent to their nets (current style) but hide unused probe labels",
                "why": "minimal churn; still noisy visually",
            },
            {
                "id": "minimize_probes",
                "summary": "Keep only UPDI/UART/V3V3/GND/SW/SENSE/COLLECTOR TPs; drop multiplier mid-node probes",
                "why": "cleanest read; less bring-up convenience",
            },
        ],
    }


def deterministic_gate(state: dict) -> dict:
    """Default picks when Jev unavailable — prefer readability + skill defaults."""
    return {
        "block_layout": {
            "selected": "left_to_right",
            "rule": "default signal-flow left-to-right for mixed HV/digital sheet",
        },
        "wiring_style": {
            "selected": "power_symbols_plus_labels",
            "rule": "KiCad skill: power symbols for rails; labels for cross-block signals; short wires for passives",
        },
        "probe_policy": {
            "selected": "cluster_edge",
            "rule": "declutter without deleting bring-up coverage",
        },
        "apply_order": [
            "block_layout",
            "wiring_style",
            "probe_policy",
            "re-export SVG",
            "netlist diff vs pre-tidy",
            "ERC must stay 0 errors",
        ],
    }


def jev_rank(state: dict) -> dict:
    if not os.environ.get("TYPESAFE_API_KEY"):
        return {"available": False, "reason": "TYPESAFE_API_KEY is not set; deterministic gate retained"}
    try:
        from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

        questions = {
            "block_layout": Choice(
                instructions=(
                    "Pick the best high-level block placement policy for a single-sheet "
                    "Geiger counter schematic that mixes 3.3V MCU/STEMMA with a HV boost "
                    "and CW multiplier. Prioritize easy reading and correct mental model "
                    "of signal/power flow. Electrical nets are already correct."
                ),
                criteria={
                    "left_to_right": state["candidates"]["block_layout"][0]["summary"]
                    + " — "
                    + state["candidates"]["block_layout"][0]["why"],
                    "power_top_signal_bottom": state["candidates"]["block_layout"][1]["summary"]
                    + " — "
                    + state["candidates"]["block_layout"][1]["why"],
                    "compact_quadrants": state["candidates"]["block_layout"][2]["summary"]
                    + " — "
                    + state["candidates"]["block_layout"][2]["why"],
                },
            ),
            "wiring_style": Choice(
                instructions=(
                    "Pick the wiring/labeling policy that maximizes readability for an "
                    "ATtiny1616 pin-heavy sheet without risking net mistakes."
                ),
                criteria={
                    "labels_for_long_nets": state["candidates"]["wiring_style"][0]["summary"]
                    + " — "
                    + state["candidates"]["wiring_style"][0]["why"],
                    "wires_everywhere": state["candidates"]["wiring_style"][1]["summary"]
                    + " — "
                    + state["candidates"]["wiring_style"][1]["why"],
                    "power_symbols_plus_labels": state["candidates"]["wiring_style"][2]["summary"]
                    + " — "
                    + state["candidates"]["wiring_style"][2]["why"],
                },
            ),
            "probe_policy": Choice(
                instructions=(
                    "Pick how aggressively to declutter test points on this prototype sheet."
                ),
                criteria={
                    "cluster_edge": state["candidates"]["probe_policy"][0]["summary"]
                    + " — "
                    + state["candidates"]["probe_policy"][0]["why"],
                    "keep_near_nets": state["candidates"]["probe_policy"][1]["summary"]
                    + " — "
                    + state["candidates"]["probe_policy"][1]["why"],
                    "minimize_probes": state["candidates"]["probe_policy"][2]["summary"]
                    + " — "
                    + state["candidates"]["probe_policy"][2]["why"],
                },
            ),
            "readability": Score(
                instructions=(
                    "Rate expected readability after applying the chosen policies to the "
                    "current ATtiny-only sheet (ERC errors already 0)."
                ),
                criteria=["poor", "marginal", "good", "excellent"],
            ),
            "needs_human_pass": Noul(
                instructions=(
                    "After applying these policies, should an engineer still do a visual "
                    "pass in Eeschema before PCB placement?"
                )
            ),
        }
        with TypeSafeClient() as client:
            result = client.system_one(state=state, questions=questions)
        # answers may be objects — normalize
        answers = {}
        raw = result.answers
        if isinstance(raw, dict):
            for k, v in raw.items():
                if hasattr(v, "model_dump"):
                    answers[k] = v.model_dump()
                elif hasattr(v, "dict"):
                    answers[k] = v.dict()
                else:
                    answers[k] = getattr(v, "__dict__", str(v))
                    # choice objects often have .choice
                    if hasattr(v, "choice"):
                        answers[k] = {
                            "type": "choice",
                            "choice": v.choice,
                            "confidence": getattr(v, "confidence", None),
                            "probabilities": getattr(v, "probabilities", None),
                        }
                    elif hasattr(v, "score"):
                        answers[k] = {
                            "type": "score",
                            "score": v.score,
                            "confidence": getattr(v, "confidence", None),
                            "legend": getattr(v, "legend", None),
                        }
                    elif hasattr(v, "noul"):
                        answers[k] = {
                            "type": "noul",
                            "noul": v.noul,
                        }
        return {"available": True, "answers": answers}
    except Exception as exc:
        detail = str(exc)
        response = getattr(exc, "response", None)
        if response is not None:
            try:
                detail = response.text or detail
            except Exception:
                pass
        return {
            "available": False,
            "error": type(exc).__name__,
            "reason": "Jev call failed; deterministic gate retained",
            "detail": detail[:1000],
        }


def merge_selected(deterministic: dict, jev: dict) -> dict:
    selected = {k: v["selected"] for k, v in deterministic.items() if isinstance(v, dict) and "selected" in v}
    if jev.get("available") and isinstance(jev.get("answers"), dict):
        for key in ("block_layout", "wiring_style", "probe_policy"):
            ans = jev["answers"].get(key)
            if isinstance(ans, dict) and ans.get("choice"):
                selected[key] = ans["choice"]
    return selected


def main() -> None:
    state = {
        "facts": facts(),
        "candidates": candidates(),
        "requirements": [
            "Preserve electrical connectivity; prove with netlist",
            "ERC errors must remain 0",
            "Iterate with SVG screenshots after applying winners",
            "Jev never edits files",
        ],
    }
    det = deterministic_gate(state)
    jev = jev_rank(state)
    report = {
        "state": state,
        "deterministic": det,
        "jev": jev,
        "selected": merge_selected(det, jev),
        "policy": "Jev ranks schematic layout policies only; it never edits the schematic",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(json.dumps({"output": str(OUT), "selected": report["selected"], "jev": jev}, indent=2, default=str))


if __name__ == "__main__":
    main()
