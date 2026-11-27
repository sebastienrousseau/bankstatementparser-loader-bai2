# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT

# The README demo: the installed version, the repository's own
# multi-group BAI2 fixture, then the loader and summary examples.
# Render with `make demo`.

Output .github/demo.gif

Set Shell "bash"
Set FontSize 15
Set Width 1200
Set Height 600
Set Padding 20
Set Theme "Catppuccin Mocha"
Set TypingSpeed 35ms

Hide
Type "export PS1='$ ' && clear"
Enter
Show

Type "poetry run python -c 'import bankstatementparser_loader_bai2 as b; print(b.__version__)'"
Enter
Wait /\$$/
Sleep 1s

Type "head -8 tests/fixtures/multi_group_multi_account.bai"
Enter
Wait /\$$/
Sleep 2s

Type "clear && poetry run python examples/01_load_transactions.py"
Enter
Wait /\$$/
Sleep 3s

Type "clear && poetry run python examples/02_summarize_file.py"
Enter
Wait /\$$/
Sleep 4s
