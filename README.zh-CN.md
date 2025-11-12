# dataioc

`dataioc` 用可复用的推导规则描述数据。请求一个结果时，容器解析它的依赖，并缓存构建出的值。数据提供方式可以独立于使用它们的计算逻辑进行配置。

[English](README.md) | [简体中文](README.zh-CN.md) | [文档](https://dyuu7.github.io/dataioc/)

它是一个用于声明式数据依赖和按需计算的轻量 Python 基础组件，适用于模型流水线、特征生成、仿真和其他数据处理流程。

## 快速开始

```python
from dataclasses import dataclass

from dataioc import DataDescriptor, DataIoC, IndexedData


@dataclass
class Sensor(IndexedData):
    values: tuple[int, ...]

    @classmethod
    def __build__(cls, container: DataIoC):
        raise NotImplementedError("Sensor readings must be provided.")


class Total(DataDescriptor[int]):
    def __build__(self, container: DataIoC) -> int:
        return sum(container[Sensor].values)


container = DataIoC().with_data(Sensor((1, 2, 3)))
assert container[Total] == 6
```

`Total` 只描述它依赖 `Sensor` 以及如何计算。结果在首次访问时构建，之后在容器中缓存。

数据来源可以替换，而不需要修改依赖它的计算：

```python
alternative = DataIoC().add_provider(Sensor, lambda _: Sensor((10, 20, 30)))
assert alternative[Total] == 60
```

## 安装

首个 PyPI 版本发布后：

```bash
python -m pip install dataioc
python -m pip install "dataioc[numpy]"
```

完整内容请阅读[文档](https://dyuu7.github.io/dataioc/)，包括 API、数据依赖模型、provider、索引数据和 NumPy 支持。

## 开发

使用尚未发布的源码：

```bash
git clone https://github.com/dyuu7/dataioc.git
cd dataioc
uv sync --frozen
```

```bash
uv sync --frozen
uv run pytest --cov --cov-report=term-missing
uv run ruff check .
uv run pyright
uv run mkdocs build --strict
uv build --no-sources
```

项目需要 Python 3.9+，核心包不强制依赖 NumPy。代码采用 MIT License。

## 贡献者

IoC 数据容器主要由 [yanang007](https://github.com/yanang007) 实现。本独立项目的原始构想、抽取、打包和维护由 [dyuu7](https://github.com/dyuu7) 完成。

<img src="https://contrib.rocks/image?repo=dyuu7/dataioc" alt="贡献者" />
