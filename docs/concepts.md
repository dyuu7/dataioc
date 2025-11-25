# Core concepts

`dataioc` separates three concerns: what a quantity means, how one implementation derives it, and which implementation a particular run uses. This is the data-oriented form of inversion of control.

## A quantity is a stable key

`DataDescriptor` identifies a value in the model. Its name can represent a domain concept such as raw readings, usable measurements, statistics, or a report.

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

A descriptor is the container key, not the stored value itself. It may carry hashable parameters so that one descriptor class can identify related values. Do not mutate a descriptor after registration, because its parameters participate in equality and hashing.

## A builder is a local rule

A builder says how to obtain one quantity from its direct dependencies. In the example, `Report` knows about `Statistics`, but not about `Measurements` or `RawReadings`. Each lower layer owns the next relationship.

A builder can be:

- a `__build__` method on a descriptor or provider object;
- a callable accepting one `DataIoC` argument;
- a class with a suitable `__build__` method.

Dependencies are requested with `container[Target]`. These requests are ordinary Python, so a builder can use conditions, loops, libraries, or existing domain objects.

## Requests form the graph

```python
container = DataIoC().add(RawReadings, (10, 20, 60))
assert container[Report] == "mean=3, peak=6"
```

Requesting `Report` forms and resolves `Report -> Statistics -> Measurements -> RawReadings`. The graph is implicit in the local rules and is expanded only as far as the requested result requires. Callers do not maintain a separate list of steps or execution order.

This is an executable dependency model, not a workflow scheduler: evaluation is synchronous and local to one process.

## Register values and implementations

| Operation | Meaning |
| --- | --- |
| `with_data(*values)` | Register existing instances by type; indexed instances keep their descriptors |
| `add(Target)` | Register the target's own lazy builder |
| `add(Target, value)` | Register an existing value other than `None` |
| `container[Target] = value` | Set a value directly, including an explicit `None` |
| `add_provider(Target, provider)` | Bind the target to another builder |

By default, the container discovers a target's own builder on first access. Strict mode requires every requested key to have data or a registered builder:

```python
strict = DataIoC(allow_implicit_registering=False)
strict.add(Report).add(Statistics).add(Measurements)
strict.add(RawReadings, (10, 20, 60))
assert strict[Report] == "mean=3, peak=6"
```

`add(Target, None)` selects builder registration because `None` is the method's default argument. Use item assignment to store `None` as a value.

See [Providers](providers.md) for choosing another implementation at container assembly time.

## Container lifetime and cache

Each successfully built key is cached, including a value of `None`. Repeated requests within one container therefore share the same result. Different indexed keys have separate cache entries; ordinary types and `UniqueData` are shared across IDs.

A container represents one resolved dataset and provider configuration. Replacing a source or provider does not invalidate values already built from it. Use a fresh container when the inputs or bindings should produce fresh results.

## Failure and diagnostics

Failed builds are not cached; dependencies that completed successfully remain cached. A failed top-level build prints its dependency tree and re-raises the original exception. After supplying missing data or fixing the builder, the target can be requested again.

Successful access trees are normally cleared. Set `record_all=True` to retain them in `container.logger`; see [Provider diagnostics](providers.md#diagnostics).

The container does not provide thread safety, asynchronous construction, automatic dependent invalidation, or cycle detection.
