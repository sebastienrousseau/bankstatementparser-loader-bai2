# bankstatementparser-loader-bai2 examples

Runnable, self-contained examples for the BAI2 loader. Each script
parses an inline BAI2 sample, so no external data files are required.

Install the package (which pulls in the core `bankstatementparser`
library) first:

```sh
pip install bankstatementparser-loader-bai2   # Python 3.10+
```

Then run any example from the repository root:

```sh
python examples/01_load_transactions.py
python examples/02_summarize_file.py
python examples/03_full_tour.py
```

| Example | Demonstrates |
|---------|--------------|
| [`01_load_transactions.py`](01_load_transactions.py) | Parsing a multi-record BAI2 payload with `load_bai2`, including the credit/debit sign convention and an `88` continuation appended to a transaction description |
| [`02_summarize_file.py`](02_summarize_file.py) | Producing a `Bai2Summary` with `summarize_bai2`, then writing the payload to disk and reading it back with `load_bai2_file` |
| [`03_full_tour.py`](03_full_tour.py) | A complete tour of the public API — `summarize_bai2` (printing every `Bai2Summary` field), `load_bai2` (from a string), and `load_bai2_file` (from a temp file) against one inline payload covering `01`/`02`/`03`/`16`-credit/`16`-debit/`88`/`49`/`98`/`99` |

Every public function exported by `bankstatementparser_loader_bai2`
(`load_bai2`, `load_bai2_file`, `summarize_bai2`, and the `Bai2Summary`
dataclass) is exercised across these scripts; each runs offline against a
self-contained inline sample, prints its results, and exits 0.
