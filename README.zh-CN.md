# dataioc

**面向 Python 的声明式数据依赖与按需计算。**

多个计算共享输入和中间量时，替换数据来源可能影响许多下游计算。dataioc 让每个计算只请求自己需要的数据，数据提供方式由容器独立配置。

[English](https://github.com/dyuu7/dataioc/blob/main/README.md) | [简体中文](https://github.com/dyuu7/dataioc/blob/main/README.zh-CN.md) | [文档](https://dyuu7.github.io/dataioc/zh/) | [PyPI](https://pypi.org/project/dataioc/)

[![CI](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml/badge.svg)](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml)

## 一份报告，两种数据来源

可以从 `Samples` 推导 `Features`，也可以通过 provider 直接提供预计算的特征。两种情况下，`Report` 都依赖同一个 `Features`。

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

每个 `__build__` 都是普通的 Python 代码。请求 `Report` 时，容器按需构建它的依赖；后续读取复用该容器中的缓存值。

另一个容器可以直接提供 `Features`，无需任何 `Samples`：

```python
saved = DataIoC()
saved.add_provider(Features, lambda _: (10, 12))
assert saved[Report] == "mean=10, peak=12"
```

报告定义保持不变。计算规则与数据来源可以分别复用和配置。

## 实际应用：磁干扰补偿

[deinterf](https://github.com/dyuu7/deinterf) 使用了同样的数据依赖模式。[方向余弦示例](https://github.com/dyuu7/deinterf/blob/main/examples/replace_direction_cosine_source_tmi.py)在磁矢量测量和惯导估计之间替换数据来源，使用方向余弦的模型项保持不变。另一个示例通过组合[添加载荷振动项](https://github.com/dyuu7/deinterf/blob/main/examples/extended_load_vibration_tmi.py)。

这些示例使用 deinterf 内置的容器和应用专用的模型组合语法。dataioc 提供可复用的数据依赖与 provider 抽象，应用负责自己的领域逻辑。

## 适用场景与验证

适用于派生测量量、特征生成、替代数据来源，以及[多组数据复用同一套计算规则](https://dyuu7.github.io/dataioc/zh/indexed-data/)。

- **核心：** Python 3.9+；3.11+ 无运行时依赖，3.9 和 3.10 仅需 `typing-extensions`。
- **数组：** 可选的 NumPy 1.26 和 2.x 集成。
- **分发：** 带类型信息的纯 Python wheel。

[CI](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml) 覆盖 Python 3.9 至 3.14、无 NumPy 的核心导入、类型检查、构建和 NumPy 兼容组合。

求值是同步的，已缓存的依赖结果不会自动失效；请在首次访问前配置 provider。详见[缓存行为与边界](https://dyuu7.github.io/dataioc/zh/concepts/)。

## 安装与继续阅读

```bash
python -m pip install dataioc
python -m pip install "dataioc[numpy]"
```

- [快速开始](https://dyuu7.github.io/dataioc/zh/quickstart/)：构建第一个派生值。
- [Provider](https://dyuu7.github.io/dataioc/zh/providers/)：配置替代数据来源。
- [索引数据](https://dyuu7.github.io/dataioc/zh/indexed-data/)：处理多组数据。
- [NumPy](https://dyuu7.github.io/dataioc/zh/numpy/)：使用数组子类。
- [API](https://dyuu7.github.io/dataioc/zh/api/)：查询接口。
- [开发](https://dyuu7.github.io/dataioc/zh/maintenance/)：运行检查、参与项目。

## 贡献者

容器主要实现：[yanang007](https://github.com/yanang007)。构想、独立组件抽取、兼容性工作及维护：[dyuu7](https://github.com/dyuu7)。

[![贡献者](https://contrib.rocks/image?repo=dyuu7/dataioc)](https://github.com/dyuu7/dataioc/graphs/contributors)

代码采用 [MIT License](https://github.com/dyuu7/dataioc/blob/main/LICENSE)。
