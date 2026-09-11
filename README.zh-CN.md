# dataioc

**声明式数据依赖，按需解析。**

每一项数据只定义自己的直接推导关系。请求一个结果时，dataioc 展开所需的计算图，按需解析依赖并缓存各项结果。provider 可以把一个上层领域量绑定到另一种数据来源或推导方式，而无需修改使用它的上层计算。

`DataDescriptor` 为数据量提供稳定的语义标识和局部推导规则，`DataIoC` 在运行时将这些局部规则连接起来。请求结果的代码不需要手工安排中间计算的顺序。

[English](https://github.com/dyuu7/dataioc/blob/main/README.md) | [简体中文](https://github.com/dyuu7/dataioc/blob/main/README.zh-CN.md) | [文档](https://dyuu7.github.io/dataioc/zh/) | [PyPI](https://pypi.org/project/dataioc/)

[![CI](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml/badge.svg)](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml)

## 一个小例子

下面的类只声明各自的局部关系：`Features` 需要 `Samples`，`Report` 需要 `Features`。任何一个类都不需要描述从原始样本到报告的完整路径。

<img src="https://raw.githubusercontent.com/dyuu7/dataioc/main/docs/assets/data-flow.png" width="480" alt="Samples 推导出 Features，再生成 Report。另一条路径通过 provider 直接提供 Features，无需 Samples。" />

```python
from dataioc import DataDescriptor, DataIoC


class Samples(DataDescriptor):
    pass


class Features(DataDescriptor):
    def __build__(self, data):
        values = data[Samples]
        mean = sum(values) / len(values)
        return mean, max(values)


class Report(DataDescriptor):
    def __build__(self, data):
        mean, peak = data[Features]
        return f"mean={mean:g}, peak={peak:g}"


data = DataIoC().add(Samples, (1, 2, 6))
assert data[Report] == "mean=3, peak=6"
assert data[Features] is data[Features]
```

访问 `Report` 时，容器展开 `Report -> Features -> Samples` 这张图。每个 `__build__` 都是普通 Python 代码；容器提供依赖上下文、决定求值顺序，并复用其中已经构建的值。

在另一次运行中，也可以把 `Features` 绑定到已保存或由外部计算的结果，无需提供 `Samples`：

```python
saved = DataIoC()
saved.add_provider(Features, lambda _: (10, 12))
assert saved[Report] == "mean=10, peak=12"
```

`Report` 的定义及其中的依赖请求都没有变化。来源选择只出现在容器的组装位置。

## 什么时候值得用

对于短小且输入来源固定的流程，直接传参通常更清楚。当计算关系需要复用，而数据会在实时测量、历史记录、仿真结果、持久化中间量和估计值之间切换时，容器才开始有价值。provider 将这项选择留在容器配置中，领域代码不必逐层传递它。

`IndexedData` 处理另一类反复出现的问题：让同一套计算关系作用于多组相关数据。构建过程中，没有显式 ID 的依赖会继承当前数据组的 ID，显式指定索引的依赖则保持不变。因此，同一套模型定义可以复用于多个传感器、样本或实验，无需复制对应的类。具体规则见[索引数据](https://dyuu7.github.io/dataioc/zh/indexed-data/)。

builder 仍然只是普通 callable 或 `__build__` 方法。已有的 Python 对象可以直接注册，核心包也不会导入 NumPy。dataioc 提供的是依赖图运行时，领域项目可以在此基础上叠加自己的概念、组合操作符和模型词汇。

## 来历

这套模式形成于 [deinterf](https://github.com/dyuu7/deinterf) 的磁干扰补偿工作。[方向余弦示例](https://github.com/dyuu7/deinterf/blob/main/examples/replace_direction_cosine_source_tmi.py)在磁矢量测量与惯导估计之间切换数据来源，使用方向余弦的模型项保持不变；另一个示例通过组合[加入载荷振动项](https://github.com/dyuu7/deinterf/blob/main/examples/extended_load_vibration_tmi.py)。

这些示例使用 deinterf 内置的容器及其模型层。dataioc 将其中的依赖解析和 provider 机制独立出来，以便与其他领域模型配合使用。

同样的结构也出现在[动态车辆磁传感器仿真 dvmss](https://github.com/dyuu7/dvmss) 中。它的 `Tmi` 数据量依赖 `MagVectorXYZ` 和 `BackgroundFieldXYZ`，后两者继续声明对 `IGRF`、`InertialAttitude`、`PermanentFieldXYZ` 和 `InducedFieldXYZ` 等数据量的依赖。应用只需提供位置、日期、姿态和磁源参数等叶子数据，然后请求 `data[Tmi]`，容器会展开并缓存中间结果。dvmss 目前使用 deinterf 中内置的容器，因此它体现的是这套设计的来源，以及同一抽象在补偿和仿真模型中的复用。

## 范围

这张图是可执行的依赖模型，不是通用工作流调度器。依赖解析是同步的，并且只发生在当前进程内。成功构建的值会按键缓存，包括 `None`。替换 provider 不会使已有值及其下游结果失效，因此新的数据集或 provider 配置通常应使用新的容器。顶层构建失败时，容器会打印依赖路径并重新抛出原始异常；也可以保留成功的访问路径用于诊断。

容器不提供线程安全、异步构建、自动缓存失效或循环依赖检测。

- **核心：** Python 3.9+；3.11+ 无运行时依赖，3.9 和 3.10 仅需 `typing-extensions`。
- **数组：** 可选的 NumPy 1.26 和 2.x 集成。
- **分发：** 带类型信息的纯 Python wheel。

[CI](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml) 覆盖 Python 3.9 至 3.14、无 NumPy 的核心导入、类型检查、构建和 NumPy 兼容组合。

## 安装

```bash
python -m pip install dataioc
python -m pip install "dataioc[numpy]"
```

## 文档

- [快速开始](https://dyuu7.github.io/dataioc/zh/quickstart/)：构建第一个派生值。
- [核心概念](https://dyuu7.github.io/dataioc/zh/concepts/)：了解描述符、缓存和失败行为。
- [Provider](https://dyuu7.github.io/dataioc/zh/providers/)：配置替代数据来源。
- [索引数据](https://dyuu7.github.io/dataioc/zh/indexed-data/)：处理多组数据。
- [NumPy](https://dyuu7.github.io/dataioc/zh/numpy/)：使用数组子类。
- [API](https://dyuu7.github.io/dataioc/zh/api/)：查询接口。

## 贡献者

容器主要实现：[yanang007](https://github.com/yanang007)。构想、独立组件抽取、兼容性工作及维护：[dyuu7](https://github.com/dyuu7)。

[![贡献者](https://contrib.rocks/image?repo=dyuu7/dataioc)](https://github.com/dyuu7/dataioc/graphs/contributors)

代码采用 [MIT License](https://github.com/dyuu7/dataioc/blob/main/LICENSE)。
