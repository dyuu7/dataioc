# 快速开始

一个最小的模型由两部分组成：已经存在的数据，以及从直接依赖推导其他量的局部规则。请求结果时，容器会把这些规则连接起来。

## 1. 注册已有数据

已有的数据可以使用 `with_data` 或 `add` 注册。

```python
from dataioc import DataDescriptor, DataIoC


class RawReadings(DataDescriptor[tuple[int, ...]]):
    pass


container = DataIoC().add(RawReadings, (10, 20, 60))
```

## 2. 定义局部推导

每个描述符只请求自己需要的量，不需要另外写出全局求值顺序。

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

## 3. 请求结果

请求 `Report` 时，容器会解析 `Report -> Statistics -> Measurements -> RawReadings`。每个成功构建的值都会缓存在当前容器中。

```python
assert container[Report] == "mean=3, peak=6"
assert container[Report] == "mean=3, peak=6"  # 复用已缓存的结果。
```

## 4. 替换一个推导

Provider 可以改变一个量的获取方式，而使用它的代码仍然请求同一个键。

```python
recorded = DataIoC().add_provider(
    Measurements,
    lambda _: (2.0, 4.0, 12.0),
)
assert recorded[Report] == "mean=6, peak=12"
```

`recorded` 不需要 `RawReadings`，因为它的 provider 直接提供了可用的 `Measurements`。`Statistics` 和 `Report` 保持不变。如果替代实现还有自己的依赖或状态，可以在 provider 对象上定义 `__build__`，详见 [Provider](providers.zh.md)。

接下来阅读[核心概念](concepts.zh.md)或 [Provider](providers.zh.md)。
