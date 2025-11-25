# 索引数据

一个类型表示多组相关数据时，使用 `IndexedData`。依赖默认继承当前数据组，因此同一套 `RawReadings -> Measurements -> Statistics -> Report` 模型可以用于多个传感器或实验。

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

这里用 ID 0 和 1 表示两个传感器的读数。未索引的依赖在构建过程中是弱引用，会继承当前构建描述符的 ID。因此，每一层都会自动跟随同一个传感器，无需重复书写 ID：

```python
assert container[Report[0]] == "mean=3, peak=6"
assert container[Report[1]] == "mean=6, peak=12"
assert container[RawReadings] is container[RawReadings[0]]
```

在构建之外，未索引的 `RawReadings` 表示 ID 0。`RawReadings[1](...)` 创建的值会携带对应描述符，`with_data` 再将其中的数据注册到该键下。

## 显式引用一个数据组

某一部分计算必须固定时，使用带索引的依赖。下面的派生量将当前组的测量值与第 0 组比较：

```python
class DifferenceFromBaseline(DataDescriptor[tuple[float, ...]]):
    def __build__(self, container: DataIoC) -> tuple[float, ...]:
        baseline = container[Measurements[0]]
        current = container[Measurements]
        return tuple(value - base for value, base in zip(current, baseline))


assert container[DifferenceFromBaseline[0]] == (0.0, 0.0, 0.0)
assert container[DifferenceFromBaseline[1]] == (1.0, 2.0, 6.0)
```

`Measurements[0]` 是强引用，始终选择第 0 组；未索引的 `Measurements` 仍是弱引用，会跟随 `DifferenceFromBaseline` 的 ID。

## 重新绑定描述符

`index_implicit(id)` 保留已有的强 ID。下标操作会显式重新绑定描述符，原描述符不变：

```python
original = Report[1]
assert original.index_implicit(2) is original
assert original[2].id == 2
assert original.id == 1
```

## 跨数据组共享

普通 Python 类型在所有构建 ID 之间共享。索引类也只需要一个共享值时，混入 `UniqueData`：

```python
@dataclass
class Calibration(IndexedData, UniqueData):
    scale: float


container.with_data(Calibration(0.1))
assert container[Calibration[1]] is container[Calibration[2]]
```

成功构建的值按键缓存。Provider 变更不会使已有的下游缓存失效，详见[容器生命周期与缓存](concepts.zh.md)。

`IndexedData`、`UniqueData` 和索引容器见 [API](api.zh.md)。
