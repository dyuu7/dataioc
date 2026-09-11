# dataioc

**Declarative data dependencies, resolved on demand.**

Each quantity defines only its immediate derivation. When a result is requested, dataioc expands the required computation graph, resolves it on demand, and caches each value. A provider can bind a domain-level quantity to another data source or derivation without changing the calculations above it.

`DataDescriptor` gives a quantity a stable name and a local rule for deriving it. `DataIoC` connects those local rules at runtime. The code that requests a result does not need to lay out the order of intermediate calculations.

[English](https://github.com/dyuu7/dataioc/blob/main/README.md) | [简体中文](https://github.com/dyuu7/dataioc/blob/main/README.zh-CN.md) | [Documentation](https://dyuu7.github.io/dataioc/) | [PyPI](https://pypi.org/project/dataioc/)

[![CI](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml/badge.svg)](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml)

## A small example

The classes below declare local relationships: `Features` needs `Samples`, and `Report` needs `Features`. Neither class has to describe the complete path from raw samples to a report.

<img src="https://raw.githubusercontent.com/dyuu7/dataioc/main/docs/assets/data-flow.png" width="480" alt="Samples feed Features, which feed Report. An alternative provider supplies Features directly, without Samples." />

```python
from dataioc import DataDescriptor, DataIoC


class Samples(DataDescriptor):
    pass


class Features(DataDescriptor):
    def __build__(self, data):
        values = data[Samples]
        mean = sum(values) / len(values)
        return mean, max(values)


class Report(DataDescriptor):
    def __build__(self, data):
        mean, peak = data[Features]
        return f"mean={mean:g}, peak={peak:g}"


data = DataIoC().add(Samples, (1, 2, 6))
assert data[Report] == "mean=3, peak=6"
assert data[Features] is data[Features]
```

Looking up `Report` expands the graph `Report -> Features -> Samples`. Each `__build__` is ordinary Python; the container supplies the dependency context, chooses the order of evaluation, and reuses values already built in that container.

A separate run can bind `Features` to a stored or externally computed value, without supplying `Samples`:

```python
saved = DataIoC()
saved.add_provider(Features, lambda _: (10, 12))
assert saved[Report] == "mean=10, peak=12"
```

The definition of `Report`, including its dependency request, has not changed. The source choice appears only where the container is assembled.

## When it helps

For a short pipeline with fixed inputs, ordinary function arguments are usually clearer. A container becomes useful when the calculation graph stays the same while data moves between live measurements, recorded data, simulations, persisted intermediates, and estimates. Providers keep that choice in the container setup instead of passing it through the domain code.

`IndexedData` covers another recurring case: applying one calculation graph to several related data groups. During a build, dependencies without an explicit ID inherit the current group's ID, while explicitly indexed dependencies remain fixed. The same model definitions can therefore be reused across sensors, samples, or experiments without duplicating their classes. See [indexed data](https://dyuu7.github.io/dataioc/indexed-data/) for the exact rules.

Builders remain regular Python callables or `__build__` methods. Existing Python objects can be registered directly, and the core package does not import NumPy. dataioc provides the dependency graph runtime; a domain package can layer its own concepts, composition operators, and model vocabulary on top of it.

## Origin

This pattern was developed while working on magnetic interference compensation in [deinterf](https://github.com/dyuu7/deinterf). Its [direction-cosine example](https://github.com/dyuu7/deinterf/blob/main/examples/replace_direction_cosine_source_tmi.py) switches the source between magnetic-vector measurements and an inertial-navigation estimate while the model terms that consume direction cosines stay unchanged. A second example [adds a load-vibration term](https://github.com/dyuu7/deinterf/blob/main/examples/extended_load_vibration_tmi.py) by composition.

Those examples use the container embedded in deinterf together with its model layer. dataioc extracts the dependency resolution and provider mechanism so it can be used with other domain models.

The same structure appears in [dvmss](https://github.com/dyuu7/dvmss), a vehicle magnetic sensor simulation. Its `Tmi` quantity depends on `MagVectorXYZ` and `BackgroundFieldXYZ`; those quantities declare further dependencies such as `IGRF`, `InertialAttitude`, `PermanentFieldXYZ`, and `InducedFieldXYZ`. The application provides leaf data such as position, date, attitude, and magnetic source parameters, then requests `data[Tmi]`. The container expands and caches the intermediate quantities. dvmss currently uses the container from deinterf, so it documents the design's lineage and its use across compensation and simulation models.

## Scope

The graph is an executable dependency model, not a general-purpose workflow scheduler. Resolution is synchronous and local to one process. Successfully built values, including `None`, are cached by key. Replacing a provider does not invalidate existing values or their dependents, so a new dataset or provider configuration should normally use a fresh container. Failed top-level builds print their dependency path before re-raising the original exception; successful paths can also be retained for diagnostics.

The container does not provide thread safety, asynchronous construction, automatic cache invalidation, or cycle detection.

- **Core:** Python 3.9+; no runtime dependencies on 3.11+, only `typing-extensions` on 3.9 and 3.10.
- **Arrays:** optional NumPy 1.26 and 2.x integration.
- **Distribution:** pure Python wheel with type information.

[CI](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml) checks Python 3.9 through 3.14, core imports without NumPy, type checking, builds, and NumPy compatibility cases.

## Install

```bash
python -m pip install dataioc
python -m pip install "dataioc[numpy]"
```

## Documentation

- [Quickstart](https://dyuu7.github.io/dataioc/quickstart/): build your first derived value.
- [Core concepts](https://dyuu7.github.io/dataioc/concepts/): understand descriptors, caching, and failure behavior.
- [Providers](https://dyuu7.github.io/dataioc/providers/): configure alternative sources.
- [Indexed data](https://dyuu7.github.io/dataioc/indexed-data/): work with multiple data groups.
- [NumPy](https://dyuu7.github.io/dataioc/numpy/): use array subclasses.
- [API](https://dyuu7.github.io/dataioc/api/): look up interfaces.

## Contributors

Primary container implementation: [yanang007](https://github.com/yanang007). Concept, extraction into an independent component, compatibility work, and maintenance: [dyuu7](https://github.com/dyuu7).

[![Contributors](https://contrib.rocks/image?repo=dyuu7/dataioc)](https://github.com/dyuu7/dataioc/graphs/contributors)

Licensed under the [MIT License](https://github.com/dyuu7/dataioc/blob/main/LICENSE).
