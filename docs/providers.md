# Providers

A provider binds a stable quantity to a concrete source or derivation. The binding belongs to container assembly, while downstream code keeps depending on the quantity itself.

## Keep consumers independent of the source

```python
from dataioc import DataDescriptor, DataIoC


class RawReadings(DataDescriptor[tuple[int, ...]]):
    pass


class Measurements(DataDescriptor[tuple[float, ...]]):
    def __build__(self, container: DataIoC) -> tuple[float, ...]:
        return tuple(value / 10 for value in container[RawReadings])


class Statistics(DataDescriptor[tuple[float, float]]):
    def __build__(self, container: DataIoC) -> tuple[float, float]:
        values = container[Measurements]
        return sum(values) / len(values), max(values)


class Report(DataDescriptor[str]):
    def __build__(self, container: DataIoC) -> str:
        mean, peak = container[Statistics]
        return f"mean={mean:g}, peak={peak:g}"


live = DataIoC().add(RawReadings, (10, 20, 60))
assert live[Report] == "mean=3, peak=6"
```

`Statistics` depends on the concept `Measurements`, not on where the values came from. A provider can supply recorded measurements under the same key:

```python
recorded = DataIoC().add_provider(
    Measurements,
    lambda _: (2.0, 4.0, 12.0),
)
assert recorded[Report] == "mean=6, peak=12"
```

`recorded` needs no `RawReadings`. The provider replaces the upstream path at `Measurements`; `Statistics` and `Report` are unchanged.

## Give a provider its own dependencies

A provider can define another local derivation instead of returning a fixed or loaded value:

```python
class Calibration(DataDescriptor[float]):
    pass


class CalibratedMeasurements:
    def __build__(self, container: DataIoC) -> tuple[float, ...]:
        scale = container[Calibration]
        return tuple(value * scale for value in container[RawReadings])


calibrated = (
    DataIoC()
    .add(RawReadings, (10, 20, 60))
    .add(Calibration, 0.2)
    .add_provider(Measurements, CalibratedMeasurements())
)
assert calibrated[Report] == "mean=6, peak=12"
```

The alternative path is now `RawReadings + Calibration -> Measurements`. Provider objects can carry state and request dependencies through the same container. This lets `Measurements` keep a stable identity while recorded, simulated, calibrated, and estimated implementations vary between runs.

Providers can be callables, objects with `__build__`, or classes with a suitable `__build__` method. Their results are resolved lazily and cached like other built values.

## Bind one indexed quantity

```python
indexed = DataIoC().add_provider(
    Measurements[1],
    lambda _: (2.0, 4.0, 12.0),
)
indexed.add_provider(
    Measurements[2],
    lambda _: (1.0, 2.0, 6.0),
)

assert indexed[Report[1]] == "mean=6, peak=12"
assert indexed[Report[2]] == "mean=3, peak=6"
```

Each descriptor provider applies only to that key. Dependencies without an explicit ID inherit the ID being built, so `Report[1]` reaches `Measurements[1]` and `Report[2]` reaches `Measurements[2]`.

Weak dependencies requested inside a provider inherit the target's current ID. Explicitly indexed dependencies keep their ID; see [Indexed data](indexed-data.md).

## Configure before resolving

Register providers before the target's first access. Repeated registration replaces the builder used by future uncached requests, but it does not invalidate existing cached values or their dependents. Use a fresh container to evaluate the model with another set of bindings.

## Diagnostics

```python
diagnostic = DataIoC(record_all=True)
diagnostic.add_provider(Measurements, lambda _: (1.0, 2.0, 6.0))
assert diagnostic[Report] == "mean=3, peak=6"
print(diagnostic.logger)
```

The logger shows nested dependencies, constructed values, provider substitutions, and failures. With `record_all=False`, successful access trees are cleared. A failing top-level build prints the dependency tree and re-raises the original exception. Clear retained records with `container.logger.clear()`.
