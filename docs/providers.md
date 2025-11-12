# Providers

## Register a provider

```python
container = DataIoC().add_provider(Sensor, lambda _: Sensor((1, 2, 3)))
```

The provider is used when `Sensor` is requested. A provider may return any value accepted for that key.

## Override one indexed key

```python
container.add_provider(Sensor[1], lambda _: Sensor((10, 20, 30)))
```

The ID-specific provider takes precedence for `Sensor[1]`. A class provider is the fallback for other IDs. ID 0 is also used by an unindexed top-level class read, so a `Sensor[0]` provider takes precedence over `Sensor` there.

## Provider objects

```python
class EstimatedSensor:
    def __build__(self, container: DataIoC) -> Sensor:
        return Sensor((10, 20, 30))


container.add_provider(Sensor, EstimatedSensor())
```

Use a provider object when the replacement has its own dependencies or state.

## Diagnostics

```python
container = DataIoC(record_all=True)
container.add_provider(Sensor, lambda _: Sensor((1, 2, 3)))
container[Total]
print(container.logger)
```

The logger shows nested dependencies, newly created values, provider substitutions, and failures.
