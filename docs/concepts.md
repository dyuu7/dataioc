# Core concepts

## Data descriptor

`DataDescriptor` identifies a value and defines how to build it.

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

The descriptor is the key used by the container. A descriptor can hold hashable parameters, so one descriptor class can represent several related values. Do not mutate a descriptor after registration: its parameters participate in key equality and hashing.

## Builder

A builder is either:

- a `__build__` method on a descriptor or provider object;
- a callable accepting one `DataIoC` argument;
- a class with a suitable `__build__` method.

Builders request their dependencies with `container[Target]`. The container follows those requests when the target is accessed.

## Register data and builders

| Operation | Meaning |
| --- | --- |
| `with_data(*values)` | Register instances by type; indexed instances keep their descriptors |
| `add(Target)` | Register a lazy builder |
| `add(Target, value)` | Register an existing value other than `None` |
| `container[Target] = value` | Set a value directly, including an explicit `None` |
| `add_provider(Target, provider)` | Configure an alternative builder |

`add(Target, None)` registers a builder because `None` is the method's default argument. Use item assignment to store `None` as data.

By default, the container can register a target's builder on first access. Strict registration requires each requested key to have data or a registered builder:

```python
strict = DataIoC(allow_implicit_registering=False)
strict.add(Total).add(Samples, (1, 2, 3))
assert strict[Total] == 6
```

## Cache

Each successfully built key is cached, including a value of `None`. Different indexed keys have separate cache entries. Ordinary types and `UniqueData` are shared across IDs; see [Indexed data](indexed-data.md).

Register providers before the first access. Replacing a provider or source value does not invalidate already cached dependents. Use a fresh container for a new dataset or provider configuration that needs fresh results.

## Failure and diagnostics

Failed builds are not cached; dependencies that were successfully built remain cached. A failed top-level build prints its dependency tree and re-raises the original exception. After providing the missing data or fixing the builder, the target can be requested again.

Successful access trees are normally cleared. Set `record_all=True` to retain them in `container.logger`; see [Providers and diagnostics](providers.md#diagnostics).

Evaluation is synchronous. The container does not provide thread safety, async construction, automatic dependent invalidation, or cycle detection.
