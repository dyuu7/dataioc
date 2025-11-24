# Providers

## Register a provider

```python
from dataclasses import dataclass

from dataioc import DataDescriptor, DataIoC, IndexedData


@dataclass
class Sensor(IndexedData):
    values: tuple[int, ...]


class Total(DataDescriptor[int]):
    def __build__(self, container: DataIoC) -> int:
        return sum(container[Sensor].values)


container = DataIoC().add_provider(Sensor, lambda _: Sensor((1, 2, 3)))
assert container[Total] == 6
```

The provider is called on the first uncached request for `Sensor`. Providers can be callables or objects with `__build__`; their results are cached just like other built values.

## Override one indexed key

```python
container.add_provider(Sensor[1], lambda _: Sensor((10, 20, 30)))
assert container[Total[1]] == 60
assert container[Total[2]] == 6
```

The ID-specific provider takes precedence for `Sensor[1]`. An `IndexedData` class provider is the fallback for its other IDs; a provider registered with a descriptor applies only to that key. ID 0 is also used by an unindexed top-level class read, so a `Sensor[0]` provider takes precedence over `Sensor` there.

Weak dependencies requested by a provider inherit the requested target ID. Explicitly indexed dependencies keep their ID; see [Indexed data](indexed-data.md).

## Replace a provider

Register replacements before the target's first access. Repeated registration replaces the builder for future uncached reads, but existing cached values and dependents are retained. Configure a fresh container to recompute a result with another source.

## Provider objects

```python
class EstimatedSensor:
    def __build__(self, container: DataIoC) -> Sensor:
        return Sensor((10, 20, 30))


estimated = DataIoC().add_provider(Sensor, EstimatedSensor())
assert estimated[Total] == 60
```

Use a provider object when the replacement has its own dependencies or state.

## Diagnostics

```python
container = DataIoC(record_all=True)
container.add_provider(Sensor, lambda _: Sensor((1, 2, 3)))
assert container[Total] == 6
print(container.logger)
```

The logger shows nested dependencies, newly created values, provider substitutions, and failures. With `record_all=False`, successful access trees are cleared. A failing top-level build prints the dependency tree and re-raises the original exception. You can clear retained records with `container.logger.clear()`.
