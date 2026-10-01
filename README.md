# Ordenação com Comparador Impreciso

Avaliação de algoritmos de ordenação quando o comparador não distingue valores
próximos: se `|a − b| ≤ δ`, a comparação responde "iguais" (modelo de
Ajtai et al.). O trabalho mede o **erro da saída** e o **desempenho** de
quatro algoritmos para δ ∈ {3, 5, 7, 11}, com δ = 0 como referência.

Derivado do [CSER-UFT/sort-evaluation](https://github.com/CSER-UFT/sort-evaluation),
de onde vêm os algoritmos e o executor de medições com `perf`.

## Principais resultados

| | quicksort | mergesort | shellsort | heapsort |
|---|---|---|---|---|
| Pior erro (n = 10⁶) | **3δ** | 5,0–5,4δ | 5,0–6,0δ | 5,0–5,6δ |
| Tempo com δ = 11 (serial) | **−5,4%** | −3,7% | −3,2% | +3,1% |
| Instruções com δ = 11 (serial) | **−11,9%** | −1,9% | −5,1% | −0,1% |

- O pior erro do quicksort fica limitado a 3δ; nos outros três ele cresce com n.
- Com tolerância, quicksort, mergesort e shellsort ficam mais rápidos, porque
  fazem menos trocas. O heapsort fica cerca de 3% mais lento.

## Estrutura

```
program/
  tolerance.h          comparador cmp_tol e métricas de erro
  quicksort.c          dual pivot
  mergesort.c          bottom-up
  shellsort.c          sequência de Knuth
  heapsort.c
scripts/
  run_tolerance.py              experimento de erro
  summarize_tolerance.py        resumos do experimento de erro
  run_tolerance_perf.sh         experimento de desempenho com perf
  summarize_tolerance_perf.py   resumos do experimento de desempenho
run_perf_job.sh                 executor de medições com perf
inputs/1000000.in               entrada usada nas medições de desempenho
results/tolerance/              resultados (CSV)
apresentacao/                   slides em LaTeX (Beamer)
```

## Como usar

O δ é lido da variável de ambiente `SORT_DELTA` (padrão 0) ou fixado na
compilação com `-DTOL_DEFAULT_DELTA=<δ>`. Com `SORT_METRICS=1`, o programa
imprime as métricas de erro da saída:

```
gcc -O3 -march=native -fopenmp program/quicksort.c -o quicksort_serial -lm
SORT_DELTA=5 SORT_METRICS=1 ./quicksort_serial inputs/1000000.in 1
```

```
TOL delta=5 n=1000000 time=... rem=... inv=... desc=... max_err=...
```

| Métrica | Significado |
|---|---|
| `rem` | elementos a remover para o resto ficar ordenado (n menos a maior subsequência não decrescente) |
| `inv` | pares fora de ordem |
| `desc` | vizinhos fora de ordem |
| `max_err` | maior `a[i] − a[j]` com `i < j` |

### Experimento de erro

```
python3 scripts/run_tolerance.py
python3 scripts/summarize_tolerance.py
```

São 600 execuções: 4 algoritmos, serial e paralelo (4 threads),
n ∈ {10⁴, 10⁵, 10⁶}, 5 sementes e δ ∈ {0, 3, 5, 7, 11}. O resultado fica em
`results/tolerance/tolerance_raw.csv`.

### Experimento de desempenho

Requer `perf`, `taskset`, `setarch` e `sudo`.

```
./scripts/run_tolerance_perf.sh        # 30 repetições por configuração
python3 scripts/summarize_tolerance_perf.py
```

Os arquivos brutos do `perf` ficam em `results/tolerance/perf/results/` e não
são versionados; o repositório traz os CSVs consolidados
(`tolerance_perf_raw.csv` e `tolerance_perf_summary.csv`).

## Referências

- M. Ajtai, V. Feldman, A. Hassidim, J. Nelson. *Sorting and Selection with
  Imprecise Comparisons*. ACM Transactions on Algorithms, 12(2), 2016.
- S. Chen, S. Jiang, B. He, X. Tang. *A Study of Sorting Algorithms on
  Approximate Memory*. Proc. ACM SIGMOD, 2016.

## Licença

GPL-3.0, a mesma do projeto original.
