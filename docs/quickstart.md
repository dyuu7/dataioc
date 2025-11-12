# Quickstart

## 1. Provide source data

Use `with_data` for values that already exist.

```python
from dataclasses import dataclass

from dataioc import DataDescriptor, DataIoC, IndexedData


@dataclass
class Sensor(IndexedData):
    values: tuple[int, ...]


class Total(DataDescriptor[int]):
    def __build__(self, container: DataIoC) -> int:
        return sum(container[Sensor].values)


container = DataIoC().with_data(Sensor((1, 2, 3)))
```

## 2. Define a derived value

Implement `__build__` and request the descriptor.

```python
assert container[Total] == 6
assert container[Total] == 6  # The second access uses the cache.
```

The container builds `Total` only on its first access. Its dependency, `Sensor`, is requested inside the builder.

## 3. Provide a computed source

Use a provider when a value should be calculated or replaced at runtime.

```python
alternative = DataIoC().add_provider(Sensor, lambda _: Sensor((10, 20, 30)))
assert alternative[Total] == 60
```

For objects with dependencies, define `__build__` instead of using a lambda.

```python
class EstimatedSensor:
    def __build__(self, container: DataIoC) -> Sensor:
        return Sensor((10, 20, 30))


alternative = DataIoC().add_provider(Sensor, EstimatedSensor())
```

Continue with [Core concepts](concepts.md) or [Providers](providers.md).
