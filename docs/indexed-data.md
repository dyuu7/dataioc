# Indexed data

Use `IndexedData` when one type represents several related data groups. Dependencies inherit the current group by default, so the same `RawReadings -> Measurements -> Statistics -> Report` model can be applied to several sensors or experiments.

```python
from dataclasses import dataclass

from dataioc import DataDescriptor, DataIoC, IndexedData, UniqueData


@dataclass
class RawReadings(IndexedData):
    values: tuple[int, ...]


class Measurements(DataDescriptor[tuple[float, ...]]):
    def __build__(self, container: DataIoC) -> tuple[float, ...]:
        return tuple(value / 10 for value in container[RawReadings].values)


class Statistics(DataDescriptor[tuple[float, float]]):
    def __build__(self, container: DataIoC) -> tuple[float, float]:
        values = container[Measurements]
        return sum(values) / len(values), max(values)


class Report(DataDescriptor[str]):
    def __build__(self, container: DataIoC) -> str:
        mean, peak = container[Statistics]
        return f"mean={mean:g}, peak={peak:g}"


container = DataIoC().with_data(
    RawReadings((10, 20, 60)),
    RawReadings[1]((20, 40, 120)),
)
```

Here IDs 0 and 1 represent readings from two sensors. An unindexed dependency is weak inside a build: it inherits the ID of the descriptor currently being built. Every layer therefore follows the same sensor without repeating the ID:

```python
assert container[Report[0]] == "mean=3, peak=6"
assert container[Report[1]] == "mean=6, peak=12"
assert container[RawReadings] is container[RawReadings[0]]
```

Outside a build, an unindexed `RawReadings` refers to ID 0. Values created as `RawReadings[1](...)` are wrapped with their descriptor, and `with_data` registers the underlying value under that key.

## Refer to one group explicitly

Use an indexed dependency when one part of a calculation must stay fixed. This derived value compares the current group's measurements with group 0:

```python
class DifferenceFromBaseline(DataDescriptor[tuple[float, ...]]):
    def __build__(self, container: DataIoC) -> tuple[float, ...]:
        baseline = container[Measurements[0]]
        current = container[Measurements]
        return tuple(value - base for value, base in zip(current, baseline))


assert container[DifferenceFromBaseline[0]] == (0.0, 0.0, 0.0)
assert container[DifferenceFromBaseline[1]] == (1.0, 2.0, 6.0)
```

`Measurements[0]` is a strong reference and always selects group 0. The unindexed `Measurements` remains weak and follows the ID of `DifferenceFromBaseline`.

## Rebind a descriptor

`index_implicit(id)` preserves an existing strong ID. Subscription explicitly rebinds the descriptor and leaves the original unchanged:

```python
original = Report[1]
assert original.index_implicit(2) is original
assert original[2].id == 2
assert original.id == 1
```

## Share data across groups

Ordinary Python types are shared across build IDs. Mix `UniqueData` into an indexed class when it should also have one shared value:

```python
@dataclass
class Calibration(IndexedData, UniqueData):
    scale: float


container.with_data(Calibration(0.1))
assert container[Calibration[1]] is container[Calibration[2]]
```

Successfully built values are cached per key. Provider changes do not invalidate cached dependents; see [Container lifetime and cache](concepts.md#container-lifetime-and-cache).

See [API](api.md) for `IndexedData`, `UniqueData`, and the indexed container.
