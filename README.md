# shellcheck-py

A python wrapper to provide a pip-installable [shellcheck] binary.

Internally this package provides a convenient way to download the pre-built
shellcheck binary for your particular platform.

### installation

```bash
pip install shellcheck-py
```

### usage

After installation, the `shellcheck` binary should be available in your
environment (or `shellcheck.exe` on windows).

### As a pre-commit hook

See [pre-commit] for instructions

Sample `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/ryanrhee/shellcheck-py
    rev: v0.7.1.1
    hooks:
    -   id: shellcheck
```

[shellcheck]: https://shellcheck.net
[pre-commit]: https://pre-commit.com
