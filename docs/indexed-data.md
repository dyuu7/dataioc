# Indexed data

Use `IndexedData` when one type represents several related data groups.

```python
from dataclasses import dataclass

from dataioc import DataDescriptor, DataIoC, IndexedData, UniqueData


@dataclass
class Sensor(IndexedData):
    values: tuple[int, ...]


container = DataIoC().with_data(
    Sensor((1, 1, 1)),
    Sensor[1]((2, 2, 2)),
)
```

An unindexed reference is weak inside a build. It inherits the ID of the descriptor currently being built:

```python
class Total(DataDescriptor[int]):
    def __build__(self, container: DataIoC) -> int:
        return sum(container[Sensor].values)


assert container[Total[0]] == 3
assert container[Total[1]] == 6
assert container[Sensor] is container[Sensor[0]]
```

Use an indexed reference when the dependency must stay fixed:

```python
class Offset(DataDescriptor[tuple[int, ...]]):
    def __build__(self, container: DataIoC) -> tuple[int, ...]:
        base = sum(container[Sensor[0]].values)
        return tuple(base + value for value in container[Sensor].values)


assert container[Offset[0]] == (4, 4, 4)
assert container[Offset[1]] == (5, 5, 5)
```

`Sensor[0]` is a strong reference to ID 0. `Sensor[1]` is a strong reference to ID 1. Outside a build, an unindexed `Sensor` refers to ID 0. Indexed values are wrapped with their descriptors when created as `Sensor[1](...)`; `with_data` registers the underlying values under those keys.

## Rebind a descriptor

`index_implicit(id)` preserves an existing strong ID. Subscription explicitly rebinds the descriptor and leaves the original unchanged:

```python
original = Total[1]
assert original.index_implicit(2) is original
assert original[2].id == 2
assert original.id == 1
```

## Share data across IDs

Ordinary Python types are shared across build IDs. Mix `UniqueData` into an indexed class when it should also have one shared value:

```python
@dataclass
class Calibration(IndexedData, UniqueData):
    offset: int


container.with_data(Calibration(10))
assert container[Calibration[1]] is container[Calibration[2]]
```

Successfully built values are cached per key. Provider changes do not invalidate cached dependents; see [Cache](concepts.md#cache).

See [API](api.md) for `IndexedData`, `UniqueData`, and the indexed container.
