# NumPy support

Install the optional extra:

```bash
python -m pip install "dataioc[numpy]"
```

The same measurement model can use a NumPy-backed `RawReadings` type by subclassing `DataNDArray`:

```python
from dataioc import DataDescriptor, DataIoC, DataNDArray


class RawReadings(DataNDArray):
    pass


class Measurements(DataDescriptor):
    def __build__(self, container: DataIoC):
        return container[RawReadings] / 10


class Statistics(DataDescriptor):
    def __build__(self, container: DataIoC):
        values = container[Measurements]
        return values.mean(), values.max()


class Report(DataDescriptor):
    def __build__(self, container: DataIoC):
        mean, peak = container[Statistics]
        return f"mean={mean:g}, peak={peak:g}"


container = DataIoC().with_data(
    RawReadings([10, 20, 60]),
    RawReadings[1]([20, 40, 120]),
)
assert container[Report] == "mean=3, peak=6"
assert container[Report[1]] == "mean=6, peak=12"
```

Only the leaf representation and numerical operations change. The four model roles and indexed dependency behavior remain the same as in the other guides.

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
