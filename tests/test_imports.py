import subprocess
import sys


def test_core_import_never_loads_optional_dependencies():
    code = """
import importlib.abc
import sys

class BlockOptional(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        blocked = {'numpy', 'sklearn', 'deinterf', 'dafmit_aeromag'}
        if sys.version_info >= (3, 11):
            blocked.add('typing_extensions')
        if fullname.split('.')[0] in blocked:
            raise AssertionError(f'Unexpected dependency: {fullname}')

sys.meta_path.insert(0, BlockOptional())
from dataioc import *
assert DataIoC().with_data(42)[int] == 42
"""
    subprocess.run([sys.executable, "-c", code], check=True)
