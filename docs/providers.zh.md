# Provider

Provider 将一个稳定的数据量绑定到具体来源或推导方式。绑定发生在容器组装时，下游代码始终依赖数据量本身。

## 让使用方与来源解耦

```python
from dataioc import DataDescriptor, DataIoC


class RawReadings(DataDescriptor[tuple[int, ...]]):
    pass


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


live = DataIoC().add(RawReadings, (10, 20, 60))
assert live[Report] == "mean=3, peak=6"
```

`Statistics` 依赖的是 `Measurements` 这个概念，而不是数据的具体来源。Provider 可以用同一个键直接提供历史测量值：

```python
recorded = DataIoC().add_provider(
    Measurements,
    lambda _: (2.0, 4.0, 12.0),
)
assert recorded[Report] == "mean=6, peak=12"
```

`recorded` 不再需要 `RawReadings`。provider 在 `Measurements` 处替换了上游路径，`Statistics` 和 `Report` 保持不变。

## 让 provider 声明自己的依赖

Provider 不仅可以返回固定值或读取结果，也可以定义另一条局部推导：

```python
class Calibration(DataDescriptor[float]):
    pass


class CalibratedMeasurements:
    def __build__(self, container: DataIoC) -> tuple[float, ...]:
        scale = container[Calibration]
        return tuple(value * scale for value in container[RawReadings])


calibrated = (
    DataIoC()
    .add(RawReadings, (10, 20, 60))
    .add(Calibration, 0.2)
    .add_provider(Measurements, CalibratedMeasurements())
)
assert calibrated[Report] == "mean=6, peak=12"
```

替代路径现在是 `RawReadings + Calibration -> Measurements`。Provider 对象可以携带状态，也可以通过同一个容器请求依赖。因此，`Measurements` 可以保持稳定身份，而历史记录、仿真、校准和估计等实现则按每次运行的需要切换。

Provider 可以是 callable、带有 `__build__` 的对象，或带有合适 `__build__` 方法的类。它的结果同样按需解析并缓存。

## 绑定一个索引量

```python
indexed = DataIoC().add_provider(
    Measurements[1],
    lambda _: (2.0, 4.0, 12.0),
)
indexed.add_provider(
    Measurements[2],
    lambda _: (1.0, 2.0, 6.0),
)

assert indexed[Report[1]] == "mean=6, peak=12"
assert indexed[Report[2]] == "mean=3, peak=6"
```

每个描述符 provider 只适用于对应的键。未显式指定 ID 的依赖会继承当前构建的 ID，因此 `Report[1]` 会访问 `Measurements[1]`，`Report[2]` 会访问 `Measurements[2]`。

Provider 内部请求的弱依赖会继承当前目标的 ID，显式索引的依赖则保留其 ID。详见[索引数据](indexed-data.zh.md)。

## 在解析前完成配置

请在目标首次访问前注册 provider。重复注册会替换后续未命中缓存时使用的 builder，但不会使已有缓存值及其下游结果失效。需要使用另一组绑定重新求值时，创建新的容器。

## 诊断

```python
diagnostic = DataIoC(record_all=True)
diagnostic.add_provider(Measurements, lambda _: (1.0, 2.0, 6.0))
assert diagnostic[Report] == "mean=3, peak=6"
print(diagnostic.logger)
```

Logger 会显示嵌套依赖、构建出的值、provider 替换和失败信息。`record_all=False` 时，成功的访问树会清除。顶层构建失败时，会打印依赖树并重新抛出原始异常。使用 `container.logger.clear()` 可以清除保留的记录。
