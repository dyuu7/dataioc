# Providers

A provider binds a quantity to a specific source or derivation method. This page extends the solar electricity model from [Quickstart](quickstart.md) with measured data, an alternative formula with its own dependencies, and configuration for one acquisition channel. Execute the code blocks in order.

## Replace an estimate with a measurement

The default model estimates solar power from irradiance, then calculates grid energy and cost for one hour. Panel area, efficiency, load power, and price are the same as in the README:

```python
from dataioc import DataDescriptor, DataIoC


class Irradiance(DataDescriptor[float]):
    pass


class SolarPower(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        efficiency = 0.2
        panel_area = 10.0  # m²
        return efficiency * panel_area * data[Irradiance]  # kW


class GridEnergy(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        load_power = 3.0  # kW
        duration = 1.0  # h
        return max(load_power - data[SolarPower], 0.0) * duration  # kWh


class ElectricityCost(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        price = 1.0  # CNY/kWh
        return data[GridEnergy] * price  # CNY


estimated = DataIoC().add(Irradiance, 0.8)  # kW/m²
assert round(estimated[ElectricityCost], 2) == 1.40
```

`GridEnergy` depends on the power value identified by `SolarPower`. A provider bound to that key can supply a measurement of 1.2 kW:

```python
measured = DataIoC().add_provider(SolarPower, lambda _: 1.2)  # kW
assert round(measured[ElectricityCost], 2) == 1.80
```

This container requires no `Irradiance`. The provider replaces the default derivation at `SolarPower`, while the grid energy and cost formulas are reused. The cost changes from 1.4 to 1.8 CNY. An existing fixed value can also be registered directly with `DataIoC().add(SolarPower, 1.2)`; providers support reading data or running alternative calculations on demand.

## Declare dependencies for an alternative formula

Planning analysis may also account for losses in the estimated output. Here the dimensionless `LossFactor` represents the fraction of power retained; a value of 0.75 retains 75% of the original estimate.

```python
class LossFactor(DataDescriptor[float]):
    pass


class LossAdjustedSolarPower:
    def __build__(self, data: DataIoC) -> float:
        efficiency = 0.2
        panel_area = 10.0  # m²
        return efficiency * panel_area * data[Irradiance] * data[LossFactor]


adjusted = (
    DataIoC()
    .add(Irradiance, 0.8)
    .add(LossFactor, 0.75)
    .add_provider(SolarPower, LossAdjustedSolarPower())
)
assert round(adjusted[SolarPower], 2) == 1.20
assert round(adjusted[ElectricityCost], 2) == 1.80
```

The derivation is now `Irradiance + LossFactor → SolarPower`. The provider requests its direct dependencies through the container, while `GridEnergy` and `ElectricityCost` remain unchanged. The alternative implementation should request its inputs; requesting `SolarPower` itself while building `SolarPower` would create a circular dependency.

A provider can be a callable accepting the container, an object with `__build__`, or a class with a suitable `__build__` method. Provider objects may carry state, and successfully built results are cached per key.

## Configure a derivation for one acquisition channel

Two irradiance sensors can supply separate inputs to the same grid electricity model. Index 0 uses the default formula, while index 1 uses the formula with a loss adjustment. All other model parameters are identical:

```python
indexed = (
    DataIoC()
    .add(Irradiance[0], 0.8)
    .add(Irradiance[1], 0.6)
    .add(LossFactor[1], 0.75)
    .add_provider(SolarPower[1], LossAdjustedSolarPower())
)
assert round(indexed[ElectricityCost[0]], 2) == 1.40
assert round(indexed[ElectricityCost[1]], 2) == 2.10
```

Each provider binding applies only to its specified key. A request for `ElectricityCost[1]` propagates index 1 through the dependencies. Within the provider, `Irradiance` and `LossFactor` resolve to `Irradiance[1]` and `LossFactor[1]`, respectively, giving 0.9 kW of solar power and a cost of 2.1 CNY. Index 0 still uses the default derivation.

Providers select sources or derivation methods, while indices distinguish acquisition channels. Descriptor dependencies requested inside a provider inherit the target's current index unless they specify an explicit index. See [Indexed data](indexed-data.md).

## Configure before resolving

Register providers before the target's first access. Repeated registration replaces the builder used by future uncached requests, but does not invalidate existing results or their cached dependents. Use a new container to recompute results after changes to inputs or bindings.

## Diagnostics

```python
diagnostic = DataIoC(record_all=True)
diagnostic.add_provider(SolarPower, lambda _: 1.2)
assert round(diagnostic[ElectricityCost], 2) == 1.80
print(diagnostic.logger)
```

The logger shows nested dependencies, constructed results, provider substitutions, and failures. With `record_all=False`, successful access trees are cleared; setting `record_all=True` retains them. A failing top-level build prints the dependency tree and re-raises the original exception. Clear retained records with `diagnostic.logger.clear()`.
