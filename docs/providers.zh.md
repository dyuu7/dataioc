# Provider

Provider 将一个数据量绑定到具体来源或推导方式。本页沿用[快速开始](quickstart.zh.md)中的光伏购电模型，依次展示实测值替换、具有自身依赖的替代公式，以及针对单个采集通道的配置。各代码块按顺序执行。

## 以实测值替代估算

默认模型根据日照强度估算光伏功率，再计算一小时内的购电量与费用。面板面积、效率、用电功率和电价与 README 相同：

```python
from dataioc import DataDescriptor, DataIoC


class Irradiance(DataDescriptor[float]):
    pass


class SolarPower(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        efficiency = 0.2
        panel_area = 10.0  # m²
        return efficiency * panel_area * data[Irradiance]  # kW


class GridEnergy(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        load_power = 3.0  # kW
        duration = 1.0  # h
        return max(load_power - data[SolarPower], 0.0) * duration  # kWh


class ElectricityCost(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        price = 1.0  # CNY/kWh
        return data[GridEnergy] * price  # CNY


estimated = DataIoC().add(Irradiance, 0.8)  # kW/m²
assert round(estimated[ElectricityCost], 2) == 1.40
```

`GridEnergy` 依赖 `SolarPower` 表示的功率值。将 provider 绑定到该键，即可提供实测的 1.2 kW：

```python
measured = DataIoC().add_provider(SolarPower, lambda _: 1.2)  # kW
assert round(measured[ElectricityCost], 2) == 1.80
```

该容器无需提供 `Irradiance`。Provider 在 `SolarPower` 处替换默认推导，购电量与费用公式继续复用，费用由 1.4 元变为 1.8 元。若已有固定值，也可使用 `DataIoC().add(SolarPower, 1.2)` 直接注册；provider 适合按需读取数据或执行替代计算。

## 为替代公式声明依赖

设计分析还可以在原有估算公式中引入损耗修正。这里用无量纲的 `LossFactor` 表示保留的功率比例；取值 0.75 表示保留原估算功率的 75%。

```python
class LossFactor(DataDescriptor[float]):
    pass


class LossAdjustedSolarPower:
    def __build__(self, data: DataIoC) -> float:
        efficiency = 0.2
        panel_area = 10.0  # m²
        return efficiency * panel_area * data[Irradiance] * data[LossFactor]


adjusted = (
    DataIoC()
    .add(Irradiance, 0.8)
    .add(LossFactor, 0.75)
    .add_provider(SolarPower, LossAdjustedSolarPower())
)
assert round(adjusted[SolarPower], 2) == 1.20
assert round(adjusted[ElectricityCost], 2) == 1.80
```

此时推导关系为 `Irradiance + LossFactor → SolarPower`。Provider 通过容器请求自己的直接依赖，`GridEnergy` 和 `ElectricityCost` 无需修改。替代实现应请求所需输入，避免在构建 `SolarPower` 时再次请求 `SolarPower` 本身，形成循环依赖。

Provider 可以是接收容器的 callable、带有 `__build__` 的对象，或带有合适 `__build__` 方法的类。对象可携带状态，成功构建的结果同样按键缓存。

## 为单个采集通道配置推导方式

两个日照传感器可以分别提供输入，并共用购电模型。索引 0 使用默认公式，索引 1 使用带损耗修正的公式；其余模型参数保持一致：

```python
indexed = (
    DataIoC()
    .add(Irradiance[0], 0.8)
    .add(Irradiance[1], 0.6)
    .add(LossFactor[1], 0.75)
    .add_provider(SolarPower[1], LossAdjustedSolarPower())
)
assert round(indexed[ElectricityCost[0]], 2) == 1.40
assert round(indexed[ElectricityCost[1]], 2) == 2.10
```

每个 provider 绑定仅作用于指定键。请求 `ElectricityCost[1]` 时，依赖沿索引 1 传播，provider 中的 `Irradiance` 和 `LossFactor` 分别解析为 `Irradiance[1]` 和 `LossFactor[1]`，得到光伏功率 0.9 kW、费用 2.1 元。索引 0 仍使用默认推导。

Provider 用于选择来源或推导方式，索引用于区分采集通道。Provider 内部未显式指定索引的描述符依赖继承当前目标的索引；显式索引依赖保持其指定值。详见[索引数据](indexed-data.zh.md)。

## 在解析前完成配置

Provider 应在目标首次访问前注册。重复注册会替换后续未命中缓存时使用的 builder，但不会使已有结果及其下游缓存失效。输入或绑定变更后需要重新求值时，应创建新容器。

## 诊断

```python
diagnostic = DataIoC(record_all=True)
diagnostic.add_provider(SolarPower, lambda _: 1.2)
assert round(diagnostic[ElectricityCost], 2) == 1.80
print(diagnostic.logger)
```

Logger 显示嵌套依赖、构建结果、provider 替换和失败信息。`record_all=False` 时，成功的访问树会被清除；设置 `record_all=True` 可保留这些记录。顶层构建失败时，容器打印依赖树并重新抛出原始异常。使用 `diagnostic.logger.clear()` 可清除保留的记录。
