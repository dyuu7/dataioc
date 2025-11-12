# 核心概念

## DataDescriptor

`DataDescriptor` 标识一个值，并定义如何构建它。

```python
class Total(DataDescriptor[int]):
    def __build__(self, container: DataIoC) -> int:
        return sum(container[Sensor].values)
```

描述符是容器使用的键。描述符可以携带可哈希参数，因此同一个描述符类可以表示多个相关值。

## Builder

Builder 可以是：

- 描述符或 provider 对象上的 `__build__` 方法；
- 接收一个 `DataIoC` 参数的 callable；
- 带有合适 `__build__` 方法的类。

Builder 使用 `container[Target]` 请求依赖。访问目标时，容器沿着这些请求解析依赖。

## 缓存

每个成功构建的键都会被缓存，包括值为 `None` 的情况。不同的索引键有独立的缓存条目。如果计算必须使用新的 provider，请在首次访问前注册；已经缓存的值仍然有效。

## 失败和诊断

失败的构建不会被缓存。顶层构建失败时，容器打印依赖树，然后重新抛出原始异常。设置`record_all=True` 可以把成功的访问树保留在 `container.logger` 中。

容器是同步的，不提供自动的依赖失效或循环依赖检测。
