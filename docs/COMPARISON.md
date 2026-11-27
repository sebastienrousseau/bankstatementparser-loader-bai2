# Comparison

Where bankstatementparser-loader-bai2 fits next to the other BAI2
parsers a Python user would reach for. Every cell comes from the
project's own source code, read on 2026-11-27; nothing here is a
measured ranking.

| Project | Language | `88` continuations | Commas in `16` text | Funds-type subfields | `700`-`799` loan codes | Writes BAI2 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **bankstatementparser-loader-bai2** | Python | Appended to the preceding `16` text | Kept verbatim | `V` and `S` shift the reference and text fields | Negative (debit side) | No |
| [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser) `Bai2Parser` 0.0.35 | Python | Ignored | Split on (text is the seventh comma field) | Not handled (text read at a fixed index) | Positive (only `400`-`699` are debits) | No |
| [`bai2`](https://github.com/ministryofjustice/bai2) (Ministry of Justice), MIT | Python | Merged into the record they continue | Kept (fields after the references are re-joined) | Parsed, including distributed availability | Not signed: amounts stay unsigned integers | Yes |

Evidence: `bankstatementparser/parsers/bai2.py` in the core (record
dispatch, `_handle_detail_16`), `bai2/parsers.py` and `bai2/helpers.py`
in `ministryofjustice/bai2`, and `bankstatementparser_loader_bai2/loader.py`
here.

## When each fits

- **bankstatementparser-loader-bai2**: you want BAI2 transactions as
  `bankstatementparser` `Transaction` objects, signed, with the free text
  intact.
- **`bankstatementparser` `Bai2Parser`**: your files carry no `88`
  continuations, no commas in the text and plain `Z`/`0` funds types,
  and you want no extra package.
- **`bai2`**: you need the whole BAI2 object model, control totals or
  writing BAI2 files, and will map the records yourself.

The wider family is listed in [The suite](suite.md).
