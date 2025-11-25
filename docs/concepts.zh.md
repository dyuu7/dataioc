# 核心概念

`dataioc` 将三件事分开：一个量表示什么、某种实现如何推导它，以及本次运行选择哪种实现。这是控制反转在数据计算中的体现。

## 数据量是稳定的键

`DataDescriptor` 标识模型中的一个值。它的名称可以对应原始读数、可用的测量值、统计量或报告等领域概念。

```python
from dataioc import DataDescriptor, DataIoC


class RawReadings(DataDescriptor[tuple[int, ...]]):
    pass


class Measurements(DataDescriptor[tuple[float, ...]]):
    def __build__(self, container: DataIoC) -> tuple[float, ...]:
        return tuple(value / 10 for value in container[RawReadings])


class Statistics(DataDescriptor[tuple[float, float]]):
    def __build__(self, container: DataIoC) -> tuple[float, float]:
        values = container[Measurements]
        return sum(values) / len(values), max(values)


class Report(DataDescriptor[str]):
    def __build__(self, container: DataIoC) -> str:
        mean, peak = container[Statistics]
        return f"mean={mean:g}, peak={peak:g}"
```

描述符是容器使用的键，不是存储的值本身。它可以携带可哈希参数，让同一个描述符类标识一组相关数据。注册后不要修改描述符，因为它的参数会参与相等比较和哈希计算。

## Builder 是局部规则

Builder 只说明如何从直接依赖得到一个量。在上面的例子中，`Report` 知道自己需要 `Statistics`，但不知道 `Measurements` 或 `RawReadings`。下一层关系分别由更下层的量负责。

Builder 可以是：

- 描述符或 provider 对象上的 `__build__` 方法；
- 接收一个 `DataIoC` 参数的 callable；
- 带有合适 `__build__` 方法的类。

Builder 通过 `container[Target]` 请求依赖。这些请求仍然是普通 Python 代码，因此可以使用条件、循环、第三方库和已有领域对象。

## 请求形成计算图

```python
container = DataIoC().add(RawReadings, (10, 20, 60))
assert container[Report] == "mean=3, peak=6"
```

请求 `Report` 时，容器形成并解析 `Report -> Statistics -> Measurements -> RawReadings`。计算图隐含在各个局部规则中，并且只展开到当前结果所需要的范围。调用方无需另外维护步骤列表或执行顺序。

这是一套可执行的依赖模型，而不是工作流调度器：求值是同步的，并且只发生在当前进程内。

## 注册值和实现

| 操作 | 含义 |
| --- | --- |
| `with_data(*values)` | 按类型注册已有实例；带索引的实例保留其描述符 |
| `add(Target)` | 注册目标自身的 lazy builder |
| `add(Target, value)` | 注册一个非 `None` 的已有值 |
| `container[Target] = value` | 直接设置值，包括显式的 `None` |
| `add_provider(Target, provider)` | 将目标绑定到另一个 builder |

默认情况下，容器会在首次访问时发现目标自身的 builder。严格模式要求每个被请求的键已经提供数据或注册 builder：

```python
strict = DataIoC(allow_implicit_registering=False)
strict.add(Report).add(Statistics).add(Measurements)
strict.add(RawReadings, (10, 20, 60))
assert strict[Report] == "mean=3, peak=6"
```

`add(Target, None)` 会选择注册 builder，因为 `None` 是该方法的默认参数。需要把 `None` 存为值时，使用下标赋值。

如何在组装容器时选择另一种实现，详见 [Provider](providers.zh.md)。

## 容器生命周期与缓存

每个成功构建的键都会被缓存，包括值为 `None` 的情况。因此，同一个容器中的重复请求会共享结果。不同索引键有独立的缓存条目；普通类型和 `UniqueData` 则在各个 ID 之间共享。

一个容器代表一组已经确定的数据与 provider 配置。替换来源或 provider 不会使已经构建的值失效。输入或绑定变化后需要重新计算时，使用新的容器。

## 失败和诊断

失败的构建不会被缓存，已经成功构建的依赖会保留。顶层构建失败时，容器打印依赖树，然后重新抛出原始异常。补充缺失数据或修正 builder 后，可以再次请求目标。

成功的访问树默认会清除。设置 `record_all=True` 可以将它们保留在 `container.logger` 中，详见 [Provider 诊断](providers.zh.md)。

容器不提供线程安全、异步构建、自动依赖失效或循环依赖检测。
