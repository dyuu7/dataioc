# NumPy support

This page extends the individual irradiance readings in [Indexed data](indexed-data.md) to arrays of hourly values. It retains the `Irradiance → SolarPower → GridEnergy → ElectricityCost` model and adds `TotalElectricityCost` for the full period.

Install the optional extra:

```bash
python -m pip install "dataioc[numpy]"
```

## Calculate hourly electricity costs

Each array element represents constant power conditions over one hour, with irradiance in kW/m². The two arrays represent two irradiance sensors, with matching time positions. Panel area is 10 m², efficiency is 20%, load power is 3 kW, and electricity costs 1 CNY/kWh. Battery storage and revenue from exported electricity are excluded.

`Irradiance` subclasses `DataNDArray`, allowing indexed arrays to be registered with `with_data`. The formulas operate element by element, with `np.maximum` replacing `max` from the scalar model:

```python
import numpy as np

from dataioc import DataDescriptor, DataIoC, DataNDArray


class Irradiance(DataNDArray):
    pass


class SolarPower(DataDescriptor[np.ndarray]):
    def __build__(self, data: DataIoC) -> np.ndarray:
        efficiency = 0.2
        panel_area = 10.0  # m²
        return efficiency * panel_area * np.asarray(data[Irradiance])  # kW


class GridEnergy(DataDescriptor[np.ndarray]):
    def __build__(self, data: DataIoC) -> np.ndarray:
        load_power = 3.0  # kW
        duration = 1.0  # h per element
        return np.maximum(load_power - data[SolarPower], 0.0) * duration  # kWh


class ElectricityCost(DataDescriptor[np.ndarray]):
    def __build__(self, data: DataIoC) -> np.ndarray:
        price = 1.0  # CNY/kWh
        return data[GridEnergy] * price  # CNY per element


class TotalElectricityCost(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        return float(data[ElectricityCost].sum())


data = DataIoC().with_data(
    Irradiance([0.8, 0.6, 0.0]),
    Irradiance[1]([0.6, 0.4, 0.0]),
)
np.testing.assert_allclose(data[ElectricityCost[0]], [1.4, 1.8, 3.0])
np.testing.assert_allclose(data[ElectricityCost[1]], [1.8, 2.2, 3.0])
assert round(data[TotalElectricityCost[0]], 2) == 6.20
assert round(data[TotalElectricityCost[1]], 2) == 7.00
```

Indices distinguish sensors, while array elements distinguish time periods. The first input gives the same first-hour cost of 1.4 CNY as the README. Irradiance is zero in the third hour, so the grid supplies all electricity at a cost of 3 CNY. The two sets of readings produce three-hour totals of 6.2 CNY and 7 CNY.

`SolarPower` uses `np.asarray` to perform calculations on an ordinary array; each derived array is identified by its own descriptor. Once `TotalElectricityCost` has been requested, hourly costs and their dependencies are also cached and available for reuse.

## Use an array of measured power

Providers work in the same way as in the scalar model. Measured power for the corresponding three hours can replace `SolarPower` directly:

```python
measured = DataIoC().add_provider(
    SolarPower,
    lambda _: np.array([1.2, 1.0, 0.0]),  # kW
)
np.testing.assert_allclose(measured[ElectricityCost], [1.8, 2.0, 3.0])
assert round(measured[TotalElectricityCost], 2) == 6.80
```

No irradiance array is required, and the grid energy and cost formulas are reused. The three hourly costs are 1.8 CNY, 2 CNY, and 3 CNY, totaling 6.8 CNY.

Array lengths, time alignment, and units are conventions of the model code; the container does not align time series automatically. Use a new container when different data or provider bindings require recomputation; see [Core concepts](concepts.md) for caching behavior.

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
