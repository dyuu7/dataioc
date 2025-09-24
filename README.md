# dataioc

A lazy dependency injection container for data, with weak/strong ID remapping,
provider overrides, and dependency tree diagnostics. Extracted from
[deinterf](https://github.com/dyuu7/deinterf) as an independent, domain-neutral
library under the original MIT license.

The IoC container was primarily implemented by
[yanang007](https://github.com/yanang007).
[dyuu7](https://github.com/dyuu7) proposed the original idea and maintains this
standalone package. See [CONTRIBUTORS.md](CONTRIBUTORS.md) for attribution.

Requires Python 3.10+. The core has no runtime dependencies on Python 3.11+;
Python 3.10 needs only `typing-extensions`. NumPy support is optional.

## Install

Until the first PyPI release, install from GitHub:

```bash
python -m pip install "dataioc @ git+https://github.com/dyuu7/dataioc.git"
python -m pip install "dataioc[numpy] @ git+https://github.com/dyuu7/dataioc.git"
```

## Weak and strong IDs

An unindexed `Sensor` is a weak reference: during a build it inherits the
requesting descriptor's ID. `Sensor[0]` and `Sensor[1]` are strong references
and always identify those specific sensors. Outside a build, `Sensor` means
sensor 0. The following example needs only the core package.

```python
from dataclasses import dataclass

from dataioc import DataDescriptor, DataIoC, IndexedData


@dataclass
class Sensor(IndexedData):
    values: tuple[int, ...]

    @classmethod
    def __build__(cls, container: DataIoC):
        raise NotImplementedError("Sensor readings must be provided.")


class Sum(DataDescriptor[int]):
    def __build__(self, container: DataIoC) -> int:
        return sum(container[Sensor].values)


class OffsetSensor0(DataDescriptor[tuple[int, ...]]):
    def __build__(self, container: DataIoC) -> tuple[int, ...]:
        base = sum(container[Sensor[0]].values)
        return tuple(base + value for value in container[Sensor].values)


container = DataIoC().with_data(
    Sensor((1, 1, 1)),
    Sensor[1]((2, 2, 2)),
)
assert (container[Sum[0]], container[Sum[1]]) == (3, 6)
assert container[OffsetSensor0[0]] == (4, 4, 4)
assert container[OffsetSensor0[1]] == (5, 5, 5)
```

Each result is built on its first access and then cached in that container,
including a result of `None`. IDs separate caches. Ordinary Python types and
classes mixing in `UniqueData` are shared across all build IDs. Descriptor
parameters must be hashable; do not mutate a descriptor after registration.
`descriptor.index_implicit(id)` preserves an existing strong ID, while
`descriptor[id]` explicitly rebinds it.

## Providers and diagnostics

```python
class DoubleSum(DataDescriptor[int]):
    def __build__(self, container: DataIoC) -> int:
        return 2 * sum(container[Sensor].values)


container = DataIoC(record_all=True).with_data(Sensor[1]((2, 2, 2)))
container.add_provider(Sum[1], DoubleSum())
assert container[Sum[1]] == 12
print(container.logger)
```

`add_provider(Target, provider)` registers a callable or an object with
`__build__`. A provider registered for an `IndexedData` class applies to all
its IDs; a provider registered for a descriptor applies only to that key.
Weak dependencies inherit the requested target ID. Register providers before
the first access: cached results and already built dependents are retained.
Repeated provider registration replaces the builder for future uncached reads.

The logger records nested dependencies, created values, provider substitutions,
and failed builds. Successful access trees are normally cleared; `record_all=True`
retains them. A failing top-level build prints its dependency tree and re-raises
the original exception. This is a synchronous container without thread safety,
async construction, automatic dependent invalidation, or cycle detection.

`with_data(*values)` registers instances (including `Sensor[1](...)`).
`add(Target)` registers a lazy builder; `add(Target, value)` supplies data.
Use `container[Target] = None` to register an explicit `None`.
`DataIoC(allow_implicit_registering=False)` requires registered builders or data.

## NumPy support

Install the `numpy` extra and explicitly import `DataNDArray`:

```python
from dataioc import DataNDArray


class SensorArray(DataNDArray):
    pass


arrays = DataIoC().with_data(SensorArray([1, 1, 1]), SensorArray[1]([2, 2, 2]))
assert arrays[SensorArray[1]].sum() == 6
```

Multiple input arrays are column-stacked after checking their sample lengths.
Shape-preserving numerical ufuncs retain the subclass when the result dtype is
compatible. Slicing and reshaping return plain NumPy arrays; reductions return
NumPy scalars. Neither the core import nor `from dataioc import *` imports NumPy.

## Development

The Hatchling, Ruff, Pyright, pytest, coverage, and uv configuration follows
[dafmit-aeromag](https://github.com/dyuu7/dafmit-aeromag).

```bash
uv sync --frozen
uv run pytest --cov --cov-report=term-missing
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv build --no-sources
```

`dataioc` does not depend on `deinterf`, `dafmit-aeromag`, or `aeromag-synth`.
Both `deinterf` and a future `aeromag-synth` can depend on it independently.
