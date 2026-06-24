# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""BAI2 -> bankstatementparser ``Transaction`` loader.

BAI2 (Bank Administration Institute, version 2) is the US cash-management
file format banks ship for balance and transaction reporting. The
`bankstatementparser <https://pypi.org/project/bankstatementparser/>`_
library does not parse BAI2; this companion loader turns a BAI2 payload
into a flat list of
:class:`bankstatementparser.transaction_models.Transaction` objects.

See :mod:`bankstatementparser_loader_bai2.loader` for the documented
record subset, amount handling, and debit / credit sign convention.
"""

from bankstatementparser_loader_bai2.loader import (
    Bai2Summary,
    load_bai2,
    load_bai2_file,
    summarize_bai2,
)

__version__ = "0.0.1"

__all__ = [
    "load_bai2",
    "load_bai2_file",
    "summarize_bai2",
    "Bai2Summary",
    "__version__",
]
