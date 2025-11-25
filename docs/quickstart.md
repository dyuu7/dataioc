# Quickstart

The smallest useful model has two parts: values that already exist, and local rules for deriving other values. The container connects those rules when a result is requested.

## 1. Register an existing value

Use `with_data` or `add` for a value that is already available.

```python
from dataioc import DataDescriptor, DataIoC


class RawReadings(DataDescriptor[tuple[int, ...]]):
    pass


container = DataIoC().add(RawReadings, (10, 20, 60))
```

## 2. Define local derivations

Each descriptor requests only the values it needs. There is no global execution order to write down.

```python
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
```

## 3. Request the result

Requesting `Report` causes the container to resolve `Report -> Statistics -> Measurements -> RawReadings`. Each successful value is cached in that container.

```python
assert container[Report] == "mean=3, peak=6"
assert container[Report] == "mean=3, peak=6"  # Reuses the cached result.
```

## 4. Replace one derivation

A provider changes how a quantity is obtained while its consumers keep requesting the same key.

```python
recorded = DataIoC().add_provider(
    Measurements,
    lambda _: (2.0, 4.0, 12.0),
)
assert recorded[Report] == "mean=6, peak=12"
```

`recorded` does not need `RawReadings`, because its provider supplies ready-to-use `Measurements`. `Statistics` and `Report` are unchanged. For a provider with its own dependencies or state, define `__build__` on a provider object; see [Providers](providers.md).

Continue with [Core concepts](concepts.md) or [Providers](providers.md).
