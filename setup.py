#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import http
import io
import os.path
import platform
import stat
import sys
import tarfile
import urllib.request
import zipfile

from distutils.command.build import build as orig_build
from distutils.core import Command
from setuptools import setup
from setuptools.command.install import install as orig_install

SHELLCHECK_VERSION = '0.9.0'
POSTFIX_SHA256 = {
    ('linux', 'armv6hf'): (
        'linux.armv6hf.tar.xz',
        '03deed9ded9dd66434ccf9649815bcde7d275d6c9f6dcf665b83391673512c75',
    ),
    ('linux', 'aarch64'): (
        'linux.aarch64.tar.xz',
        '179c579ef3481317d130adebede74a34dbbc2df961a70916dd4039ebf0735fae',
    ),
    ('linux', 'x86_64'): (
        'linux.x86_64.tar.xz',
        '700324c6dd0ebea0117591c6cc9d7350d9c7c5c287acbad7630fa17b1d4d9e2f',
    ),
    ('darwin', 'x86_64'): (
        'darwin.x86_64.tar.xz',
        '7d3730694707605d6e60cec4efcb79a0632d61babc035aa16cda1b897536acf5',
    ),
    ('win32', 'AMD64'): (
        'zip',
        'ae58191b1ea4ffd9e5b15da9134146e636440302ce3e2f46863e8d71c8be1bbb',
    ),
}
POSTFIX_SHA256[('cygwin', 'x86_64')] = POSTFIX_SHA256[('win32', 'AMD64')]
POSTFIX_SHA256[('win32', 'ARM64')] = POSTFIX_SHA256[('win32', 'AMD64')]
POSTFIX_SHA256[('darwin', 'arm64')] = POSTFIX_SHA256[('darwin', 'x86_64')]
POSTFIX_SHA256[('linux', 'armv7l')] = POSTFIX_SHA256[('linux', 'armv6hf')]
PY_VERSION = '6'


def get_download_url() -> tuple[str, str]:
    postfix, sha256 = POSTFIX_SHA256[(sys.platform, platform.machine())]
    url = (
        f'https://github.com/koalaman/shellcheck/releases/download/'
        f'v{SHELLCHECK_VERSION}/shellcheck-v{SHELLCHECK_VERSION}.{postfix}'
    )
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


def extract(url: str, data: bytes) -> bytes:
    with io.BytesIO(data) as bio:
        if '.tar.' in url:
            with tarfile.open(fileobj=bio) as tarf:
                for info in tarf.getmembers():
                    if info.isfile() and info.name.endswith('shellcheck'):
                        return tarf.extractfile(info).read()
        elif url.endswith('.zip'):
            with zipfile.ZipFile(bio) as zipf:
                for info in zipf.infolist():
                    if info.filename.endswith('.exe'):
                        return zipf.read(info.filename)

    raise AssertionError(f'unreachable {url}')


def save_executable(data: bytes, base_dir: str):
    exe = 'shellcheck' if sys.platform != 'win32' else 'shellcheck.exe'
    output_path = os.path.join(base_dir, exe)
    os.makedirs(base_dir, exist_ok=True)

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
        url, sha256 = get_download_url()
        archive = download(url, sha256)
        data = extract(url, archive)
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
