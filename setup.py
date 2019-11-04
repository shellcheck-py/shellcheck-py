#!/usr/bin/env python3
import os.path
import stat
import sys
from distutils.command.build import build as orig_build
from distutils.core import Command
from hashlib import sha512
from http import HTTPStatus
from urllib.request import urlopen

from setuptools import setup
from setuptools.command.install import install as orig_install

SHELLCHECK_VERSION = '0.7.0'
PY_VERSION = '1'


def get_arch() -> str:
    if sys.platform.startswith('linux'):
        # TODO(rhee): detect "linux-aarch64" and "linux-armv6hf"
        return 'linux-x86_64'
    elif sys.platform == 'darwin':
        return 'darwin-x86_64'
    elif sys.platform == 'win32':
        return 'exe'
    else:
        raise ValueError('Unsupported platform')


def get_executable_name() -> str:
    return f'shellcheck-v{SHELLCHECK_VERSION}.{get_arch()}'


def get_download_url() -> str:
    return f'https://storage.googleapis.com/shellcheck/{get_executable_name()}'


def download(url: str) -> bytes:
    with urlopen(url) as resp, urlopen(url + '.sha512sum') as shasum_resp:
        code = resp.getcode()
        scode = shasum_resp.getcode()
        if code != HTTPStatus.OK or scode != HTTPStatus.OK:
            raise ValueError(f'HTTP failure. Codes: {code}, {scode}')

        data = resp.read()
        actual_shasum = sha512(data).hexdigest()
        expected_shasum = shasum_resp.read().decode('utf8').split(' ')[0]

        if expected_shasum != actual_shasum:
            raise ValueError(
                f'SHA512 mismatch! '
                f'expected "{expected_shasum}" but got "{actual_shasum}"',
            )

        return data


def save_executable(data: bytes, base_dir: str):
    exe = 'shellcheck' if sys.platform != 'win32' else 'shellcheck.exe'
    output_path = os.path.join(base_dir, exe)
    os.makedirs(base_dir)

    with open(output_path, 'wb') as fp:
        fp.write(data)

    # Mark as executable.
    # https://stackoverflow.com/a/14105527
    mode = os.stat(output_path).st_mode
    mode |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    os.chmod(output_path, mode)


class build(orig_build):
    sub_commands = orig_build.sub_commands + [('fetch_binaries', None)]


class install(orig_install):
    sub_commands = orig_install.sub_commands + [('install_shellcheck', None)]


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
        self.set_undefined_options(
            'install', ('install_scripts', 'install_dir'),
        )

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


try:
    from wheel.bdist_wheel import bdist_wheel as orig_bdist_wheel
except ImportError:
    pass
else:
    class bdist_wheel(orig_bdist_wheel):
        def finalize_options(self):
            orig_bdist_wheel.finalize_options(self)
            # Mark us as not a pure python package
            self.root_is_pure = False

        def get_tag(self):
            _, _, plat = orig_bdist_wheel.get_tag(self)
            # We don't contain any python source, nor any python extensions
            return 'py2.py3', 'none', plat

    command_overrides['bdist_wheel'] = bdist_wheel

setup(version=f'{SHELLCHECK_VERSION}.{PY_VERSION}', cmdclass=command_overrides)
