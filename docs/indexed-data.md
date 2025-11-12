# Indexed data

Use `IndexedData` when one type represents several related data groups.

```python
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
```

Use an indexed reference when the dependency must stay fixed:

```python
class Offset(DataDescriptor[tuple[int, ...]]):
    def __build__(self, container: DataIoC) -> tuple[int, ...]:
        base = sum(container[Sensor[0]].values)
        return tuple(base + value for value in container[Sensor].values)
```

`Sensor[0]` is a strong reference to ID 0. `Sensor[1]` is a strong reference to ID 1. Ordinary types and `UniqueData` classes are shared across IDs.

See [API](api.md) for `IndexedData`, `UniqueData`, and the indexed container.
