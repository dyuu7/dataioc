# Quickstart

This guide develops the README's solar electricity model in four steps: registering data, defining formulas, requesting results, and replacing a source. Each guide is self-contained; execute the code blocks within a page in order.

The model calculates grid electricity cost over one hour, assuming constant power and excluding battery storage and revenue from exported electricity. The panels cover 10 m² at 20% efficiency; the building's power demand is 3 kW, and electricity costs 1 CNY/kWh.

## 1. Register irradiance data

`Irradiance` identifies solar irradiance in kW/m². Register an existing value under this key with `add`:

```python
from dataioc import DataDescriptor, DataIoC


class Irradiance(DataDescriptor[float]):
    pass


data = DataIoC().add(Irradiance, 0.8)  # kW/m²
```

The `float` in `DataDescriptor[float]` specifies the quantity's value type. The README omits type annotations; both forms have the same runtime behavior. Data objects with their own types or indices can also be registered with `with_data`; see [Indexed data](indexed-data.md).

## 2. Define the formulas

- Solar power (kW) = efficiency × panel area (m²) × irradiance (kW/m²).
- Grid energy (kWh) = max(load power − solar power, 0) × duration (h).
- Electricity cost (CNY) = grid energy × price (CNY/kWh).

Each derived quantity's `__build__` method requests only its direct dependencies:

```python
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
```

## 3. Request electricity cost

A request for `ElectricityCost` resolves dependencies along `ElectricityCost → GridEnergy → SolarPower → Irradiance` and computes the required results. Each successfully built value is cached in the current container.

```python
assert round(data[ElectricityCost], 2) == 1.40
assert round(data[SolarPower], 2) == 1.60
assert round(data[GridEnergy], 2) == 1.40
```

At an irradiance of 0.8 kW/m², solar power is 1.6 kW, grid energy is 1.4 kWh, and the cost is 1.4 CNY. Subsequent requests for `SolarPower` and `GridEnergy` return the cached intermediate results.

## 4. Use measured power

If measured solar power is 1.2 kW, bind a provider to `SolarPower` in a new container:

```python
measured = DataIoC().add_provider(SolarPower, lambda _: 1.2)  # kW
assert round(measured[ElectricityCost], 2) == 1.80
```

`measured` requires no `Irradiance`, since the provider supplies solar power directly. The formulas for `GridEnergy` and `ElectricityCost` remain unchanged, giving 1.8 kWh of grid energy at a cost of 1.8 CNY.

A container represents a fixed set of inputs and provider bindings and can manage multiple sensors or datasets through indices. Changes to inputs or bindings do not automatically invalidate existing results; use a new container to recompute results after such changes.

Continue with [Core concepts](concepts.md) for graph resolution and caching, or [Providers](providers.md) to configure an alternative derivation of solar power with its own dependencies.
