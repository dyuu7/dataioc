# 快速开始

本指南将 README 中的光伏购电模型分解为数据注册、公式定义、结果请求和来源替换四个步骤。各页示例可独立运行；同一页的代码块按顺序执行。

模型计算一小时内的购电费用，假设该时段内功率恒定，不考虑储能与余电上网收益。光伏面板面积为 10 m²，效率为 20%；建筑用电功率为 3 kW，电价为 1 元/kWh。

## 1. 注册日照数据

`Irradiance` 标识日照强度，单位为 kW/m²。通过 `add` 将已有数值注册到该键：

```python
from dataioc import DataDescriptor, DataIoC


class Irradiance(DataDescriptor[float]):
    pass


data = DataIoC().add(Irradiance, 0.8)  # kW/m²
```

`DataDescriptor[float]` 中的 `float` 表示该量的值类型。README 省略了类型注解，两种写法的运行行为相同。带有自身类型或索引的数据对象也可通过 `with_data` 注册，详见[索引数据](indexed-data.zh.md)。

## 2. 定义计算公式

- 光伏功率（kW）= 效率 × 面板面积（m²）× 日照强度（kW/m²）。
- 购电量（kWh）= max(用电功率 − 光伏功率, 0) × 时长（h）。
- 购电费用（元）= 购电量 × 电价（元/kWh）。

每个派生量的 `__build__` 方法只请求其直接依赖：

```python
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
```

## 3. 请求购电费用

请求 `ElectricityCost` 时，容器沿 `ElectricityCost → GridEnergy → SolarPower → Irradiance` 解析依赖，再计算所需结果。每个成功构建的值都会缓存在当前容器中。

```python
assert round(data[ElectricityCost], 2) == 1.40
assert round(data[SolarPower], 2) == 1.60
assert round(data[GridEnergy], 2) == 1.40
```

日照强度为 0.8 kW/m² 时，光伏功率为 1.6 kW，购电量为 1.4 kWh，费用为 1.4 元。后续请求 `SolarPower` 和 `GridEnergy` 时，容器直接返回已缓存的中间结果。

## 4. 使用实测功率

若实测光伏功率为 1.2 kW，可在新容器中为 `SolarPower` 绑定 provider：

```python
measured = DataIoC().add_provider(SolarPower, lambda _: 1.2)  # kW
assert round(measured[ElectricityCost], 2) == 1.80
```

`measured` 无需提供 `Irradiance`，因为 provider 直接提供光伏功率。`GridEnergy` 和 `ElectricityCost` 的公式保持不变，计算得到购电量为 1.8 kWh，费用为 1.8 元。

一个容器对应一组确定的输入与 provider 配置，也可通过索引管理多个传感器或数据组。输入或绑定变更不会自动使已有结果失效；需要重新求值时，应创建新容器。

继续阅读[核心概念](concepts.zh.md)，了解计算图与缓存机制；或阅读 [Provider](providers.zh.md)，为光伏功率配置具有自身依赖的替代推导方法。
