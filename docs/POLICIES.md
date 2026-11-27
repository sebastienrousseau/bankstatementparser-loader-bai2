# Supported Python policy

**Floor: Python 3.10.** `pyproject.toml` declares
`python = ">=3.10,<4.0"`, and the toolchain badge in the README states
the same floor; `scripts/readme-check.sh` fails CI if the two disagree.

**Tested: CPython 3.10, 3.11, 3.12, 3.13 and 3.14** on Linux, macOS and
Windows. The CI `Test` job runs that whole matrix on every push and pull
request, with the 100% line and branch coverage gate on each leg. A
version not in the matrix is not supported, whatever the constraint
allows.

**Fuzzing** runs on CPython 3.12 on Linux x86_64 only, because Atheris
ships wheels for nothing else. The manual is built on CPython 3.12.

## When the floor moves

- The floor is shared by every `bankstatementparser` package, so it
  moves for the whole suite in one release, never for one package
  alone.
- It moves only in a release, on the `0.0.x` line like any other
  change, and that release's CHANGELOG entry names the new floor and
  the reason.
- A new CPython release joins the matrix once its dependencies install
  on it; adding a version is a CHANGELOG entry too.
