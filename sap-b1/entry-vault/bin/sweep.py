#!/usr/bin/env python3
"""Mine every profile the vault needs, in parallel, with no model in the loop.

    sweep.py                 # everything, priority order
    sweep.py --jobs 6
    sweep.py --only profile

Writing the notes needs a model. Measuring the books does not — it is SQL, and it is
the part that takes hours. So this runs the whole measurement sweep on its own and
parks the results in _data/, where a note-writer (model or human) picks them up.
Restartable: anything already written is skipped.
"""
from __future__ import annotations
import argparse, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import DOCS, ROOT

DATA = os.path.join(HERE, "..", "_data")

# Header tables in the order the vault needs them, with the line tables that matter.
PRIORITY = [
    "OPCH", "OPDN", "ORPC", "OVPM", "ORCT", "OINV", "ORIN", "OJDT", "ODRF", "OPDF",
    "OPOR", "OBTF", "OWTR", "OWTQ", "OIGN", "OIGE", "OWOR", "ODLN", "ORDR", "ORDN",
    "ORPD", "OIPF", "OMRV", "OBNK", "OQUT", "ORRR",
]
# Master and setup tables the foundation notes are built on.
MASTERS = ["OACT", "NNM1", "OBPL", "OCRD", "OCRG", "OITM", "OPRC", "ODIM", "OWHS",
           "OWHT", "OUSR", "OFPR", "OCST", "OSLP", "OBGT", "OACP", "OITR", "OWDD",
           "OWDR", "OATC", "CUFD", "OCTG"]
# Line tables worth their own profile (the ones a person types into).
LINES = ["PCH1", "PCH12", "PDN1", "RPC1", "VPM2", "VPM1", "VPM4", "RCT2", "RCT1",
         "INV1", "INV12", "RIN1", "JDT1", "DRF1", "POR1", "BTF1", "WTR1", "IGN1",
         "IGE1", "WOR1", "DLN1", "RDR1", "RDN1", "IPF1", "ATC1", "ITR1"]

TT = {"OPCH": 18, "OPDN": 20, "ORPC": 19, "OVPM": 46, "ORCT": 24, "OINV": 13,
      "ORIN": 14, "OJDT": 30, "OWTR": 67, "OIGN": 59, "OIGE": 60, "OWOR": 202,
      "ODLN": 15, "ORDN": 16, "ORPD": 21, "OIPF": 69, "OMRV": 162, "ORDR": 17}


def jobs(only):
    J = []
    def add(kind, name, cmd, out):
        if only and only != kind:
            return
        J.append((kind, name, cmd, out))

    for t in PRIORITY:
        add("profile", f"profile {t}",
            ["profile.py", t, "--co", "OIL,MART,BEV", "--days", "120", "--vocab-max", "30"],
            f"profile-{t}.md")
    for t in LINES:
        add("profile", f"profile {t}",
            ["profile.py", t, "--co", "OIL,MART,BEV", "--days", "120", "--vocab-max", "30"],
            f"profile-{t}.md")
    for t in MASTERS:
        add("profile", f"profile {t}",
            ["profile.py", t, "--co", "OIL,MART,BEV", "--days", "3650", "--vocab-max", "40"],
            f"profile-{t}.md")
    for t, tt in TT.items():
        for co in ("OIL", "MART", "BEV"):
            add("gl", f"gl {tt} {co}",
                ["gl.py", str(tt), "--co", co, "--days", "365", "--memo"],
                f"gl-{tt}-{co}.md")
    add("gl", "gl -3 OIL", ["gl.py", "-3", "--co", "OIL", "--days", "3650", "--memo"], "gl--3-OIL.md")
    add("gl", "gl 321 OIL", ["gl.py", "321", "--co", "OIL", "--days", "3650", "--memo"], "gl-321-OIL.md")
    for t in PRIORITY:
        for co in ("OIL", "MART", "BEV"):
            add("flow", f"flow {t} {co}", ["flow.py", t, "--co", co, "--days", "365"],
                f"flow-{t}-{co}.md")
    for t in PRIORITY:
        add("sample", f"sample {t}", ["sample.py", t, "--n", "2", "--co", "OIL"], f"sample-{t}-OIL.md")
    return J


def run(kind, name, cmd, out, force):
    dest = os.path.join(DATA, out)
    if not force and os.path.exists(dest) and os.path.getsize(dest) > 400:
        return name, "skip", 0
    t0 = time.time()
    full = [sys.executable, os.path.join(HERE, cmd[0])] + cmd[1:] + ["--out", dest]
    p = subprocess.run(full, capture_output=True, text=True, cwd=ROOT, timeout=2400)
    dt = time.time() - t0
    if p.returncode != 0:
        # keep the reason next to the data so a note-writer sees the gap, not a silence
        open(dest + ".error", "w").write((p.stderr or p.stdout)[-3000:])
        return name, "FAIL", dt
    return name, "ok", dt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=5)
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    J = jobs(a.only)
    print(f"{len(J)} jobs, {a.jobs} workers", flush=True)
    done = fail = skip = 0
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        futs = {ex.submit(run, *j, a.force): j for j in J}
        for i, f in enumerate(as_completed(futs), 1):
            try:
                name, st, dt = f.result()
            except Exception as e:
                name, st, dt = str(futs[f][1]), f"EXC {e}"[:120], 0
            if st == "ok":
                done += 1
            elif st == "skip":
                skip += 1
            else:
                fail += 1
            print(f"[{i}/{len(J)}] {st:5} {dt:5.1f}s  {name}", flush=True)
    print(f"\ndone={done} skipped={skip} failed={fail}", flush=True)


if __name__ == "__main__":
    main()
