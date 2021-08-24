#!/usr/bin/env python3
import hashlib
import http
import os.path
import stat
import sys
import urllib.request
from distutils.command.build import build as orig_build
from distutils.core import Command
from typing import Tuple

from setuptools import setup
from setuptools.command.install import install as orig_install

SHFMT_VERSION = 'v3.3.1'
POSTFIX_SHA256 = {
    # TODO(rhee): detect "linux.aarch64" and "linux.armv6hf"
    'linux': (
        'linux_amd64',
        '0f73bf27219571bca7c5ef7d740d6ae72227e3995ffd88c7cb2b5712751538e2',
    ),
    'darwin': (
        'darwin_amd64',
        'ade755f37fd470e176536593a72394bbf543c80e0256eb937c3c09d1f4b2a55d',
    ),
    'win32': (
        'windows_amd64.exe',
        'aa116e5437a7e03c137bea0331177a91f98735094ef0ca2ffcfd6be2a3d61765',
    ),
}
PY_VERSION = '3'


def get_download_url() -> Tuple[str, str]:
    postfix, sha256 = POSTFIX_SHA256[sys.platform]
    url = (
        f'https://github.com/mvdan/sh/releases/download/'
        f'{SHFMT_VERSION}/shfmt_{SHFMT_VERSION}_{postfix}'
    )
    print(url)
    return url, sha256


def download(url: str, sha256: str) -> bytes:
    with urllib.request.urlopen(url) as resp:
        code = resp.getcode()
        if code != http.HTTPStatus.OK:
            raise ValueError(f'HTTP failure. Code: {code}')
        data = resp.read()

    checksum = hashlib.sha256(data).hexdigest()
    if checksum != sha256:
        raise ValueError(f'sha256 mismatch, expected {sha256}, got {checksum}')

    return data


def save_executable(data: bytes, base_dir: str):
    exe = 'shfmt' if sys.platform != 'win32' else 'shfmt.exe'
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
    sub_commands = orig_install.sub_commands + [('install_shfmt', None)]


class fetch_binaries(Command):
    build_temp = None

    def initialize_options(self):
        pass

    def finalize_options(self):
        self.set_undefined_options('build', ('build_temp', 'build_temp'))

    def run(self):
        # save binary to self.build_temp
        url, sha256 = get_download_url()
        data = download(url, sha256)
        save_executable(data, self.build_temp)


class install_shfmt(Command):
    description = 'install the shfmt executable'
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
    'install_shfmt': install_shfmt,
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

setup(version=f'{SHFMT_VERSION}.{PY_VERSION}', cmdclass=command_overrides)
