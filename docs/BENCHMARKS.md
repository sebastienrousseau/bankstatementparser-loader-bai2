# Benchmarks

`benches/bench_load_bai2.py` measures what a BAI2 file costs to load as
it grows along the two axes a bank-day file grows in practice:
transactions within one account (`16` records under one `03`) and
accounts within one file (several `03` groups under one `02`). It times
`load_bai2` and, beside it, `summarize_bai2`, because a caller that only
wants totals should not pay for the full transaction list.

Nothing asserts a threshold: wall-clock is not comparable between
machines. CI runs `python benches/bench_load_bai2.py --quick` on every
push so the benchmark keeps running against the current API.

## Results

Run with `poetry run python benches/bench_load_bai2.py` on 2026-11-27:
Apple M1 Pro, macOS 27.2.1, CPython 3.12.16,
bankstatementparser-loader-bai2 0.0.36, bankstatementparser 0.0.35.

| Accounts | Transactions each | Total | KiB | `load_bai2` ms | `summarize_bai2` ms | us per transaction |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 10 | 10 | 0.7 | 0.05 | 0.02 | 5.15 |
| 1 | 100 | 100 | 6.4 | 0.43 | 0.12 | 4.29 |
| 1 | 1000 | 1000 | 66.2 | 4.35 | 1.21 | 4.35 |
| 10 | 500 | 5000 | 328.9 | 22.74 | 5.77 | 4.55 |
| 50 | 200 | 10000 | 647.8 | 46.82 | 12.24 | 4.68 |

The cost per transaction at 10,000 transactions is 0.91x the cost at
10, so loading is linear: a payroll-day file costs in proportion to its
size. `summarize_bai2` costs at most 0.32x `load_bai2`, so the summary
path does not build the transaction list and throw it away.

Reproduce with `python benches/bench_load_bai2.py` (add `--json` for
machine-readable output).
