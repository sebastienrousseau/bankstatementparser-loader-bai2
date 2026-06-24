# Contributing to bankstatementparser-loader-bai2

Thank you for your interest in contributing to bankstatementparser-loader-bai2. This guide covers
the development workflow and standards.

`bankstatementparser-loader-bai2` is the BAI2 loader companion to
[`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser). It parses
BAI2 (Bank Administration Institute, version 2) cash-management files into
`bankstatementparser` `Transaction` objects via a small public API:
`load_bai2`, `load_bai2_file`, and `summarize_bai2`. It depends on
`bankstatementparser`, so most domain behaviour lives in the core library.

## Development Setup

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation)
- Git with SSH commit signing configured

### Setup

```bash
# Clone and install
git clone git@github.com:sebastienrousseau/bankstatementparser-loader-bai2.git
cd bankstatementparser-loader-bai2
poetry env use python3.12
poetry install

# Verify
poetry run pytest tests/ -q
```

The package depends on the core `bankstatementparser` library
(`>= 0.0.9`); it is installed automatically by `poetry install`.

### On macOS

```bash
brew install python@3.12 poetry
```

### On Linux (Debian/Ubuntu)

```bash
sudo apt install python3 python3-pip
pip install poetry
```

### On WSL

```bash
sudo apt install python3 python3-pip
pip install poetry
# Ensure ~/.local/bin is in PATH
```

## Workflow

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
3. **Make changes** - follow the coding standards below
4. **Run tests**:
   ```bash
   poetry run pytest tests/ -v
   ```
5. **Run linters**:
   ```bash
   poetry run ruff check bankstatementparser_loader_bai2/
   poetry run mypy --strict bankstatementparser_loader_bai2/
   poetry run black --check bankstatementparser_loader_bai2/ tests/
   ```
6. **Sign and commit**:
   ```bash
   git commit -S -m "feat: add my feature"
   ```
7. **Push** and open a pull request

## Commit Signing (Required)

All commits **must** be signed with SSH or GPG.

### SSH Signing

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519
git config --global commit.gpgsign true
```

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: handle 88 continuation on account records
fix: correct the credit/debit sign on type-16 detail records
docs: clarify the sign convention
test: cover multi-group file parsing
refactor: simplify field splitting in the loader
```

## Coding Standards

- **Line length:** 79 characters (enforced by Black + Ruff)
- **Type hints:** Required on all public functions (mypy strict)
- **Docstrings:** Required on all public classes and functions
  (interrogate enforces 100%)
- **Tests:** Every new feature or fix must include tests

## Testing

```bash
# Full suite
poetry run pytest tests/ -v

# Single file
poetry run pytest tests/test_loader.py -v
```

The suite enforces 100% line and branch coverage.

## Pull Request Checklist

- [ ] All tests pass (`poetry run pytest`)
- [ ] Linters pass (`ruff check`, `mypy --strict`, `black --check`)
- [ ] Coverage and docstring gates pass (pytest 100%, interrogate 100%)
- [ ] Commits are signed
- [ ] PR title follows conventional commit format
- [ ] New features include tests and documentation

## License

By contributing, you agree that your contributions will be licensed under
the [Apache License 2.0](LICENSE).
