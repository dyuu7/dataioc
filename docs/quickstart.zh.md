# 快速开始

## 1. 提供原始数据

已有的数据使用 `with_data` 注册。

```python
from dataclasses import dataclass

from dataioc import DataDescriptor, DataIoC, IndexedData


@dataclass
class Sensor(IndexedData):
    values: tuple[int, ...]


class Total(DataDescriptor[int]):
    def __build__(self, container: DataIoC) -> int:
        return sum(container[Sensor].values)


container = DataIoC().with_data(Sensor((1, 2, 3)))
```

## 2. 定义派生值

实现 `__build__`，然后请求这个描述符。

```python
assert container[Total] == 6
assert container[Total] == 6  # 第二次访问使用缓存。
```

容器只在首次访问时构建 `Total`。builder 内部通过 `container[Sensor]` 请求它的依赖。

## 3. 提供计算得到的数据

如果数据需要在运行时计算或替换，使用 provider。

```python
alternative = DataIoC().add_provider(Sensor, lambda _: Sensor((10, 20, 30)))
assert alternative[Total] == 60
```

有依赖关系的 provider 可以定义 `__build__`，不必使用 lambda。

```python
class EstimatedSensor:
    def __build__(self, container: DataIoC) -> Sensor:
        return Sensor((10, 20, 30))


alternative = DataIoC().add_provider(Sensor, EstimatedSensor())
```

接下来阅读[核心概念](concepts.zh.md)或[Provider](providers.zh.md)。
