# dataioc

**Declarative data dependency graphs for Python.**

Each `DataDescriptor` names a quantity and defines how it is derived from its direct dependencies. `DataIoC` composes these local rules into a graph, then resolves and caches only the subgraph required by the requested result. A provider binding replaces a quantity's source or derivation without changing downstream calculations.

[English](https://github.com/dyuu7/dataioc/blob/main/README.md) | [简体中文](https://github.com/dyuu7/dataioc/blob/main/README.zh-CN.md) | [Documentation](https://dyuu7.github.io/dataioc/) | [PyPI](https://pypi.org/project/dataioc/)

[![CI](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml/badge.svg)](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml)

## Example

This example calculates the cost of grid electricity for a building with a solar power system over one hour. During planning, solar power is estimated from irradiance. During operation, meter readings provide measured power. Both stages use the same grid energy and cost formulas.

The model assumes constant power throughout the hour and excludes battery storage and revenue from exported electricity. The panels cover 10 m² at 20% efficiency; the building's power demand is 3 kW, and grid electricity costs 1 CNY/kWh.

- Solar power (kW) = efficiency × panel area (m²) × irradiance (kW/m²).
- Grid energy (kWh) = max(load power − solar power, 0) × duration (h).
- Electricity cost (CNY) = grid energy × price (CNY/kWh).

`DataDescriptor` identifies a quantity in the model. For a derived quantity, its `__build__` method defines the calculation:

<img src="https://raw.githubusercontent.com/dyuu7/dataioc/main/docs/assets/data-flow.png" width="720" alt="During planning, SolarPower is derived from Irradiance and used to calculate GridEnergy and ElectricityCost. For operational analysis, a provider supplies measured SolarPower, replacing the derivation from irradiance while the remaining formulas stay unchanged." />

```python
from dataioc import DataDescriptor, DataIoC


class Irradiance(DataDescriptor):
    pass


class SolarPower(DataDescriptor):
    def __build__(self, data):
        efficiency = 0.2
        panel_area = 10.0  # m²
        return efficiency * panel_area * data[Irradiance]  # kW


class GridEnergy(DataDescriptor):
    def __build__(self, data):
        load_power = 3.0  # kW
        duration = 1.0  # h
        return max(load_power - data[SolarPower], 0.0) * duration  # kWh


class ElectricityCost(DataDescriptor):
    def __build__(self, data):
        price = 1.0  # CNY/kWh
        return data[GridEnergy] * price  # CNY


data = DataIoC().add(Irradiance, 0.8)  # kW/m²
assert round(data[ElectricityCost], 2) == 1.40
```

At an irradiance of 0.8 kW/m², the model yields 1.6 kW of solar power and a grid energy requirement of 1.4 kWh, at a cost of 1.4 CNY. The caller only needs to request `data[ElectricityCost]`; the container computes the required intermediate quantities from their dependencies and caches the results.

If the measured solar output during operation is 1.2 kW, a provider bound to `SolarPower` in a new container can supply this measurement in place of the estimate:

```python
measured = DataIoC().add_provider(SolarPower, lambda _: 1.2)  # kW
assert round(measured[ElectricityCost], 2) == 1.80
```

Using measured power, the grid energy requirement is 1.8 kWh, at a cost of 1.8 CNY. The container no longer requires `Irradiance`: the provider replaces the default derivation of `SolarPower`, while the calculation rules for `GridEnergy` and `ElectricityCost` remain unchanged. In an application, the provider may also read power data from a file or call another prediction model.

A container represents a fixed set of inputs and provider bindings and can manage multiple sensors or datasets through indices. Computed results are cached and are not automatically invalidated when inputs or provider bindings change; use a new container to recompute results after such changes. See [Core concepts](https://dyuu7.github.io/dataioc/concepts/) for dependency resolution, caching, and other runtime limits.

## When it helps

`dataioc` originated in [deinterf](https://github.com/dyuu7/deinterf), a magnetic interference compensation project. In that project, [field-direction quantities can be derived from magnetic sensor data or estimated by an inertial navigation system](https://github.com/dyuu7/deinterf/blob/main/examples/replace_direction_cosine_source_tmi.py), while the downstream compensation formulas need to be reused. The model therefore needs to distinguish the meaning of each quantity, its calculation dependencies, and the data source selected for each run.

`dataioc` generalizes this requirement into a data dependency container: the model defines local calculation rules for each quantity, and the application configures inputs and sources before requesting the required results. [aeromag-synth](https://github.com/dyuu7/aeromag-synth) uses the same approach in magnetic survey simulation.

Multiple sensors of the same type may also measure the same physical quantity. `dataioc` uses [indices](https://dyuu7.github.io/dataioc/indexed-data/) to distinguish data from separate acquisition channels, apply the same calculation rules to each sensor, and cache the corresponding results independently. Providers select derivation methods, while indices distinguish acquisition channels. These mechanisms can be combined, for example, to configure a separate calibration method for each sensor.

This approach suits scientific and engineering models that evolve through successive iterations, allowing different derivation methods and multiple measurement datasets to share calculation logic. Existing numerical functions can continue to perform the calculations, while the container organizes their data dependencies.

## Install

```bash
python -m pip install dataioc
python -m pip install "dataioc[numpy]"
```

## Documentation

- [Quickstart](https://dyuu7.github.io/dataioc/quickstart/): build a result from local dependency rules.
- [Core concepts](https://dyuu7.github.io/dataioc/concepts/): understand descriptors, builders, caching, and failure behavior.
- [Providers](https://dyuu7.github.io/dataioc/providers/): bind a quantity to another source or derivation.
- [Indexed data](https://dyuu7.github.io/dataioc/indexed-data/): reuse one model across related data groups.
- [NumPy](https://dyuu7.github.io/dataioc/numpy/): use array subclasses.
- [API](https://dyuu7.github.io/dataioc/api/): look up interfaces.

## Contributors

[yanang007](https://github.com/yanang007) wrote the original container implementation. [dyuu7](https://github.com/dyuu7) proposed the concept, handled the engineering work and extraction into `dataioc`, and maintains the project.

<a href="https://github.com/yanang007">
  <img src="https://wsrv.nl/?url=avatars.githubusercontent.com/u/8695716&amp;w=128&amp;h=128&amp;fit=cover&amp;mask=circle&amp;output=png"
       width="64" height="64" alt="yanang007" title="yanang007" />
</a>
<a href="https://github.com/dyuu7">
  <img src="https://wsrv.nl/?url=avatars.githubusercontent.com/u/49279922&amp;w=128&amp;h=128&amp;fit=cover&amp;mask=circle&amp;output=png"
       width="64" height="64" alt="dyuu7" title="dyuu7" />
</a>

Licensed under the [MIT License](https://github.com/dyuu7/dataioc/blob/main/LICENSE).
