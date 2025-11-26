# 索引数据

同一种物理量可由多个同类传感器分别采集。索引用于区分这些数据实例，使同一套计算规则能够分别用于各采集通道。本页将[快速开始](quickstart.zh.md)中的光伏模型应用于两个日照传感器，比较各自读数对应的购电费用。面板面积、效率、用电功率、时长与电价保持一致。

## 注册多个采集通道

对于快速开始中的标量描述符，可以通过 `add(Irradiance[0], 0.8)` 和 `add(Irradiance[1], 0.6)` 分别注册数值。已有数据需要组织为对象时，可使用 `IndexedData`，通过 `with_data` 按对象类型和索引注册。

以下将 `Irradiance` 定义为带有 `value` 字段的数据对象，`SolarPower` 相应读取该字段。购电量与费用公式沿用 README：

```python
from dataclasses import dataclass

from dataioc import DataDescriptor, DataIoC, IndexedData, UniqueData


@dataclass
class Irradiance(IndexedData):
    value: float  # kW/m²


class SolarPower(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        efficiency = 0.2
        panel_area = 10.0  # m²
        return efficiency * panel_area * data[Irradiance].value  # kW


class GridEnergy(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        load_power = 3.0  # kW
        duration = 1.0  # h
        return max(load_power - data[SolarPower], 0.0) * duration  # kWh


class ElectricityCost(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        price = 1.0  # CNY/kWh
        return data[GridEnergy] * price  # CNY


data = DataIoC().with_data(
    Irradiance(0.8),
    Irradiance[1](0.6),
)
```

这里用 ID 0 和 1 表示两个传感器。未显式指定索引的描述符依赖在构建过程中是弱引用，会继承当前目标的 ID。因此，请求 `ElectricityCost[1]` 时，容器依次解析 `GridEnergy[1]`、`SolarPower[1]` 和 `Irradiance[1]`，无需在每条计算规则中重复指定传感器。

```python
assert round(data[ElectricityCost[0]], 2) == 1.40
assert round(data[ElectricityCost[1]], 2) == 1.80
assert data[Irradiance] is data[Irradiance[0]]
```

两组读数分别得到 1.6 kW 和 1.2 kW 的光伏功率估算，对应购电费用为 1.4 元和 1.8 元。这是两个采集通道下的模型结果，分别缓存。

在构建之外，未索引的 `Irradiance` 表示 ID 0。`Irradiance[1](...)` 创建的值携带对应描述符，`with_data` 将其注册到该键下。

## 显式引用一个数据组

比较传感器对应的计算结果时，可以固定一个基准通道。以下派生量计算当前通道与第 0 通道的购电费用之差，单位为元：

```python
class CostDifferenceFromBaseline(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        baseline = data[ElectricityCost[0]]
        current = data[ElectricityCost]
        return current - baseline


assert round(data[CostDifferenceFromBaseline[0]], 2) == 0.00
assert round(data[CostDifferenceFromBaseline[1]], 2) == 0.40
```

`ElectricityCost[0]` 是强引用，始终选择第 0 组；未索引的 `ElectricityCost` 仍是弱引用，会继承 `CostDifferenceFromBaseline` 的 ID。索引 1 对应的费用比基准高 0.4 元。

## 重新绑定描述符

`index_implicit(id)` 保留已有的强 ID。下标操作显式重新绑定描述符，原描述符不变：

```python
original = ElectricityCost[1]
assert original.index_implicit(2) is original
assert original[2].id == 2
assert original.id == 1
```

## 跨数据组共享

普通 Python 类型在所有构建 ID 之间共享。索引类也只需要一个共享值时，可以混入 `UniqueData`。例如，将原先固定在费用公式中的电价提取为共享的 `Tariff`：

```python
@dataclass
class Tariff(IndexedData, UniqueData):
    price: float  # CNY/kWh


def cost_with_tariff(data: DataIoC) -> float:
    return data[GridEnergy] * data[Tariff].price


shared = DataIoC().with_data(
    Irradiance(0.8),
    Irradiance[1](0.6),
    Tariff(1.0),
)
shared.add_provider(ElectricityCost[0], cost_with_tariff)
shared.add_provider(ElectricityCost[1], cost_with_tariff)

assert shared[Tariff[0]] is shared[Tariff[1]]
assert round(shared[ElectricityCost[0]], 2) == 1.40
assert round(shared[ElectricityCost[1]], 2) == 1.80
```

每个采集通道使用自身的 `GridEnergy`，同时访问同一个电价对象。这里在新容器中完成所有输入与 provider 配置，再请求计算结果。

Provider 用于选择来源或推导方式，索引用于区分数据组；两者可以结合使用，例如为不同传感器配置不同校准方法，参见 [Provider](providers.zh.md)。输入或绑定变更不会自动使已有缓存失效，详见[容器生命周期与缓存](concepts.zh.md)。

下一步可阅读 [NumPy 支持](numpy.zh.md)，将每个传感器的单次日照读数扩展为逐小时数组。接口说明见 [API](api.zh.md)。
