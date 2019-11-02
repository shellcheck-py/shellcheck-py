#!/usr/bin/env python3

from setuptools import setup
from setuptools.command.install import install as orig_install
from setuptools.command.sdist import sdist as orig_sdist

from distutils.core import Command
from distutils.command.build import build as orig_build

from os import path

from sys import platform

from urllib.request import urlopen
from http import HTTPStatus

from hashlib import sha512

from os import makedirs
from os import fstat
from os import fchmod
import errno

from functools import lru_cache


def get_arch() -> str:
    if platform == "linux" or platform == "linux2":
        # TODO(rhee): detect "linux-aarch64" and "linux-armv6hf"
        return 'linux-x86_64'
    elif platform == "darwin":
        return 'darwin-x86_64'
    elif platform == "win32" or platform == "win64":
        return 'exe'
    else:
        raise RuntimeError('Unsupported platform')


def get_executable_name() -> str:
    return f'shellcheck-v{get_version()}.{get_arch()}'


@lru_cache(maxsize=1)
def get_version() -> str:
    with open('VERSION', 'r') as fp:
        return fp.read().strip()


def get_download_url() -> str:
    return path.join(
        'https://storage.googleapis.com/',
        'shellcheck',
        get_executable_name(),
    )


def download(url: str) -> bytes:
    with urlopen(url) as resp, urlopen(url + '.sha512sum') as shasum_resp:

        code = resp.getcode()
        scode = shasum_resp.getcode()
        if code != HTTPStatus.OK or scode != HTTPStatus.OK:
            raise RuntimeError(f'HTTP failure. Codes: {code}, {scode}')

        data = resp.read()
        actual_shasum = sha512(data).hexdigest()
        expected_shasum = shasum_resp.read().decode('utf8').split(" ")[0]

        if expected_shasum != actual_shasum:
            raise RuntimeError(
                'SHA512 mismatch! '
                f'expected "{expected_shasum}" but got "{actual_shasum}"'
            )

        return data


def save_executable(data: bytes, base_dir: str):
    out_dir = path.join(base_dir, 'bin')
    output_path = path.join(
        out_dir,
        'shellcheck',
    )

    makedirs(out_dir, exist_ok=True)

    with open(output_path, 'wb') as fp:
        fp.write(data)
        mode = fstat(fp.fileno()).st_mode
        mode |= 0o111
        fchmod(fp.fileno(), mode & 0o7777)


class build(orig_build):
    sub_commands = orig_build.sub_commands + [
        ('fetch_binaries', None),
    ]


class install(orig_install):
    sub_commands = orig_install.sub_commands + [
        ('install_shellcheck', None),
    ]


class fetch_binaries(Command):
    build_temp = None

    def initialize_options(self):
        pass

    def finalize_options(self):
        self.set_undefined_options('build', ('build_temp', 'build_temp'))

    def run(self):
        # save binary to self.build_temp
        url = get_download_url()
        data = download(url)
        save_executable(data, self.build_temp)


class install_shellcheck(Command):
    description = 'install the shellcheck executable'
    outfiles = ()
    build_dir = install_dir = None

    def initialize_options(self):
        pass

    def finalize_options(self):
        # this initializes attributes based on other commands' attributes
        self.set_undefined_options('build', ('build_temp', 'build_dir'))
        self.set_undefined_options('install', ('install_data', 'install_dir'))

    def run(self):
        self.outfiles = self.copy_tree(self.build_dir, self.install_dir)

    def get_outputs(self):
        return self.outfiles


command_overrides = {
    'install': install,
    'install_shellcheck': install_shellcheck,
    'build': build,
    'fetch_binaries': fetch_binaries,
}


def wheel_support():
    class bdist_wheel(orig_bdist_wheel):
        def finalize_options(self):
            orig_bdist_wheel.finalize_options(self)
            # Mark us as not a pure python package
            self.root_is_pure = False

        def get_tag(self):
            python, abi, plat = orig_bdist_wheel.get_tag(self)
            # We don't contain any python source, nor any python extensions
            python, abi = 'py2.py3', 'none'
            return python, abi, plat

    command_overrides['bdist_wheel'] = bdist_wheel


try:
    from wheel.bdist_wheel import bdist_wheel as orig_bdist_wheel
except ImportError:
    pass
else:
    wheel_support()

setup(cmdclass=command_overrides)
