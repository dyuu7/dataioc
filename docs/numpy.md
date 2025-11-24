# NumPy support

Install the optional extra:

```bash
python -m pip install "dataioc[numpy]"
```

Define an array type by subclassing `DataNDArray`:

```python
from dataioc import DataIoC, DataNDArray


class SensorArray(DataNDArray):
    pass


container = DataIoC().with_data(
    SensorArray([1, 1, 1]),
    SensorArray[1]([2, 2, 2]),
)
assert container[SensorArray[1]].sum() == 6
```

## Compatibility

The supported range is `numpy>=1.26,<3`. Python 3.9 supports NumPy 1.26 and 2.0; newer NumPy releases require newer Python versions. Package installers select a compatible release.

CI tests NumPy 1.26.0, the latest 1.26 release, 2.0.0, and the latest stable 2.x, alongside the locked dependencies across Python 3.9 through 3.14.

## Array behavior

| Operation | Behavior |
| --- | --- |
| Multiple input arrays | Check sample counts, then stack columns |
| Shape-preserving numerical ufunc | Retain the subclass when the result dtype is compatible |
| Multiple-output ufunc | Apply the subclass rule separately to each result |
| Explicit `out` or in-place operation | Preserve the output object's identity |
| Slicing or reshaping | Return a plain NumPy array |
| Scalar indexing or reduction | Follow NumPy's scalar conventions |

Numerical promotion and overflow behavior follow the installed NumPy version, so result dtypes can differ between 1.x and 2.x.

Neither the core import nor `from dataioc import *` imports NumPy. Explicitly importing `DataNDArray` loads the optional integration; it requires NumPy to be installed.

See the [API reference](api.md) for signatures.
