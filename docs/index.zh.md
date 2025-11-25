# dataioc

**面向 Python 的数据 IoC：每个量只声明所需依赖，容器按需展开计算图，并可在不修改下游计算的情况下替换 provider。**

`dataioc` 用局部推导规则描述计算。每个 builder 只请求自己的直接依赖，容器再根据这些请求组合出当前结果所需的计算图，不需要另外维护一套完整工作流。

## 从这里开始

1. [快速开始](quickstart.zh.md)：定义局部规则并请求结果。
2. [核心概念](concepts.zh.md)：了解描述符、builder 和计算图解析。
3. [Provider](providers.zh.md)：将一个量绑定到另一种来源或推导方式。
4. [索引数据](indexed-data.zh.md)：让同一模型复用于多组相关数据。
5. [NumPy 支持](numpy.zh.md)：使用可选的 `DataNDArray` 集成。

## 模型方式

```text
定义局部推导规则
        |
绑定数据与 provider
        |
请求所需结果
        |
只解析必要的计算图
```

每条推导规则只声明自己的直接依赖。容器在运行时组合这些规则，只计算当前结果所需的部分，并在当前容器中复用成功构建的值。

Provider 在组装容器时选定，因此同一个量可以改用另一种来源或推导方式，而使用它的下游计算无需改变。

核心包没有强制的数值库依赖。使用 `DataNDArray` 时安装 `numpy` extra。

## 链接

- [API 参考](api.zh.md)
- [GitHub 仓库](https://github.com/dyuu7/dataioc)
- [贡献者](https://github.com/dyuu7/dataioc#contributors)
