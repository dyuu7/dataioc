# 索引数据

一个类型表示多组相关数据时，使用 `IndexedData`。

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

未索引的引用在构建过程中是弱引用，会继承当前构建描述符的 ID：

```python
class Total(DataDescriptor[int]):
    def __build__(self, container: DataIoC) -> int:
        return sum(container[Sensor].values)


assert container[Total[0]] == 3
assert container[Total[1]] == 6
assert container[Sensor] is container[Sensor[0]]
```

依赖必须保持固定时，使用带索引的引用：

```python
class Offset(DataDescriptor[tuple[int, ...]]):
    def __build__(self, container: DataIoC) -> tuple[int, ...]:
        base = sum(container[Sensor[0]].values)
        return tuple(base + value for value in container[Sensor].values)


assert container[Offset[0]] == (4, 4, 4)
assert container[Offset[1]] == (5, 5, 5)
```

`Sensor[0]` 是指向 ID 0 的强引用，`Sensor[1]` 是指向 ID 1 的强引用。顶层读取时，未索引的 `Sensor` 表示 ID 0。`Sensor[1](...)` 会把实例与其描述符包装在一起；`with_data` 将其中的数据注册到对应键下。

## 重新绑定描述符

`index_implicit(id)` 保留已有的强 ID。下标操作会显式重新绑定描述符，原描述符不变：

```python
original = Total[1]
assert original.index_implicit(2) is original
assert original[2].id == 2
assert original.id == 1
```

## 跨 ID 共享数据

普通 Python 类型在所有构建 ID 之间共享。索引类也只需要一个共享值时，混入 `UniqueData`：

```python
@dataclass
class Calibration(IndexedData, UniqueData):
    offset: int


container.with_data(Calibration(10))
assert container[Calibration[1]] is container[Calibration[2]]
```

成功构建的值按键缓存。Provider 变更不会使已有的下游缓存失效，详见[缓存](concepts.zh.md)。

`IndexedData`、`UniqueData` 和索引容器见 [API](api.zh.md)。
