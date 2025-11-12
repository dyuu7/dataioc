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

The supported range is `numpy>=1.26,<3`, including NumPy 1.26 and 2.x. The resolver selects the newest release compatible with the Python version.

`DataNDArray` preserves its subclass for shape-preserving ufunc results when the result dtype is compatible. Multiple-output ufuncs, explicit `out` arrays, and in-place operations are supported.

Slicing, reshaping, and scalar indexing follow the documented behavior in the [API reference](api.md). Numerical promotion follows the installed NumPy version, so result dtypes may differ between NumPy 1.x and 2.x.
