#!/usr/bin/env python3
"""calibrate_august.py — re-measures the August backtest and pins it, with its provenance.

The site's one trust sentence is "the same plan was run for August and came this
close to what the factory really made". Until 2026-09-06 gen_live.py read that
number out of `sim/summary.json`, which is a WORKING FILE: the default
`python3 engine/august_sim.py` overwrites it. So the claim drifted silently —
the committed summary said 2,122,639 L while the committed engine, run on the
committed inputs, made 2,124,866 L. Nothing failed, because nothing looked.

This script makes the claim an artefact instead of a side effect:

    cd jolly && python3 engine/calibrate_august.py        # rewrites the artefact
    cd jolly && python3 engine/calibrate_august.py --check # exit 1 if it is stale

It runs the August replay under its own SIM_TAG (so no working file is touched),
records what came out, and stamps it with the sha256 of every file the answer
depends on. gen_live.py reads the artefact and compares those hashes to the tree:
matching, it publishes the number as measured; not matching, it publishes it
with `reproducible: false` and a warning that says which file moved. A bare
re-run of the engine can no longer move the site's credibility number, and an
engine change that WOULD move it can no longer pass unnoticed.

Stdlib only. Reads no business system: the August inputs are frozen in sim/.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
JOLLY = os.path.dirname(HERE)
ARTEFACT = os.path.join(JOLLY, "reference", "august-calibration.json")
TAG = "-calibration"
INPUTS = "sim/sim-inputs.json"

# Everything the replay's answer depends on. A change to any one of these can move
# the number, so each one is hashed into the artefact.
DEPENDS_ON = ["engine/august_sim.py", "engine/plan_units.py", "engine/plan_explode.py", INPUTS]


def sha256(rel):
    with open(os.path.join(JOLLY, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def fingerprint():
    return {rel: sha256(rel) for rel in DEPENDS_ON}


def replay():
    """Run the August sim under our own tag and return (totals, shift). The scratch
    outputs are removed afterwards — this script owns no plan artefact.

    EVERY SIM_ VARIABLE IS DROPPED, not the two that were thought of. The child used to
    inherit `dict(os.environ, …)` with SIM_HOURS and SIM_SUNDAYS_OFF popped, and
    august_sim.py reads a THIRD one — SIM_HOURS_SCHEDULE — so a taper exported in the
    shell would silently pin the site's trust number to a schedule August never ran, and
    `--check` would then bless it, because --check compares file hashes and knows nothing
    about the environment the measurement was taken in. The shift the replay actually ran
    under goes into the artefact for the same reason: so it is readable afterwards."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("SIM_")}
    env["SIM_INPUTS"], env["SIM_TAG"] = INPUTS, TAG
    r = subprocess.run([sys.executable, "engine/august_sim.py"], cwd=JOLLY, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        sys.stderr.write(r.stderr.decode("utf-8", "replace"))
        raise SystemExit(f"calibrate_august.py: the August replay failed (rc={r.returncode})")
    with open(os.path.join(JOLLY, f"sim/summary{TAG}.json"), encoding="utf-8") as fh:
        summary = json.load(fh)
    totals, shift = summary["totals"], summary.get("shift") or {}
    for path in (f"sim/summary{TAG}.json", f"sim/events{TAG}.json"):
        p = os.path.join(JOLLY, path)
        if os.path.exists(p):
            os.remove(p)
    shutil.rmtree(os.path.join(JOLLY, f"sim/days{TAG}"), ignore_errors=True)
    return totals, shift


def build():
    totals, shift = replay()
    made, actual = totals["made_l"], totals["actual_made_l"]
    return {
        "id": "august-calibration",
        "measured_on": date.today().isoformat(),
        "sim_made_l": made,
        # The RUPEES the same replay made. A change that keeps the litres and moves the
        # SKU mix passes a litres-only pin, and the mix is what the money page is built
        # from — so the backtest pins both (WS2 asked for made_l AND value).
        "sim_value": totals["value"],
        "actual_made_l": actual,
        "delta_pct": round(abs(made - actual) / max(actual, 1) * 100, 2),
        # What the replay's shift actually was. The hashes say the engine and the inputs
        # have not moved; this says the ENVIRONMENT had not moved either.
        "shift": shift,
        "how": f"SIM_INPUTS={INPUTS} SIM_TAG={TAG} python3 engine/august_sim.py",
        "what_it_means": ("the same engine, standing on 1 August knowing nothing later, "
                          "against what the factory really made that month"),
        "actual_source": "out/august-actuals-SCORING.csv (ji.jivo.in run records)",
        "depends_on": fingerprint(),
        "rebuild_with": "python3 engine/calibrate_august.py",
        "note": ("Pinned because sim/summary.json is a working file that any bare "
                 "`python3 engine/august_sim.py` overwrites. Before 2026-09-06 the site "
                 "read the claim from there and it had drifted to 2,122,639 L / 0.16% "
                 "against an engine that made 2,124,866 L / 0.27%."),
    }


def stale(art):
    """[(file, recorded, now)] for every dependency whose hash has moved."""
    return [(rel, was, sha256(rel)) for rel, was in (art.get("depends_on") or {}).items()
            if os.path.exists(os.path.join(JOLLY, rel)) and sha256(rel) != was]


def main(argv):
    if "--check" in argv:
        if not os.path.exists(ARTEFACT):
            print(f"august-calibration.json is not there — run: python3 engine/calibrate_august.py")
            return 1
        with open(ARTEFACT, encoding="utf-8") as fh:
            art = json.load(fh)
        moved = stale(art)
        for rel, was, now in moved:
            print(f"STALE: {rel} is {now[:12]}, the calibration was measured against {was[:12]}")
        print("august calibration: " + ("STALE — re-measure it" if moved else
                                        f"{art['sim_made_l']:,} L vs {art['actual_made_l']:,} L "
                                        f"({art['delta_pct']}%), Rs {art.get('sim_value', 0):,}, "
                                        f"reproducible"))
        return 1 if moved else 0
    art = build()
    with open(ARTEFACT, "w", encoding="utf-8") as fh:
        json.dump(art, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(f"wrote reference/august-calibration.json — plan {art['sim_made_l']:,} L "
          f"/ Rs {art['sim_value']:,} vs actual {art['actual_made_l']:,} L "
          f"({art['delta_pct']}%), shift {art['shift']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
