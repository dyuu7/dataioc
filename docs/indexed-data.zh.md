# 索引数据

一个类型表示多组相关数据时，使用 `IndexedData`。

```python
container = DataIoC().with_data(
    Sensor((1, 1, 1)),
    Sensor[1]((2, 2, 2)),
)
```

未索引的引用在构建过程中是弱引用，会继承当前构建描述符的 ID：

```python
class Total(DataDescriptor[int]):
    def __build__(self, container: DataIoC) -> int:
        return sum(container[Sensor].values)


assert container[Total[0]] == 3
assert container[Total[1]] == 6
```

依赖必须保持固定时，使用带索引的引用：

```python
class Offset(DataDescriptor[tuple[int, ...]]):
    def __build__(self, container: DataIoC) -> tuple[int, ...]:
        base = sum(container[Sensor[0]].values)
        return tuple(base + value for value in container[Sensor].values)
```

`Sensor[0]` 是指向 ID 0 的强引用，`Sensor[1]` 是指向 ID 1 的强引用。普通类型和混入`UniqueData` 的类会在不同 ID 之间共享。

`IndexedData`、`UniqueData` 和索引容器见 [API](api.zh.md)。
