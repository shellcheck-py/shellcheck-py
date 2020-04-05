#!/usr/bin/env python3
import io
import os.path
import re
import stat
import sys
import tarfile
import tempfile
import zipfile
from distutils.command.build import build as orig_build
from distutils.core import Command
from http import HTTPStatus
from typing import Dict
from urllib.request import urlopen

from setuptools import setup
from setuptools.command.install import install as orig_install

SHELLCHECK_VERSION = '0.7.1'
PY_VERSION = '1'


def get_arch() -> str:
    if sys.platform.startswith('linux'):
        # TODO(rhee): detect "linux.aarch64" and "linux.armv6hf"
        return 'linux.x86_64.tar.xz'
    elif sys.platform == 'darwin':
        return 'darwin.x86_64.tar.xz'
    elif sys.platform == 'win32':
        return 'zip'
    else:
        raise ValueError('Unsupported platform')


def get_artifact_name() -> str:
    return f'shellcheck-v{SHELLCHECK_VERSION}.{get_arch()}'


def get_download_url() -> str:
    return (
        'https://github.com/koalaman/shellcheck/releases/download/'
        f'v{SHELLCHECK_VERSION}/{get_artifact_name()}'
    )


def download(url: str) -> bytes:
    with urlopen(url) as resp:
        code = resp.getcode()
        if code != HTTPStatus.OK:
            raise ValueError(f'HTTP failure. Code: {code}')
        return resp.read()


def extract(url: str, data: bytes) -> Dict[str, bytes]:
    result = {}
    if '.tar.' in url:
        tmpf = tempfile.NamedTemporaryFile(delete=False)
        try:
            with tmpf:
                tmpf.write(data)
            with tarfile.open(tmpf.name) as tar:
                for member in (x for x in tar.getmembers() if x.isfile()):
                    name = member.name.rpartition('\\')[2].rpartition('/')[2]
                    result[name] = tar.extractfile(member).read()
        finally:
            os.remove(tmpf.name)
    elif url.endswith('.zip'):
        with io.BytesIO(data) as bio, zipfile.ZipFile(bio) as zipp:
            for info in (x for x in zipp.infolist() if not x.is_dir()):
                name = info.filename.rpartition('\\')[2].rpartition('/')[2]
                result[name] = zipp.read(info.filename)
    else:
        exe = 'shellcheck' if sys.platform != 'win32' else 'shellcheck.exe'
        result[exe] = data
    return result


def save_files(files: Dict[str, bytes], base_dir: str) -> None:
    os.makedirs(base_dir)

    for name, data in files.items():
        match = re.search(
            r'(?i)(?:^|[\/])(?P<basename>shellcheck)(?:.*?)(?P<ext>\.exe)?$',
            name
        )
        is_exe = False
        if match:
            name = f'{match.group("basename")}{match.group("ext") or ""}'
            is_exe = True

        output_path = os.path.join(base_dir, name)
        with open(output_path, 'wb') as fp:
            fp.write(data)

        if is_exe:
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
        files = extract(url, data)
        save_files(files, self.build_temp)


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
