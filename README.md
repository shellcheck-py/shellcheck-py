[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/MaxWinterstein/shfmt-py/master.svg)](https://results.pre-commit.ci/latest/github/MaxWinterstein/shfmt-py/master)

# shfmt-py

A python wrapper to provide a pip-installable [shfmt] binary.

Internally this package provides a convenient way to download the pre-built
shellcheck binary for your particular platform.

This package is totally cloned from [shellcheck-py] and modified to provide `shfmt` instead.

### installation

```bash
pip install shfmt-py
```

### usage

After installation, the `shellcheck` binary should be available in your
environment (or `shellcheck.exe` on windows).

### As a pre-commit hook

See [pre-commit] for instructions

Sample `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/maxwinterstein/shfmt-py
    rev: v3.3.1
    hooks:
    -   id: shfmt
```

[shfmt]: https://github.com/mvdan/sh
[pre-commit]: https://pre-commit.com
[shellcheck-py]: https://github.com/shellcheck-py/shellcheck-py
