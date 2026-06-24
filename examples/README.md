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
```

| Example | Demonstrates |
|---------|--------------|
| [`01_load_transactions.py`](01_load_transactions.py) | Parsing a multi-record BAI2 payload with `load_bai2`, including the credit/debit sign convention and an `88` continuation appended to a transaction description |
| [`02_summarize_file.py`](02_summarize_file.py) | Producing a `Bai2Summary` with `summarize_bai2`, then writing the payload to disk and reading it back with `load_bai2_file` |
