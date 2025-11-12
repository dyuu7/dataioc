# Provider

## 注册 provider

```python
container = DataIoC().add_provider(Sensor, lambda _: Sensor((1, 2, 3)))
```

请求 `Sensor` 时会调用这个 provider。Provider 可以返回适用于该键的任意值。

## 覆盖一个索引键

```python
container.add_provider(Sensor[1], lambda _: Sensor((10, 20, 30)))
```

针对 ID 的 provider 在 `Sensor[1]` 上优先使用。类级 provider 是其他 ID 的后备实现。ID 0 也用于未索引的顶层类读取，因此 `Sensor[0]` provider 会在该场景覆盖 `Sensor`。

## Provider 对象

```python
class EstimatedSensor:
    def __build__(self, container: DataIoC) -> Sensor:
        return Sensor((10, 20, 30))


container.add_provider(Sensor, EstimatedSensor())
```

替代实现有自己的依赖或状态时，使用 provider 对象。

## 诊断

```python
container = DataIoC(record_all=True)
container.add_provider(Sensor, lambda _: Sensor((1, 2, 3)))
container[Total]
print(container.logger)
```

Logger 会显示嵌套依赖、新创建的值、provider 替换和失败信息。
