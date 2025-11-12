# Core concepts

## Data descriptor

`DataDescriptor` identifies a value and defines how to build it.

```python
class Total(DataDescriptor[int]):
    def __build__(self, container: DataIoC) -> int:
        return sum(container[Sensor].values)
```

The descriptor is the key used by the container. A descriptor can hold hashable parameters, so one descriptor class can represent several related values.

## Builder

A builder is either:

- a `__build__` method on a descriptor or provider object;
- a callable accepting one `DataIoC` argument;
- a class with a suitable `__build__` method.

Builders request their dependencies with `container[Target]`. The container follows those requests when the target is accessed.

## Cache

Each successfully built key is cached, including a value of `None`. Different indexed keys have separate cache entries. Register providers before the first access when a computation must use the new provider; existing cached values remain valid.

## Failure and diagnostics

Failed builds are not cached. A failed top-level build prints its dependency tree and re-raises the original exception. Set `record_all=True` to retain successful access trees in `container.logger`.

The container is synchronous and has no automatic dependent invalidation or cycle detection.
