[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/MaxWinterstein/shfmt-py/master.svg)](https://results.pre-commit.ci/latest/github/MaxWinterstein/shfmt-py/master)

# shfmt-py

A python wrapper to provide a pip-installable [shfmt] binary.

Internally this package provides a convenient way to download the pre-built
shellcheck binary for your particular platform.

This package is totally cloned from [shellcheck-py] and modified to provide `shfmt` instead.

## Installation

```bash
pip install shfmt-py
```

## Usage

### CLI

After installation, the `shfmt` binary should be available in your
environment (or `shfmt.exe` on windows).

### As pre-commit hook

See [pre-commit] for instructions

Sample `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/maxwinterstein/shfmt-py
  rev: 3.4.3.1
  hooks:
    - id: shfmt
```

## FAQ

Q: I get something like `SSL: CERTIFICATE_VERIFY_FAILED` on macOS
A: Install certificates with e.g.: `"/Applications/Python 3.9/Install Certificates.command"`. See [here][here1] or [here][here2] for

[shfmt]: https://github.com/mvdan/sh
[pre-commit]: https://pre-commit.com
[shellcheck-py]: https://github.com/shellcheck-py/shellcheck-py
[here1]: https://github.com/albertogeniola/MerossIot/issues/62#issuecomment-535769621
[here2]: https://stackoverflow.com/questions/27835619/urllib-and-ssl-certificate-verify-failed-error
