#!/usr/bin/env python3
"""Semantic PCB review helper.

Deterministic code extracts board facts and generates legal trace-width and
routing candidates. Jev may rank candidates or flag semantic risk; KiCad DRC,
clearance, creepage, and fabrication rules remain authoritative.
"""
from __future__ import annotations
import json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/glowcost-geiger.kicad_pcb"
OUT = ROOT / "docs/kicad/jev-review.json"

def facts():
    text = BOARD.read_text()
    nets = sorted(set(re.findall(r'\(net\s+"([^"]+)"', text)))
    segments = len(re.findall(r'^\s*\(segment\s*$', text, re.M))
    vias = len(re.findall(r'^\s*\(via\s*$', text, re.M))
    footprints = len(re.findall(r'^\s*\(footprint\s', text, re.M))
    slots = sum(text.count(u) for u in ("e6d4d7a9-4f35-4a6c-9d81-1a1f76a3a001", "e6d4d7a9-4f35-4a6c-9d81-1a1f76a3a002"))
    return {"board":"glowcost-geiger","outline_mm":[120,32],"stackup_mm":1.6,
            "footprints":footprints,"segments":segments,"vias":vias,"hv_slots_1mm":slots,
            "net_classes":{"PI_SIGNAL":{"clearance_mm":0.2,"width_mm":0.2},
                            "LV_POWER":{"clearance_mm":0.25,"width_mm":0.3},
                            "HV_SENSE":{"clearance_mm":0.5,"width_mm":0.25},
                            "HV_SERVICE":{"clearance_mm":1.5,"width_mm":0.4}},
            "nets":nets}

def candidates():
    return {
      "PI_SIGNAL": [{"width_mm":.20,"clearance_mm":.20,"use":"SDA/SCL, raw pulse, enable"},
                    {"width_mm":.25,"clearance_mm":.25,"use":"more robust Pi wiring"}],
      "LV_POWER": [{"width_mm":.30,"clearance_mm":.25,"use":"3V3 and logic return"},
                   {"width_mm":.40,"clearance_mm":.30,"use":"higher transient margin"}],
      "HV_SENSE": [{"width_mm":.25,"clearance_mm":.50,"use":"high impedance divider"},
                   {"width_mm":.30,"clearance_mm":.75,"use":"extra contamination margin"}],
      "HV_SERVICE": [{"width_mm":.40,"clearance_mm":1.50,"use":"tube and multiplier service"},
                      {"width_mm":.50,"clearance_mm":2.00,"use":"preferred prototype margin"}]
    }

def deterministic_gate(state):
    decisions = {}
    for cls, opts in state["candidates"].items():
        required = state["facts"]["net_classes"][cls]
        legal = [o for o in opts if o["width_mm"] >= required["width_mm"] and o["clearance_mm"] >= required["clearance_mm"]]
        decisions[cls] = {"legal": legal, "selected": legal[0] if legal else None,
                          "rule": "minimum class width/clearance is deterministic"}
    decisions["hv"] = {"human_review": True, "reason":"400 V insulation and creepage cannot be delegated to Jev"}
    return decisions

def jev_rank(state):
    if not os.environ.get("TYPESAFE_API_KEY"):
        return {"available":False,"reason":"TYPESAFE_API_KEY is not set; deterministic gate retained"}
    try:
        from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
        questions = {
          "trace_choice": Choice(instructions="Choose the best legal trace option per class for a compact Geiger PCB; preserve HV margin and serviceability.", criteria=["minimum legal option","higher robustness option","review"]),
          "layout_risk": Score(instructions="Rate semantic layout risk using the supplied structured board facts; exact geometry remains outside your authority.", criteria=["poor","marginal","good","excellent"]),
          "needs_review": Noul(instructions="Should an engineer review the proposed routing choices despite passing deterministic rules?")
        }
        with TypeSafeClient() as client:
            result = client.system_one(state=state, questions=questions)
        return {"available":True,"answers":result.answers}
    except Exception as exc:
        return {"available":False,"error":type(exc).__name__,"reason":"Jev call failed; deterministic gate retained"}

def main():
    state={"facts":facts(),"candidates":candidates(),"requirements":["KiCad DRC is authoritative","HV creepage is human-reviewed","do not route through slots"]}
    report={"state":state,"deterministic":deterministic_gate(state),"jev":jev_rank(state),"policy":"Jev ranks legal candidates only; it never edits the PCB"}
    OUT.write_text(json.dumps(report,indent=2,default=str)+'\n')
    print(json.dumps({"output":str(OUT),"jev":report["jev"],"selected":report["deterministic"]},indent=2,default=str))

if __name__ == '__main__': main()
