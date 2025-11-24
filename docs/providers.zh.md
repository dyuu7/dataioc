# Provider

## 注册 provider

```python
from dataclasses import dataclass

from dataioc import DataDescriptor, DataIoC, IndexedData


@dataclass
class Sensor(IndexedData):
    values: tuple[int, ...]


class Total(DataDescriptor[int]):
    def __build__(self, container: DataIoC) -> int:
        return sum(container[Sensor].values)


container = DataIoC().add_provider(Sensor, lambda _: Sensor((1, 2, 3)))
assert container[Total] == 6
```

首次请求且未命中缓存时，会调用这个 provider。Provider 可以是 callable 或带有 `__build__` 的对象；结果和其他构建值一样会被缓存。

## 覆盖一个索引键

```python
container.add_provider(Sensor[1], lambda _: Sensor((10, 20, 30)))
assert container[Total[1]] == 60
assert container[Total[2]] == 6
```

针对 ID 的 provider 在 `Sensor[1]` 上优先使用。为 `IndexedData` 类注册的 provider 是其他 ID 的后备实现；为描述符注册的 provider 只适用于该键。ID 0 也用于未索引的顶层类读取，因此 `Sensor[0]` provider 会在该场景覆盖 `Sensor`。

Provider 请求的弱依赖会继承当前目标的 ID，显式索引的依赖则保留其 ID。详见[索引数据](indexed-data.zh.md)。

## 替换 provider

请在目标首次访问前注册替代实现。重复注册会替换后续未命中缓存时使用的 builder，但已有缓存值及其下游结果会保留。需要使用另一种来源重新计算时，配置新的容器。

## Provider 对象

```python
class EstimatedSensor:
    def __build__(self, container: DataIoC) -> Sensor:
        return Sensor((10, 20, 30))


estimated = DataIoC().add_provider(Sensor, EstimatedSensor())
assert estimated[Total] == 60
```

替代实现有自己的依赖或状态时，使用 provider 对象。

## 诊断

```python
container = DataIoC(record_all=True)
container.add_provider(Sensor, lambda _: Sensor((1, 2, 3)))
assert container[Total] == 6
print(container.logger)
```

Logger 会显示嵌套依赖、新创建的值、provider 替换和失败信息。`record_all=False` 时，成功的访问树会清除。顶层构建失败时，会打印依赖树并重新抛出原始异常。可以使用 `container.logger.clear()` 清除保留的记录。
