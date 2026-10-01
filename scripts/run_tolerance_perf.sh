#!/bin/bash
set -euo pipefail

NRUNS="${1:-30}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$ROOT/results/tolerance/perf"
BIN="$WORK/bin"

ALGORITHMS=(quicksort mergesort shellsort heapsort)
DELTAS=(0 3 5 7 11)
INPUT="$ROOT/inputs/1000000.in"
THREADS=(1 4)

mkdir -p "$BIN"
rm -f "$WORK"/results/*.p1 "$WORK"/results/*.p2 "$WORK"/results/*.p3

echo "[INFO] Compilando..."
for alg in "${ALGORITHMS[@]}"; do
    for d in "${DELTAS[@]}"; do
        gcc -O3 -march=native -fopenmp -DTOL_DEFAULT_DELTA="$d" \
            "$ROOT/program/$alg.c" -o "$BIN/${alg}-d${d}_serial" -lm
        gcc -O3 -march=native -fopenmp -DTOL_DEFAULT_DELTA="$d" -DPARALLEL \
            "$ROOT/program/$alg.c" -o "$BIN/${alg}-d${d}_parallel" -lm
    done
done

sudo -v
while true; do sudo -n true; sleep 60; done 2>/dev/null &
KEEPALIVE=$!
trap 'kill $KEEPALIVE 2>/dev/null' EXIT

cd "$WORK"
total=$(( ${#ALGORITHMS[@]} * ${#DELTAS[@]} * ${#THREADS[@]} ))
i=0
for alg in "${ALGORITHMS[@]}"; do
    for t in "${THREADS[@]}"; do
        variant=$([ "$t" -eq 1 ] && echo serial || echo parallel)
        for d in "${DELTAS[@]}"; do
            i=$((i + 1))
            echo "================ [$i/$total] ${alg} delta=${d} ${variant} t=${t}"
            "$ROOT/run_perf_job.sh" "$BIN/${alg}-d${d}_${variant}" "$INPUT" "$t" "$NRUNS" \
                > "$WORK/log_${alg}-d${d}_${variant}.txt" 2>&1 \
                || echo "[WARN] falhou, veja $WORK/log_${alg}-d${d}_${variant}.txt"
        done
    done
done

echo
echo "[INFO] Concluido. Arquivos em $WORK/results/"
