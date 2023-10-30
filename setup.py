from __future__ import annotations

from setuptools import setup

try:
    from wheel.bdist_wheel import bdist_wheel as orig_bdist_wheel
except ImportError:
    cmdclass = {}
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

    cmdclass = {'bdist_wheel': bdist_wheel}

setup(cmdclass=cmdclass)
