# Copyright (C) 2023-2026 Bank Statement Parser. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Coverage-guided Atheris fuzz target for the BAI2 loader.

``load_bai2`` and ``summarize_bai2`` are the package's two entry points
for untrusted text, and they promise one failure mode for bad input:
``ValueError`` (a missing ``01`` File Header, a malformed amount). Any
other exception escapes the target and libFuzzer records it as a
crash. Every transaction that does load must also be well formed: a
finite amount, ``source == "bai2"`` and, when it has a category, a
``bai2:<code>`` one; and the summary, which never reads amounts, must
not refuse a file the load accepted.

Run (Linux x86_64, Python 3.12+, ``poetry install --with fuzz``)::

    python fuzz/fuzz_load_bai2.py fuzz/corpus -max_total_time=60
"""

from __future__ import annotations

import sys

import atheris

with atheris.instrument_imports():
    from bankstatementparser_loader_bai2 import load_bai2, summarize_bai2


def _check_transactions(text: str) -> bool:
    """Load ``text``; return whether it parsed, failing on bad output."""
    try:
        transactions = load_bai2(text)
    except ValueError:
        return False
    for txn in transactions:
        if not txn.amount.is_finite():
            raise AssertionError(f"non-finite amount {txn.amount!r}")
        category = txn.category or "bai2:"
        if txn.source != "bai2" or not category.startswith("bai2:"):
            raise AssertionError(f"mislabelled transaction {txn!r}")
    return True


def test_one_input(data: bytes) -> None:
    """Load and summarise one fuzz input as BAI2 text."""
    text = atheris.FuzzedDataProvider(data).ConsumeUnicodeNoSurrogates(
        len(data)
    )
    loaded = _check_transactions(text)
    try:
        summarize_bai2(text)
    except ValueError:
        # Only a missing header refuses a summary, and that refuses
        # the load too.
        if loaded:
            raise


def main() -> None:
    """Hand the target to libFuzzer with the command-line options."""
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
