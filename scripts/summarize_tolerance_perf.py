#!/usr/bin/env python3
import csv
import glob
import os
import re
import statistics as st
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "results", "tolerance", "perf")
DADOS = os.path.join(ROOT, "apresentacao", "dados")

ALGS = ["quicksort", "mergesort", "shellsort", "heapsort"]
DELTAS = [3, 5, 7, 11]

NAME_RE = re.compile(r"^(?P<algo>.+?)-d(?P<delta>\d+)_(?P<mode>serial|parallel)_"
                     r"(?P<input>\d+)\.in_t(?P<threads>\d+)_run(?P<run>\d+)$")
EVENTS = ["instructions", "cycles", "branches", "branch-misses", "cache-references",
          "cache-misses", "L1-dcache-load-misses", "LLC-load-misses",
          "dTLB-load-misses", "iTLB-load-misses"]


def num(s):
    return float(s.replace(".", "").replace(",", "."))


def parse(path):
    txt = open(path, encoding="utf-8").read()
    out = {}
    for ev in EVENTS:
        m = re.search(rf"^\s*([\d.,]+)\s+{re.escape(ev)}(?::u)?\s", txt, re.M)
        if m:
            out[ev] = num(m.group(1))
    m = re.search(r"^\s*([\d.,]+)\s+Joules\s+power/energy-pkg/", txt, re.M)
    if m:
        out["energy_pkg"] = num(m.group(1))
    m = re.search(r"^\s*([\d.,]+)\s+seconds time elapsed", txt, re.M)
    if m:
        out["time"] = num(m.group(1))
    return out


def main():
    runs = defaultdict(dict)
    for path in glob.glob(os.path.join(WORK, "results", "*.p[123]")):
        stem, ext = os.path.splitext(os.path.basename(path))
        m = NAME_RE.match(stem)
        if not m:
            continue
        key = (m["algo"], int(m["delta"]), m["mode"], int(m["threads"]), int(m["run"]))
        vals = parse(path)
        rec = runs[key]
        if ext == ".p3":
            rec["energy_pkg"] = vals.get("energy_pkg")
        else:
            rec.setdefault("_times", []).append(vals.pop("time"))
            for k, v in vals.items():
                rec.setdefault(k, v)

    rows = []
    for (algo, delta, mode, threads, run), rec in sorted(runs.items()):
        rows.append({"algorithm": algo, "delta": delta, "variant": mode, "threads": threads,
                     "run": run, "time": st.mean(rec.pop("_times")), **rec})
    fields = ["algorithm", "delta", "variant", "threads", "run", "time", "energy_pkg", *EVENTS]
    with open(os.path.join(WORK, "tolerance_perf_raw.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    groups = defaultdict(list)
    for r in rows:
        groups[(r["algorithm"], r["delta"], r["variant"])].append(r)

    metrics = ["time", "energy_pkg", "instructions", "cycles", "branch-misses", "cache-misses"]
    summary = []
    for (algo, delta, mode), rs in sorted(groups.items()):
        s = {"algorithm": algo, "delta": delta, "variant": mode, "runs": len(rs)}
        for k in metrics:
            vals = [r[k] for r in rs if r.get(k) is not None]
            s[k] = st.median(vals) if vals else None
        ts = [r["time"] for r in rs]
        s["time_cv_pct"] = st.stdev(ts) / st.mean(ts) * 100
        summary.append(s)
    with open(os.path.join(WORK, "tolerance_perf_summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)

    med = {(s["algorithm"], s["delta"], s["variant"]): s for s in summary}
    os.makedirs(DADOS, exist_ok=True)
    for metric in metrics:
        for mode in ["serial", "parallel"]:
            path = os.path.join(DADOS, f"perf_{metric.replace('-', '_')}_{mode}.dat")
            with open(path, "w") as f:
                f.write("delta " + " ".join(ALGS) + "\n")
                for d in DELTAS:
                    vals = []
                    for a in ALGS:
                        base, cur = med[(a, 0, mode)][metric], med[(a, d, mode)][metric]
                        vals.append(f"{(cur / base - 1) * 100:.1f}")
                    f.write(f"{d} " + " ".join(vals) + "\n")

    print(f"[INFO] {len(rows)} execucoes, {len(summary)} configuracoes")


if __name__ == "__main__":
    main()
