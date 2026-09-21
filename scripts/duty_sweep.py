#!/usr/bin/env python3
"""Open-loop HV versus MCU PWM duty for the ATtiny boost model.

The stock deck holds the gate off once the behavioral OVP divider crosses
1.242 V, so a fixed 20% on-time cannot show what duty actually controls.
This sweep turns that gate term off (the board has no comparator) and holds
EN high. A few clamp-on points show where that behavioral limiter sits.
"""
from __future__ import annotations

import csv
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/geiger-duty-matplotlib")
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / "sim/hv/converter.cir").read_text()
OUT = ROOT / "docs/sim"
BUILD = ROOT / "build/hv-duty"
OUT.mkdir(parents=True, exist_ok=True)

# Firmware TCA0: 20 MHz / 2000 = 10 kHz, CMP2 steps of 1. Cap in main.c is 20%.
DUTY_PCT = (1, 2, 4, 6, 8, 10, 12, 15, 20, 30)
CLAMP_DUTY_PCT = (8, 12, 20)
PLANT_DUTY_PCT = (8, 12, 15, 20)
VBAT = 3.3
ILOAD = 1e-6
FET_VDS_MAX = 60.0  # HL2310A / C7420347


def deck_for(duty_pct: float, clamp: bool, plant: bool = False) -> str:
    """clamp keeps both gate cuts. plant removes the sense switch and the OVP term."""
    ton = duty_pct / 100.0 / 10000.0
    deck = BASE
    deck = re.sub(r"\bVBAT=\S+", f"VBAT={VBAT:g}", deck, count=1)
    deck = re.sub(r"\bILOAD=\S+", f"ILOAD={ILOAD:g}", deck, count=1)
    deck = re.sub(r"\bTON=\S+", f"TON={ton:.8g}", deck, count=1)
    if plant or not clamp:
        deck = deck.replace(
            "Bgate gate 0 V={v(clock)*(v(delayed)>0.5)*(v(en)>2)*(v(ovp)<1.242)}",
            "Bgate gate 0 V={v(clock)*(v(delayed)>0.5)*(v(en)>2)}",
        )
    if plant:
        deck = deck.replace("Sinhibit enable 0 sense 0 HYST OFF\n", "")
    deck = deck.replace("PULSE(0 3.3 5m 1u 1u 195m 500m)", "DC 3.3")
    deck = deck.replace(
        "Bevent anode cathode I={20u*v(event)*max(0,min(1,v(hv)/360))}",
        "Bevent anode cathode I=0",
    )
    deck = deck.replace(
        """.control
set wr_singlescale
set wr_vecnames
tran 10u 0.3 0 2u uic
wrdata metrics.txt v(hv) v(sw) i(L1) i(Vbat) v(en) v(ttl) v(cathode) v(anode) v(gate) v(ovp) v(base) v(collector)
linearize v(hv) v(sw) i(L1) i(Vbat) v(en) v(ttl) v(cathode) v(anode) v(gate) v(ovp) v(base) v(collector)
wrdata wave.txt v(hv) v(sw) i(L1) i(Vbat) v(en) v(ttl) v(cathode) v(anode) v(gate) v(ovp) v(base) v(collector)
quit
.endc""",
        """.control
tran 10u 0.4 0 2u uic
meas tran hv_early AVG v(hv) from=0.20 to=0.24
meas tran hv_late AVG v(hv) from=0.34 to=0.39
meas tran hv_min MIN v(hv) from=0.34 to=0.39
meas tran hv_max MAX v(hv) from=0.34 to=0.39
meas tran sw_pk MAX v(sw) from=0.05 to=0.39
meas tran il_pk MAX i(L1) from=0.05 to=0.39
meas tran iin AVG i(Vbat) from=0.34 to=0.39
meas tran sense_avg AVG v(sense) from=0.34 to=0.39
quit
.endc""",
    )
    return deck


def parse_meas(log: str, name: str) -> float:
    match = re.search(rf"^{name}\s*=\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)", log, re.I | re.M)
    if not match:
        raise RuntimeError(f"missing {name}\n{log[-1500:]}")
    return float(match.group(1))


def run_case(duty_pct: float, clamp: bool, plant: bool = False) -> dict:
    name = f"{'plant' if plant else 'clamp' if clamp else 'sense'}_d{duty_pct:g}"
    work = BUILD / name
    work.mkdir(parents=True, exist_ok=True)
    (work / "converter.cir").write_text(deck_for(duty_pct, clamp, plant))
    proc = subprocess.run(
        ["ngspice", "-b", "-o", "run.log", "converter.cir"],
        cwd=work,
        check=True,
        stdout=subprocess.DEVNULL,
        timeout=240,
    )
    del proc
    log = (work / "run.log").read_text(errors="replace")
    lowered = log.lower()
    if "timestep too small" in lowered or "fatal error" in lowered:
        raise RuntimeError(f"{name}: {log[-1500:]}")
    early = parse_meas(log, "hv_early")
    late = parse_meas(log, "hv_late")
    row = {
        "case": name,
        "clamp": clamp and not plant,
        "plant": plant,
        "duty_pct": duty_pct,
        "cmp2_counts": round(duty_pct / 100.0 * 2000),
        "hv_mean_V": late,
        "hv_min_V": parse_meas(log, "hv_min"),
        "hv_max_V": parse_meas(log, "hv_max"),
        "hv_early_V": early,
        "settled": abs(late - early) < max(2.0, 0.01 * abs(late)),
        "peak_switch_V": parse_meas(log, "sw_pk"),
        "peak_inductor_mA": parse_meas(log, "il_pk") * 1e3,
        "input_mA": -parse_meas(log, "iin") * 1e3,
        "sense_V": parse_meas(log, "sense_avg"),
        "fet_within_60V": parse_meas(log, "sw_pk") <= FET_VDS_MAX,
    }
    print(name, {k: row[k] for k in ("hv_mean_V", "peak_switch_V", "peak_inductor_mA", "settled")}, flush=True)
    return row


def main() -> None:
    jobs = (
        [(d, False, False) for d in DUTY_PCT]
        + [(d, True, False) for d in CLAMP_DUTY_PCT]
        + [(d, False, True) for d in PLANT_DUTY_PCT]
    )
    rows = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(run_case, duty, clamp, plant) for duty, clamp, plant in jobs]
        for fut in as_completed(futures):
            rows.append(fut.result())
    rows.sort(key=lambda r: (r["plant"], r["clamp"], r["duty_pct"]))
    fields = list(rows[0])
    with (OUT / "duty-sweep.csv").open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.18,
        "figure.facecolor": "#f8fafc",
        "axes.facecolor": "#f8fafc",
        "savefig.facecolor": "#f8fafc",
    })
    sense_rows = [r for r in rows if not r.get("plant") and not r["clamp"]]
    plant_rows = [r for r in rows if r.get("plant")]
    fig, ax = plt.subplots(2, 1, figsize=(10, 7), layout="constrained")
    if plant_rows:
        ax[0].plot([r["duty_pct"] for r in plant_rows], [r["hv_mean_V"] for r in plant_rows], "-o", label="PWM only (sense clamp removed)")
    ax[0].plot([r["duty_pct"] for r in sense_rows], [r["hv_mean_V"] for r in sense_rows], "-s", label="Sense comparator holds the gate")
    ax[0].axvspan(1, 20, color="green", alpha=0.08, label="Firmware uses 1–20%")
    ax[0].axhline(440, color="red", ls="--", label="440 V model ceiling")
    ax[0].set(xlabel="PWM duty (%)", ylabel="HV (V)", title="3.3 V, 1 µA · 340–390 ms mean")
    ax[0].legend()
    ax[1].plot([r["duty_pct"] for r in sense_rows], [r["peak_switch_V"] for r in sense_rows], "-s", label="With sense clamp")
    if plant_rows:
        ax[1].plot([r["duty_pct"] for r in plant_rows], [r["peak_switch_V"] for r in plant_rows], "-o", label="PWM only")
    ax[1].axhline(FET_VDS_MAX, color="red", ls="--", label="HL2310A 60 V")
    ax[1].set(xlabel="PWM duty (%)", ylabel="Switch node peak (V)", title="Q3 drain stress versus duty")
    ax[1].legend()
    fig.savefig(OUT / "duty-sweep.png", dpi=180, bbox_inches="tight")
    fig.savefig(OUT / "duty-sweep.svg", bbox_inches="tight")
    plt.close(fig)
    svg = OUT / "duty-sweep.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    image = ROOT / "docs/images/sim-duty-sweep.png"
    image.write_bytes((OUT / "duty-sweep.png").read_bytes())
    print("wrote", OUT / "duty-sweep.csv")


if __name__ == "__main__":
    main()
