<!-- SPDX-License-Identifier: Apache-2.0 -->

# Getting support

Thanks for using bankstatementparser-loader-bai2. Here's the fastest way to get help, by need.

## Questions & how-to

- **Read first:** the [README](README.md), the runnable
  [`examples/`](examples/), and the parent
  [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser) repo for
  the `Transaction` model and statement-parsing background.
- **Still stuck?** Open a
  [GitHub Discussion](https://github.com/sebastienrousseau/bankstatementparser/discussions)
  on the parent repo (shared with bankstatementparser) or a question
  issue here. Include your Python version, `bankstatementparser-loader-bai2` version
  (`python -c "import bankstatementparser_loader_bai2; print(bankstatementparser_loader_bai2.__version__)"`),
  and a minimal BAI2 reproducer.

## Bugs

Open a bug report at
<https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/issues/new> with:

- your Python version,
- your `bankstatementparser-loader-bai2` version
  (`python -c "import bankstatementparser_loader_bai2; print(bankstatementparser_loader_bai2.__version__)"`),
- a minimal BAI2 reproducer (a small input file or string passed to
  `load_bai2`), and
- the full traceback.

A failing record set (with sensitive values redacted) helps enormously.

## Feature requests

Open a feature request at
<https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/issues/new>.
Improvements to BAI2 record-type coverage and parsing fidelity on top of
the [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser) public
API are especially welcome — see [ARCHITECTURE.md](ARCHITECTURE.md) for
the extension points and [ROADMAP.md](ROADMAP.md) for what's planned.

## Security

**Do not** open public issues for vulnerabilities. Follow the private
disclosure process in [SECURITY.md](SECURITY.md).

## Contributing & maintaining

See [CONTRIBUTING.md](CONTRIBUTING.md) and [GOVERNANCE.md](GOVERNANCE.md).

## Supported versions

Fixes land on the latest release line. See [SECURITY.md](SECURITY.md) for
the supported-version policy. bankstatementparser-loader-bai2 requires Python 3.10+.
