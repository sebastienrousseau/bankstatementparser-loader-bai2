# bankstatementparser-loader-bai2 Roadmap

This roadmap tracks the next set of capabilities for the BAI2 loader
companion of the
[bankstatementparser](https://github.com/sebastienrousseau/bankstatementparser)
library. The versions are **target** windows; releases ship when the
gates pass, not on a calendar.

## v0.0.10 - Initial release (current)

- `load_bai2`, `load_bai2_file`, and `summarize_bai2` over a documented,
  pragmatic BAI2 subset (`01`/`02`/`03`/`16`/`88`, with `49`/`98`/`99`
  trailers ignored).
- `Decimal` amount conversion from minor units and a documented
  type-code-range debit/credit sign convention with the raw code
  preserved.
- 100% line + branch coverage gate, 100% docstring coverage gate.
- Two runnable examples.

## Planned

- **Optional control-total validation** — opt-in checking of the
  `49`/`98`/`99` trailer sums against the accumulated transaction
  amounts, surfaced as a structured discrepancy report.
- **Balance records** — surface the `03` account opening/closing balance
  fields (and the `100`/`015`-style summary type codes) alongside
  transactions.
- **Richer continuation handling** — interpret `88` continuations on
  `03` account records as account-level notes rather than dropping them.
- **Funds-type / availability** — expose the `fundsType` and
  value-dating distribution fields where banks populate them.

## Out of scope (handled elsewhere)

- **ISO 20022 camt.053 and SWIFT MT940** parsing — those are different
  formats with their own dedicated loaders.
- **PDF / image statement parsing** — see the core
  [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser)
  library.
