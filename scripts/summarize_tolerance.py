#!/usr/bin/env python3
import csv
import os
import statistics as st
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "results", "tolerance", "tolerance_raw.csv")
OUTDIR = os.path.join(ROOT, "apresentacao", "dados")

ALGS = ["quicksort", "mergesort", "shellsort", "heapsort"]
DELTAS = [3, 5, 7, 11]


def write(name, header, rows):
    with open(os.path.join(OUTDIR, name), "w", newline="") as f:
        w = csv.writer(f, delimiter=" ")
        w.writerow(header)
        w.writerows(rows)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    g = defaultdict(list)
    for r in csv.DictReader(open(RAW)):
        g[(r["algorithm"], r["variant"], int(r["n"]), int(r["delta"]))].append(r)
    sizes = sorted({k[2] for k in g})

    rows = []
    for n in sizes:
        row = [n]
        for a in ALGS:
            row.append(round(max(int(r["max_err"]) / d
                                 for d in DELTAS for r in g[(a, "serial", n, d)]), 2))
        rows.append(row)
    write("maxerr_por_n.dat", ["n", *ALGS], rows)

    for n in sizes:
        rows = []
        for d in DELTAS:
            row = [d]
            for a in ALGS:
                row.append(round(st.mean(int(r["rem"]) for r in g[(a, "serial", n, d)]) / n * 100, 2))
            rows.append(row)
        write(f"rem_n{n}.dat", ["delta", *ALGS], rows)

    print(f"[INFO] resumos gravados em {OUTDIR}")


if __name__ == "__main__":
    main()
