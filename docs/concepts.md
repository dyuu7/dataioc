# Core concepts

`dataioc` separates three concerns: what a quantity means, how one implementation derives it, and which implementation a particular run uses. This is the data-oriented form of inversion of control.

## A quantity is a stable key

`DataDescriptor` identifies a quantity in the model. This page uses the solar electricity model from [Quickstart](quickstart.md): `Irradiance` represents solar irradiance, `SolarPower` represents solar output, `GridEnergy` represents purchased electricity, and `ElectricityCost` represents its cost. Panel area, efficiency, load power, duration, and price are the same as in the README.

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
```

A descriptor is the container key, not the stored value itself. It may carry hashable parameters so that one descriptor class can identify related values. Do not mutate a descriptor after registration, because its parameters participate in equality and hashing.

## A builder is a local rule

A builder defines how to calculate a quantity from its direct dependencies. For example, `ElectricityCost` depends only on `GridEnergy`. The derivation of grid energy from solar power belongs to `GridEnergy`, and the derivation of solar power from irradiance belongs to `SolarPower`.

A builder can be:

- a `__build__` method on a descriptor or provider object;
- a callable accepting one `DataIoC` argument;
- a class with a suitable `__build__` method.

Dependencies are requested with `data[Target]`. These requests are ordinary Python, so a builder can use conditions, loops, libraries, or existing domain objects.

## Requests form the graph

```python
data = DataIoC().add(Irradiance, 0.8)  # kW/m²
assert round(data[ElectricityCost], 2) == 1.40
```

Requesting `ElectricityCost` forms and resolves `ElectricityCost → GridEnergy → SolarPower → Irradiance`. The graph is implicit in the local rules and is expanded only as far as the requested result requires. Callers do not maintain a separate list of steps or execution order.

`dataioc` resolves dependencies and executes calculations synchronously within the current process. It organizes data dependencies and does not provide workflow scheduling.

## Register values and implementations

| Operation | Meaning |
| --- | --- |
| `with_data(*values)` | Register existing instances by type; indexed instances keep their descriptors |
| `add(Target)` | Register the target's own lazy builder |
| `add(Target, value)` | Register an existing value other than `None` |
| `data[Target] = value` | Set a value directly, including an explicit `None` |
| `add_provider(Target, provider)` | Bind the target to another builder |

By default, the container discovers a target's own builder on first access. Strict mode requires every requested key to have data or a registered builder:

```python
strict = DataIoC(allow_implicit_registering=False)
strict.add(ElectricityCost).add(GridEnergy).add(SolarPower)
strict.add(Irradiance, 0.8)
assert round(strict[ElectricityCost], 2) == 1.40
```

`add(Target, None)` selects builder registration because `None` is the method's default argument. Use item assignment to store `None` as a value.

See [Providers](providers.md) for choosing another implementation at container assembly time.

## Container lifetime and cache

Each successfully built key is cached, including a value of `None`. Repeated requests within one container therefore share the same result. Different indexed keys have separate cache entries; ordinary types and `UniqueData` are shared across IDs.

A container represents a fixed set of inputs and provider bindings and can manage multiple sensors or datasets through indices. Changes to inputs or bindings do not automatically invalidate existing results; use a new container to recompute results after such changes. Providers select sources or derivation methods, while indices distinguish data groups; see [Indexed data](indexed-data.md).

## Failure and diagnostics

Failed builds are not cached; dependencies that completed successfully remain cached. A failed top-level build prints its dependency tree and re-raises the original exception. After supplying missing data or fixing the builder, the target can be requested again.

Successful access trees are normally cleared. Set `record_all=True` to retain them in `data.logger`; see [Provider diagnostics](providers.md#diagnostics).

The container does not provide thread safety, asynchronous construction, automatic dependent invalidation, or cycle detection.
