# bankstatementparser-loader-bai2

**BAI2** (Bank Administration Institute, version 2) is the de-facto US
cash-management file format that banks ship for intraday and prior-day
balance and transaction reporting.

**bankstatementparser-loader-bai2** turns a BAI2 payload into a flat
list of
[`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser)
`Transaction` objects (`source="bai2"`) that the rest of a deterministic
pipeline can consume unchanged.

| Concern | How this loader handles it |
| :--- | :--- |
| Record model | A documented, pragmatic subset of BAI2 (`01`/`02`/`03`/`16`/`88` plus ignored trailers) |
| Amounts | BAI2 minor-unit integers (cents) converted to `Decimal` (never `float`); a malformed amount is a `ValueError` |
| Debit / credit | Derived from the `16` type-code range, with the raw code preserved |
| Multiple accounts | All `16` records across every group and account are flattened into one list |
| Real-world text | The `16` free-text field (and `88` continuations) is kept verbatim: commas and slashes inside it are preserved, not split on |
| Robustness | Tolerates CRLF, blank lines, trailing spaces, an optional trailing `/` per record, and `V`/`S` funds-type subfields |
| Errors | A clear `ValueError` if the file does not start with an `01` File Header |

## In this manual

- [BAI2 support](format.md): the public API, the record subset, the
  field mapping and the sign convention.
- [The suite](suite.md): the `bankstatementparser` packages.
- [Comparison](COMPARISON.md) and [Benchmarks](BENCHMARKS.md).
- [Supported Python policy](POLICIES.md).
- [API reference](api.md): generated from the docstrings.
- [Roadmap](roadmap.md), [Changelog](changelog.md) and
  [Security policy](security.md).

The source, issues and releases live on
[GitHub](https://github.com/sebastienrousseau/bankstatementparser-loader-bai2);
the package is on
[PyPI](https://pypi.org/project/bankstatementparser-loader-bai2/).
