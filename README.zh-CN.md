# dataioc

**面向 Python 的声明式数据依赖图。**

每个 `DataDescriptor` 代表一个数据量，并定义它如何由直接依赖推导。`DataIoC` 将这些局部规则组成计算图，只计算和缓存当前结果所需的子图。给任一数据量绑定 provider，就能替换图中的这一步，下游计算无需改动。

[English](https://github.com/dyuu7/dataioc/blob/main/README.md) | [简体中文](https://github.com/dyuu7/dataioc/blob/main/README.zh-CN.md) | [文档](https://dyuu7.github.io/dataioc/zh/) | [PyPI](https://pypi.org/project/dataioc/)

[![CI](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml/badge.svg)](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml)

## 示例

原始读数 `10`、`20`、`60` 分别表示测量值 `1`、`2`、`6`。

<img src="https://raw.githubusercontent.com/dyuu7/dataioc/main/docs/assets/data-flow.png" width="720" alt="默认情况下，RawReadings 转换为 Measurements；当 provider 将历史数据绑定到 Measurements 时，这条默认推导被替换，而 Statistics 和 Report 保持不变。" />

```python
from dataioc import DataDescriptor, DataIoC


class RawReadings(DataDescriptor):
    pass


class Measurements(DataDescriptor):
    def __build__(self, data):
        return tuple(value / 10 for value in data[RawReadings])


class Statistics(DataDescriptor):
    def __build__(self, data):
        values = data[Measurements]
        return sum(values) / len(values), max(values)


class Report(DataDescriptor):
    def __build__(self, data):
        mean, peak = data[Statistics]
        return f"mean={mean:g}, peak={peak:g}"


data = DataIoC().add(RawReadings, (10, 20, 60))
assert data[Report] == "mean=3, peak=6"
assert data[Measurements] is data[Measurements]
```

调用方只需请求 `data[Report]`，容器会沿依赖关系完成其余计算，并缓存得到的值。

如果这次要使用历史测量值，只需给 `Measurements` 注册另一个 provider：

```python
recorded = DataIoC().add_provider(Measurements, lambda _: (1.0, 2.0, 6.0))
assert recorded[Report] == "mean=3, peak=6"
```

`RawReadings` 此时不再需要，`Statistics` 和 `Report` 都不用改。

## 适用场景

输入和计算过程都固定时，直接调用函数更简单。`dataioc` 适合关系稳定、数据来源会变的模型，例如同一个量在不同场景下来自实测、历史记录、仿真或估计。

`dataioc` 最初来自 [deinterf](https://github.com/dyuu7/deinterf)：[方向余弦既可以根据磁矢量测量得到，也可以直接采用惯导估计](https://github.com/dyuu7/deinterf/blob/main/examples/replace_direction_cosine_source_tmi.py)，后面的补偿计算不用跟着改。[dvmss](https://github.com/dyuu7/dvmss) 也沿用这种组织方式：应用给出输入并请求 `Tmi`，中间量由容器补齐。

## 范围

`dataioc` 只负责在当前进程中同步解析数据依赖，不是工作流调度器。每组数据或 provider 配置应使用一个新容器。缓存、诊断和其他运行限制见[核心概念](https://dyuu7.github.io/dataioc/zh/concepts/)。

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

[![贡献者](https://contrib.rocks/image?repo=dyuu7/dataioc)](https://github.com/dyuu7/dataioc/graphs/contributors)

代码采用 [MIT License](https://github.com/dyuu7/dataioc/blob/main/LICENSE)。
