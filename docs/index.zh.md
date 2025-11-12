# dataioc

**面向 Python 的声明式数据依赖与按需计算。**

dataioc 用可复用的推导规则描述数据。请求一个结果时，容器解析它的依赖，并缓存构建出的值。数据提供方式可以独立于使用它们的计算逻辑进行配置。

## 从这里开始

1. [快速开始](quickstart.zh.md)：定义一个派生值。
2. [核心概念](concepts.zh.md)：了解描述符和 builder。
3. [Provider](providers.zh.md)：替换数据来源或计算方式。
4. [索引数据](indexed-data.zh.md)：让同一模型复用于多组数据。
5. [NumPy 支持](numpy.zh.md)：使用 NumPy 1.26 和 2.x 的 `DataNDArray`。

## 工作模型

```text
声明推导规则
    |
请求结果
    |
按需解析依赖
    |
缓存构建出的值
```

核心包没有强制的数值库依赖。使用 `DataNDArray` 时安装 `numpy` extra。

## 链接

- [API 参考](api.zh.md)
- [GitHub 仓库](https://github.com/dyuu7/dataioc)
- [贡献者](https://github.com/dyuu7/dataioc/blob/main/README.zh-CN.md#贡献者)
