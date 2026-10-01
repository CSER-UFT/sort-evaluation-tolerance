#!/usr/bin/env python3
import csv
import itertools
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRCDIR = os.path.join(ROOT, "program")
OUTDIR = os.path.join(ROOT, "results", "tolerance")

ALGORITHMS = ["quicksort", "mergesort", "shellsort", "heapsort"]
DELTAS = [0, 3, 5, 7, 11]
SIZES = [10_000, 100_000, 1_000_000]
SEEDS = [11, 23, 37, 41, 53]
VARIANTS = [("serial", 1), ("parallel", 4)]

CFLAGS = ["-O3", "-march=native", "-fopenmp"]


def build(bindir):
    bins = {}
    for alg, (variant, _) in itertools.product(ALGORITHMS, VARIANTS):
        out = os.path.join(bindir, f"{alg}_{variant}")
        extra = ["-DPARALLEL"] if variant == "parallel" else []
        subprocess.run(["gcc", *CFLAGS, *extra, os.path.join(SRCDIR, f"{alg}.c"),
                        "-o", out, "-lm"], check=True)
        bins[(alg, variant)] = out
    return bins


def parse_tol(stdout):
    for line in stdout.splitlines():
        if line.startswith("TOL "):
            return dict(kv.split("=") for kv in line.split()[1:])
    raise RuntimeError(f"linha TOL ausente na saida:\n{stdout}")


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        bins = build(tmp)
        total = len(ALGORITHMS) * len(VARIANTS) * len(SIZES) * len(SEEDS) * len(DELTAS)
        done = 0
        for alg, (variant, threads), n, seed in itertools.product(
                ALGORITHMS, VARIANTS, SIZES, SEEDS):
            inp = os.path.join(tmp, f"{n}_{seed}.in")
            with open(inp, "w") as f:
                f.write(f"{seed}\n{n}\n")
            for delta in DELTAS:
                env = dict(os.environ, SORT_DELTA=str(delta), SORT_METRICS="1",
                           OMP_NUM_THREADS=str(threads))
                res = subprocess.run([bins[(alg, variant)], inp, str(threads)],
                                     capture_output=True, text=True, env=env)
                if res.returncode != 0:
                    raise RuntimeError(f"{alg}_{variant} n={n} seed={seed} delta={delta} "
                                       f"falhou:\n{res.stderr}")
                m = parse_tol(res.stdout)
                rows.append({"algorithm": alg, "variant": variant, "threads": threads,
                             "n": n, "seed": seed, "delta": delta, **m})
                done += 1
            print(f"[{done}/{total}] {alg}_{variant} n={n} seed={seed}", flush=True)

    path = os.path.join(OUTDIR, "tolerance_raw.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[INFO] {len(rows)} execucoes salvas em {path}")


if __name__ == "__main__":
    main()
