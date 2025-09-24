import doctest
import re
from pathlib import Path

from dataioc import _data


def test_readme_python_examples():
    readme = Path(__file__).parents[1] / "README.md"
    namespace = {}
    for block in re.findall(r"```python\n(.*?)```", readme.read_text(), re.DOTALL):
        exec(compile(block, str(readme), "exec"), namespace)


def test_source_docstring_examples():
    assert doctest.testmod(_data).failed == 0
