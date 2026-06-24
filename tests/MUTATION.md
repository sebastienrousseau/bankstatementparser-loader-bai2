<!-- SPDX-License-Identifier: Apache-2.0 -->

# Mutation testing report

Mutation testing is run with [`mutmut`](https://github.com/boxed/mutmut)
(version 3.x). It mutates the package source
(`bankstatementparser_loader_bai2/`) and re-runs the behavioural test
suite against each mutant; a *survivor* is a mutation the tests do not
detect — i.e. a behaviour we have not pinned.

## How to run

```bash
make mutation      # mutmut run + mutmut results
# or directly:
mutmut run
mutmut results
mutmut show <mutant-name>
```

Configuration lives in `[tool.mutmut]` in `pyproject.toml`. The mutant
runs execute the loader-behaviour suites only
(`test_loader.py`, `test_fixture_golden.py`,
`test_real_fixtures_golden.py`, `test_mutation_kills.py`). The
docs/regression suites are excluded from the mutant runs because they
assert documentation consistency (they do not pin loader logic) and they
`exec` README code blocks in-process, which collides with mutmut's import
trampoline inside its sandbox copy.

## Score

| Metric | Value |
| :--- | ---: |
| Total mutants | 336 |
| Killed | 317 |
| Survived | 19 |
| **Kill rate** | **94.3%** |
| **Kill rate excluding documented equivalent mutants** | **100%** |

All 19 survivors are **equivalent mutants**: they change the source text
but cannot change observable behaviour for any valid (or invalid) input,
so no test can distinguish them. Each is justified below. The remaining
non-equivalent mutants are all killed.

## Equivalent mutants (justified survivors)

### `_iter_records` line-ending normalisation (10, 12, 13)

These mutate the string literals in
`text.replace("\r\n", "\n").replace("\r", "\n")` (e.g. `"\r\n"` ->
`"XX\r\nXX"`, or the replacement `"\n"` -> `"XX\nXX"`). The two
`replace` calls are redundant by design: any `\r` left behind by a
mutated first replace is still converted by the second
`replace("\r", "\n")` (and vice-versa), and a CRLF that survives the
first call still collapses via the second. The net normalisation — and
therefore the record stream — is identical, so no input distinguishes
them.

### `_iter_records` terminator trim `rstrip` -> `lstrip` (21)

`line = line[:-1].rstrip()` trims trailing whitespace before the `/`
terminator. The line has already been `line.strip()`-ed at the top of
the loop, so it has no leading whitespace for `lstrip` to remove
differently; and `_split_16` / `_split_record` `.strip()` each field
afterwards, so any trailing-space difference is erased downstream.
Output is identical.

### `_record_code` split maxsplit (5, 8, 14, 17)

These change the `maxsplit` argument of `record.split(",", 1)` /
`head.split(":", 1)` (to absent or `2`). Only `[0]` (the first segment)
is read, and the first segment is identical regardless of `maxsplit`, so
the returned code never changes.

### `_split_16` funds-type guard / default (17, 18)

`len(parts) > 3` -> `> 4` and the `else ""` -> `else "XXXX"` only affect
the `funds_type` value, which is solely fed to `_text_field_index`. When
`len(parts) <= 3` there are no ref/text fields to locate, so the
funds-type value is never consumed; and `"XXXX"` maps to the same
"no extra subfields" branch (`_FUNDS_TYPE_SUBFIELDS.get(...) == 0`) as
`""`. No observable difference.

### `_split_16` text guard `>` -> `>=` (38)

`len(parts) > text_index` -> `>= text_index` differs only when
`len(parts) == text_index`. In that case the original yields `""`, and
the mutant yields `",".join(parts[text_index:])` = `",".join([])` =
`""`. Identical.

### `_continuation_text` `and` -> `or` (6)

`if found and head.strip() == "88"`. This helper is only ever called with
a record whose code is `88`. When a separator is found, `head` is `"88"`
so both operators are `True`; when no separator is found, the original
skips and the mutant returns the (empty) tail — both produce `""`. No
distinguishing input exists.

### `_parse_bai2_date` `or` -> `and` (2)

`if len(text) != 6 or not text.isdigit(): return None`. The mutant
(`and`) lets a malformed value (wrong length, or non-digit) fall through,
but the subsequent `datetime.strptime` is wrapped in a `try/except
ValueError` that returns `None` for exactly those malformed values. Both
branches return `None`, so the result is unchanged.

### `_parse_bai2_date` day-slice `text[4:6]` -> `text[4:7]` (23)

The function only reaches this line when `len(text) == 6`, so `text[4:7]`
and `text[4:6]` are the same two-character slice (slicing past the end is
a no-op in Python). Identical.

### State-init `None` -> `""` for falsy-only uses (load_bai2 20, 45; summarize_bai2 30)

`account_currency` is consumed as `account_currency or group_currency`,
where `None` and `""` are both falsy and yield `group_currency`
identically. `summarize_bai2`'s `group_currency` initialiser is never
read before its first assignment inside the `02` branch. No behaviour
change.

### `load_bai2_file` encoding alias (2, 5)

`encoding="utf-8"` -> `encoding=None` or `"UTF-8"`. The vendored fixtures
and all test payloads are ASCII, for which the platform default and the
case-insensitive `"UTF-8"` alias decode byte-for-byte identically to
`"utf-8"`. (A non-equivalent failure would require a non-UTF-8 platform
default *and* non-ASCII bytes, which this loader's text contract does not
cover.)
