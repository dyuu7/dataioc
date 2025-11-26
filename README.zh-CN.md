# dataioc

**面向 Python 的声明式数据依赖图。**

每个 `DataDescriptor` 代表一个数据量，并定义其如何由直接依赖推导。`DataIoC` 将这些局部规则组成计算图，仅计算和缓存当前结果所需的子图。为任一数据量绑定 provider，即可替换其来源或推导方式，无需修改下游计算。

[English](https://github.com/dyuu7/dataioc/blob/main/README.md) | [简体中文](https://github.com/dyuu7/dataioc/blob/main/README.zh-CN.md) | [文档](https://dyuu7.github.io/dataioc/zh/) | [PyPI](https://pypi.org/project/dataioc/)

[![CI](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml/badge.svg)](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml)

## 示例

本例计算配有光伏系统的建筑在一小时内的购电费用。设计阶段，根据日照估算发电功率；系统投入运行后，采用电表实测功率。两个阶段使用相同的购电量与费用计算公式。

模型假设该时段内功率恒定，且不考虑储能与余电上网收益。光伏面板面积为 10 m²，效率为 20%；建筑用电功率为 3 kW，电价为 1 元/kWh。

- 光伏功率（kW）= 效率 × 面板面积（m²）× 日照强度（kW/m²）。
- 购电量（kWh）= max(用电功率 − 光伏功率, 0) × 时长（h）。
- 购电费用（元）= 购电量 × 电价（元/kWh）。

`DataDescriptor` 标识模型中的数据量，派生量的 `__build__` 方法定义其计算公式：

<img src="https://raw.githubusercontent.com/dyuu7/dataioc/main/docs/assets/data-flow.png" width="720" alt="设计阶段：根据日照强度 Irradiance 推导光伏功率 SolarPower，进而计算购电量 GridEnergy 和费用 ElectricityCost。运行分析阶段：provider 提供实测光伏功率，替换基于日照的推导，其余计算保持不变。" />

```python
from dataioc import DataDescriptor, DataIoC


class Irradiance(DataDescriptor):
    pass


class SolarPower(DataDescriptor):
    def __build__(self, data):
        efficiency = 0.2
        panel_area = 10.0  # m²
        return efficiency * panel_area * data[Irradiance]  # kW


class GridEnergy(DataDescriptor):
    def __build__(self, data):
        load_power = 3.0  # kW
        duration = 1.0  # h
        return max(load_power - data[SolarPower], 0.0) * duration  # kWh


class ElectricityCost(DataDescriptor):
    def __build__(self, data):
        price = 1.0  # CNY/kWh
        return data[GridEnergy] * price  # CNY


data = DataIoC().add(Irradiance, 0.8)  # kW/m²
assert round(data[ElectricityCost], 2) == 1.40
```

日照强度为 0.8 kW/m² 时，模型计算得到光伏功率为 1.6 kW，购电量为 1.4 kWh，费用为 1.4 元。调用方仅需请求 `data[ElectricityCost]`，容器将根据依赖关系计算所需的中间量，并缓存结果。

若运行期间测得光伏功率为 1.2 kW，可在新容器中为 `SolarPower` 绑定 provider，以实测值替代公式估算：

```python
measured = DataIoC().add_provider(SolarPower, lambda _: 1.2)  # kW
assert round(measured[ElectricityCost], 2) == 1.80
```

采用实测功率后，购电量为 1.8 kWh，费用为 1.8 元。此时无需向容器提供 `Irradiance`：provider 替换了 `SolarPower` 的默认推导，而 `GridEnergy` 和 `ElectricityCost` 的计算规则保持不变。在实际应用中，provider 还可读取文件中的功率数据，或调用其他预测模型。

一个容器对应一组确定的输入与 provider 配置，可以通过索引管理多个传感器或数据组。已计算的结果会被缓存，且不会随输入或 provider 配置的变更自动失效；需要重新求值时，应创建新容器。依赖解析方式、缓存机制与其他运行限制见[核心概念](https://dyuu7.github.io/dataioc/zh/concepts/)。

## 适用场景

`dataioc` 源于磁测干扰补偿项目 [deinterf](https://github.com/dyuu7/deinterf)。在该项目中，[描述磁场方向的量既可由磁传感器数据计算，也可由惯性导航系统估计](https://github.com/dyuu7/deinterf/blob/main/examples/replace_direction_cosine_source_tmi.py)，而后续补偿公式需要复用。模型因此需要分别表达数据量的含义、计算关系，以及每次运行采用的数据来源。

`dataioc` 将这一需求抽取为通用的数据依赖容器：模型定义各个量的局部计算规则，应用配置输入与来源，再请求所需结果。[aeromag-synth](https://github.com/dyuu7/aeromag-synth) 在磁测仿真中采用了相同的组织方式。

同一种物理量也可能由多个同类传感器分别采集。`dataioc` 通过[索引](https://dyuu7.github.io/dataioc/zh/indexed-data/)区分不同采集通道的数据，使同一套计算规则能够分别用于各传感器，并独立缓存相应的计算结果。Provider 用于选择推导方式，索引用于区分采集通道；两者可以结合使用，例如为不同传感器配置各自的校准方法。

这种方式适用于需要持续迭代的科研与工程模型，可支持不同推导方法与多组采集数据共用计算逻辑。已有数值函数可继续承担具体计算，容器负责组织它们之间的数据依赖。

## 安装

```bash
python -m pip install dataioc
python -m pip install "dataioc[numpy]"
```

## 文档

- [快速开始](https://dyuu7.github.io/dataioc/zh/quickstart/)：从局部依赖规则构建结果。
- [核心概念](https://dyuu7.github.io/dataioc/zh/concepts/)：了解描述符、builder、缓存和失败行为。
- [Provider](https://dyuu7.github.io/dataioc/zh/providers/)：将一个量绑定到另一种来源或推导方式。
- [索引数据](https://dyuu7.github.io/dataioc/zh/indexed-data/)：让同一模型复用于多组相关数据。
- [NumPy](https://dyuu7.github.io/dataioc/zh/numpy/)：使用数组子类。
- [API](https://dyuu7.github.io/dataioc/zh/api/)：查询接口。

## 贡献者

[yanang007](https://github.com/yanang007) 编写了最初的容器实现。[dyuu7](https://github.com/dyuu7) 提出了这套设想，将其工程化以及抽取为 `dataioc`，并负责维护。

<a href="https://github.com/yanang007">
  <img src="https://wsrv.nl/?url=avatars.githubusercontent.com/u/8695716&amp;w=128&amp;h=128&amp;fit=cover&amp;mask=circle&amp;output=png"
       width="64" height="64" alt="yanang007" title="yanang007" />
</a>
<a href="https://github.com/dyuu7">
  <img src="https://wsrv.nl/?url=avatars.githubusercontent.com/u/49279922&amp;w=128&amp;h=128&amp;fit=cover&amp;mask=circle&amp;output=png"
       width="64" height="64" alt="dyuu7" title="dyuu7" />
</a>

代码采用 [MIT License](https://github.com/dyuu7/dataioc/blob/main/LICENSE)。
