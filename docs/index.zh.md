# dataioc

**面向 Python 的声明式数据依赖图。**

每个 `DataDescriptor` 代表一个数据量，并定义其如何由直接依赖推导。`DataIoC` 将这些局部规则组成计算图，仅计算和缓存当前结果所需的子图。为任一数据量绑定 provider，即可替换其来源或推导方式，无需修改下游计算。

## 从光伏购电模型开始

本套指南延续 README 中的光伏示例：根据日照估算发电功率，进而计算建筑的购电量与费用。设计阶段使用公式估算，运行分析阶段采用实测功率，两种来源共用购电量与费用公式。

| 数据量 | 含义 | 标量模型单位 |
| --- | --- | --- |
| `Irradiance` | 日照强度 | kW/m² |
| `SolarPower` | 光伏功率 | kW |
| `GridEnergy` | 购电量 | kWh |
| `ElectricityCost` | 购电费用 | 元 |

![光伏功率由日照估算或由 provider 提供实测值，下游购电量与费用使用相同公式。](https://raw.githubusercontent.com/dyuu7/dataioc/main/docs/assets/data-flow.png)

[快速开始](quickstart.zh.md)完整复现 README 中 1.4 元与 1.8 元的计算结果。后续章节在这一模型上逐步增加替代推导、多传感器数据与逐小时数组。各页示例可独立运行；同一页的代码块按顺序执行。

## 阅读路径

1. [快速开始](quickstart.zh.md)：注册日照数据、定义公式、请求购电费用，并替换为实测功率。
2. [核心概念](concepts.zh.md)：理解数据量、builder、依赖解析、缓存与失败行为。
3. [Provider](providers.zh.md)：为光伏功率配置实测来源或带损耗修正的推导公式。
4. [索引数据](indexed-data.zh.md)：区分多个日照传感器，复用计算规则并共享电价。
5. [NumPy 支持](numpy.zh.md)：将单次读数扩展为逐小时数组，计算时段总费用。
6. [API 参考](api.zh.md)：查询上述模型所使用的接口及其详细约定。

Provider 用于选择同一物理量的来源或推导方式，索引用于区分多个采集通道的数据。两者可以结合使用，例如为不同传感器配置各自的校准方法。

一个容器对应一组确定的输入与 provider 配置，也可包含多个索引数据组。已计算的结果会被缓存；输入或绑定变更后需要重新求值时，应创建新容器。具体约定见[核心概念](concepts.zh.md)。

## 安装

```bash
python -m pip install dataioc
python -m pip install "dataioc[numpy]"
```

核心包没有强制的数值库依赖。使用 `DataNDArray` 时安装 `numpy` extra。

## 项目链接

- [GitHub 仓库与 README](https://github.com/dyuu7/dataioc)
- [贡献者](https://github.com/dyuu7/dataioc#contributors)
