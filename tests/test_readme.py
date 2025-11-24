import doctest
import re
from pathlib import Path

import pytest

from dataioc import _data

ROOT = Path(__file__).parents[1]


def _execute_python_examples(path):
    namespace = {}
    for block in re.findall(
        r"```python\n(.*?)```", path.read_text(encoding="utf-8"), re.DOTALL
    ):
        exec(compile(block, str(path), "exec"), namespace)


@pytest.mark.parametrize("filename", ["README.md", "README.zh-CN.md"])
def test_readme_python_examples(filename):
    _execute_python_examples(ROOT / filename)


@pytest.mark.parametrize(
    "filename",
    [
        f"{page}{suffix}.md"
        for page in ("quickstart", "concepts", "providers", "indexed-data", "numpy")
        for suffix in ("", ".zh")
    ],
)
def test_guide_python_examples(filename):
    _execute_python_examples(ROOT / "docs" / filename)


def test_source_docstring_examples():
    assert doctest.testmod(_data).failed == 0
