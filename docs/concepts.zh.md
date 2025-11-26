# 核心概念

`dataioc` 将三件事分开：一个量表示什么、某种实现如何推导它，以及本次运行选择哪种实现。这是控制反转在数据计算中的体现。

## 数据量是稳定的键

`DataDescriptor` 标识模型中的数据量。本页沿用[快速开始](quickstart.zh.md)中的光伏购电模型：`Irradiance` 表示日照强度，`SolarPower` 表示光伏功率，`GridEnergy` 表示购电量，`ElectricityCost` 表示购电费用。面板面积、效率、用电功率、时长和电价均与 README 相同。

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
```

描述符是容器使用的键，不是存储的值本身。它可以携带可哈希参数，让同一个描述符类标识一组相关数据。注册后不要修改描述符，因为它的参数会参与相等比较和哈希计算。

## Builder 是局部规则

Builder 定义如何从直接依赖计算一个量。例如，`ElectricityCost` 仅依赖 `GridEnergy`；购电量如何根据光伏功率计算，以及光伏功率如何根据日照推导，分别由 `GridEnergy` 和 `SolarPower` 定义。

Builder 可以是：

- 描述符或 provider 对象上的 `__build__` 方法；
- 接收一个 `DataIoC` 参数的 callable；
- 带有合适 `__build__` 方法的类。

Builder 通过 `data[Target]` 请求依赖。这些请求仍然是普通 Python 代码，因此可以使用条件、循环、第三方库和已有领域对象。

## 请求形成计算图

```python
data = DataIoC().add(Irradiance, 0.8)  # kW/m²
assert round(data[ElectricityCost], 2) == 1.40
```

请求 `ElectricityCost` 时，容器形成并解析 `ElectricityCost → GridEnergy → SolarPower → Irradiance`。计算图隐含在各个局部规则中，并且只展开到当前结果所需要的范围。调用方无需另外维护步骤列表或执行顺序。

`dataioc` 在当前进程中同步解析依赖并执行计算。它负责组织数据依赖，不提供工作流调度。

## 注册值和实现

| 操作 | 含义 |
| --- | --- |
| `with_data(*values)` | 按类型注册已有实例；带索引的实例保留其描述符 |
| `add(Target)` | 注册目标自身的 lazy builder |
| `add(Target, value)` | 注册一个非 `None` 的已有值 |
| `data[Target] = value` | 直接设置值，包括显式的 `None` |
| `add_provider(Target, provider)` | 将目标绑定到另一个 builder |

默认情况下，容器会在首次访问时发现目标自身的 builder。严格模式要求每个被请求的键已经提供数据或注册 builder：

```python
strict = DataIoC(allow_implicit_registering=False)
strict.add(ElectricityCost).add(GridEnergy).add(SolarPower)
strict.add(Irradiance, 0.8)
assert round(strict[ElectricityCost], 2) == 1.40
```

`add(Target, None)` 会选择注册 builder，因为 `None` 是该方法的默认参数。需要把 `None` 存为值时，使用下标赋值。

如何在组装容器时选择另一种实现，详见 [Provider](providers.zh.md)。

## 容器生命周期与缓存

每个成功构建的键都会被缓存，包括值为 `None` 的情况。因此，同一个容器中的重复请求会共享结果。不同索引键有独立的缓存条目；普通类型和 `UniqueData` 则在各个 ID 之间共享。

一个容器对应一组确定的输入与 provider 配置，可以通过索引管理多个传感器或数据组。输入或 provider 配置的变更不会自动使已有结果失效；需要重新求值时，应创建新容器。Provider 用于选择来源或推导方式，索引用于区分数据组，详见[索引数据](indexed-data.zh.md)。

## 失败和诊断

失败的构建不会被缓存，已经成功构建的依赖会保留。顶层构建失败时，容器打印依赖树，然后重新抛出原始异常。补充缺失数据或修正 builder 后，可以再次请求目标。

成功的访问树默认会清除。设置 `record_all=True` 可以将它们保留在 `data.logger` 中，详见 [Provider 诊断](providers.zh.md)。

容器不提供线程安全、异步构建、自动依赖失效或循环依赖检测。
