# 核心概念

## DataDescriptor

`DataDescriptor` 标识一个值，并定义如何构建它。

```python
from dataioc import DataDescriptor, DataIoC


class Samples(DataDescriptor[tuple[int, ...]]):
    pass


class Total(DataDescriptor[int]):
    def __build__(self, container: DataIoC) -> int:
        return sum(container[Samples])


container = DataIoC().add(Samples, (1, 2, 3))
assert container[Total] == 6
```

描述符是容器使用的键。描述符可以携带可哈希参数，因此同一个描述符类可以表示多个相关值。注册后不要修改描述符：它的参数会参与键的相等比较和哈希计算。

## Builder

Builder 可以是：

- 描述符或 provider 对象上的 `__build__` 方法；
- 接收一个 `DataIoC` 参数的 callable；
- 带有合适 `__build__` 方法的类。

Builder 使用 `container[Target]` 请求依赖。访问目标时，容器沿着这些请求解析依赖。

## 注册数据和 builder

| 操作 | 含义 |
| --- | --- |
| `with_data(*values)` | 按类型注册实例；带索引的实例保留其描述符 |
| `add(Target)` | 注册 lazy builder |
| `add(Target, value)` | 注册一个非 `None` 的已有值 |
| `container[Target] = value` | 直接设置值，包括显式的 `None` |
| `add_provider(Target, provider)` | 配置替代 builder |

`add(Target, None)` 会注册 builder，因为 `None` 是该方法的默认参数。需要把 `None` 存为数据时，使用下标赋值。

默认情况下，容器可以在首次访问时注册目标的 builder。严格注册模式要求每个被请求的键已经提供数据或注册 builder：

```python
strict = DataIoC(allow_implicit_registering=False)
strict.add(Total).add(Samples, (1, 2, 3))
assert strict[Total] == 6
```

## 缓存

每个成功构建的键都会被缓存，包括值为 `None` 的情况。不同的索引键有独立的缓存条目。普通类型和 `UniqueData` 在各个 ID 之间共享，详见[索引数据](indexed-data.zh.md)。

请在首次访问前注册 provider。替换 provider 或源数据不会使已经缓存的下游结果失效。新数据集或新的 provider 配置需要重新求值时，使用新的容器。

## 失败和诊断

失败的构建不会被缓存，已经成功构建的依赖则保留在缓存中。顶层构建失败时，容器打印依赖树，然后重新抛出原始异常。提供缺失的数据或修正 builder 后，可以再次请求该目标。

成功的访问树默认会清除。设置 `record_all=True` 可以将它们保留在 `container.logger` 中，详见 [Provider 与诊断](providers.zh.md)。

求值是同步的。容器不提供线程安全、异步构建、自动依赖失效或循环依赖检测。
