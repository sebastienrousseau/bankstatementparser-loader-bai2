# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in
bankstatementparser-loader-bai2, please email
**security@bankstatementparser.com** instead of using the issue tracker.

Please include:
1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if available)

We will acknowledge receipt within 48 hours and provide updates on the
remediation timeline.

## Threat Model

`bankstatementparser-loader-bai2` is a pure-Python library that parses
BAI2 cash-management text into
[`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser)
`Transaction` objects. It has no network listener, performs no XML
parsing, and executes no external code. The security surface is small:

- **Untrusted input** — `load_bai2(text)` may be handed arbitrary
  strings. Parsing is a bounded, single-pass tokenisation with no
  recursion or `eval`, so malformed input results in a `ValueError` or
  best-effort extraction, never code execution.
- **Filesystem reads** — `load_bai2_file(path)` opens a caller-supplied
  path with `Path.read_text`. It does not write, append, or delete.

## Hardening

- **No code execution** — the loader never calls `eval`, `exec`, or
  `subprocess`, and imports nothing dynamically.
- **No network and no XML** — there is nothing to harden against XXE,
  SSRF, or TLS misconfiguration because none of those code paths exist.
- **Decimal arithmetic** — financial amounts use `decimal.Decimal`
  throughout, avoiding `float` rounding surprises.
- **Bounded parsing** — input is processed line by line with simple
  string operations; there are no unbounded regular expressions or
  backtracking hot spots.

## Continuous Integration

- `ci.yml` runs the full quality matrix (ruff, mypy, pytest with the
  100% coverage gate, interrogate).
- `security.yml` runs `bandit` against the package on every push and
  weekly via cron.
- `codeql.yml` runs GitHub's CodeQL Python analysis weekly.
- Dependency updates are picked up via Dependabot.

## Cryptography Status

`bankstatementparser-loader-bai2` does not perform cryptographic
operations. It does not sign, encrypt, verify certificates, or hash
passwords. Any crypto-bearing package in the dependency tree is
transitive via `bankstatementparser`.

## Contact

- **Email**: security@bankstatementparser.com
- **GitHub Advisories**: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/security/advisories
- **GitHub Discussions**: https://github.com/sebastienrousseau/bankstatementparser/discussions
