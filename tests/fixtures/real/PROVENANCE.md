<!-- SPDX-License-Identifier: Apache-2.0 -->

# Provenance of the real-world BAI2 fixtures

These files are **third-party, real-world-format BAI2 cash-management
files** vendored verbatim (byte-for-byte) into this repository's test
corpus. They are **not** edited, normalised, or hand-crafted: the whole
point is that they are messy, real bank output that exercises the loader
against constructs synthetic fixtures miss.

## Source

| Fixture file | Upstream path |
| :--- | :--- |
| `moov_bai2_sample1.bai` | [`test/testdata/sample1.txt`](https://github.com/moov-io/bai2/blob/master/test/testdata/sample1.txt) |
| `moov_bai2_sample5_issue113.bai` | [`test/testdata/sample5-issue113.txt`](https://github.com/moov-io/bai2/blob/master/test/testdata/sample5-issue113.txt) |

- **Upstream project:** [moov-io/bai2](https://github.com/moov-io/bai2)
- **License:** Apache License, Version 2.0 (same license as this project)
- **Retrieval date:** 2026-06-24
- **Retrieval method:** `curl -fsSL` of the raw files on the `master`
  branch, with no subsequent editing of the data.

## What they are (honest description)

- `moov_bai2_sample1.bai` — a real-world-format BAI2 file from the
  moov-io/bai2 test corpus: a single CAD group with two accounts and
  value-dated (`V` funds-type) transaction detail records, including
  `88` continuations that carry structured availability data on the
  `03` account summary.
- `moov_bai2_sample5_issue113.bai` — **derived from a real GitHub
  issue** ([moov-io/bai2#113](https://github.com/moov-io/bai2/issues/113)).
  It contains the gnarly real-world constructs that motivated this
  change: free-text `16` fields full of commas (`ACH Credit
  Payment,Entry Description: EXP; -, SEC: CCD, ...`), slashes inside
  reference and text fields (`Client Ref ID: AB/GS/TEST0001/RPBA0001`),
  a `88:` colon-delimited continuation, trailing spaces after the
  record terminator, and many `88` continuations carrying structured
  sub-data (`EREF:`, `DBNM:`, `CACT:`, ...).

## What they are NOT

These are **third-party test data**, not a customer export from this
project's own users. No real account holder's private data is implied;
the values are the moov-io project's published test fixtures. They are
included solely to test parsing behaviour against real-world format.

## Attribution (Apache-2.0)

Per the Apache License, Version 2.0, attribution to the upstream
moov-io/bai2 project is preserved here. The upstream copyright and
license notices apply to the unmodified fixture data; see
<https://github.com/moov-io/bai2/blob/master/LICENSE>.
