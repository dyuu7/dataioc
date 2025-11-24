# dataioc

**Declarative data dependencies and on-demand computation for Python.**

When calculations share inputs and intermediate values, changing a data source can affect many consumers. dataioc lets each calculation request the data it needs, with providers configured separately.

[English](https://github.com/dyuu7/dataioc/blob/main/README.md) | [简体中文](https://github.com/dyuu7/dataioc/blob/main/README.zh-CN.md) | [Documentation](https://dyuu7.github.io/dataioc/) | [PyPI](https://pypi.org/project/dataioc/)

[![CI](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml/badge.svg)](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml)

## One report, two data sources

Derive `Features` from `Samples`, or supply precomputed features through a provider. `Report` uses the same dependency in both cases.

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

Each `__build__` is ordinary Python. Requesting `Report` builds its dependencies on demand; subsequent reads reuse cached values in that container.

A second container can provide `Features` directly, without any `Samples`:

```python
saved = DataIoC()
saved.add_provider(Features, lambda _: (10, 12))
assert saved[Report] == "mean=10, peak=12"
```

The report definition stays the same. Computation rules and data sources can be reused and configured independently.

## In practice: magnetic interference compensation

The same dependency pattern is used in [deinterf](https://github.com/dyuu7/deinterf). Its [direction-cosine example](https://github.com/dyuu7/deinterf/blob/main/examples/replace_direction_cosine_source_tmi.py) switches between magnetic-vector measurements and an inertial-navigation estimate while preserving the consuming model terms. Another [example adds a load-vibration term](https://github.com/dyuu7/deinterf/blob/main/examples/extended_load_vibration_tmi.py) by composition.

These examples use deinterf's embedded container and application-specific model composition. dataioc provides the reusable dependency and provider abstraction for applications with their own domain logic.

## Fit and verification

Use dataioc for derived measurements, feature generation, alternative data sources, and [multiple datasets sharing computation rules](https://dyuu7.github.io/dataioc/indexed-data/).

- **Core:** Python 3.9+; no runtime dependencies on 3.11+, only `typing-extensions` on 3.9 and 3.10.
- **Arrays:** optional NumPy 1.26 and 2.x integration.
- **Distribution:** pure Python wheel with type information.

[CI](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml) checks Python 3.9 through 3.14, core imports without NumPy, type checking, builds, and NumPy compatibility cases.

Evaluation is synchronous. Cached dependents are not automatically invalidated; configure providers before first access. See [cache behavior and limits](https://dyuu7.github.io/dataioc/concepts/).

## Install and explore

```bash
python -m pip install dataioc
python -m pip install "dataioc[numpy]"
```

- [Quickstart](https://dyuu7.github.io/dataioc/quickstart/): build your first derived value.
- [Providers](https://dyuu7.github.io/dataioc/providers/): configure alternative sources.
- [Indexed data](https://dyuu7.github.io/dataioc/indexed-data/): work with multiple data groups.
- [NumPy](https://dyuu7.github.io/dataioc/numpy/): use array subclasses.
- [API](https://dyuu7.github.io/dataioc/api/): look up interfaces.
- [Development](https://dyuu7.github.io/dataioc/maintenance/): run checks and contribute.

## Contributors

Primary container implementation: [yanang007](https://github.com/yanang007). Concept, extraction into an independent component, compatibility work, and maintenance: [dyuu7](https://github.com/dyuu7).

[![Contributors](https://contrib.rocks/image?repo=dyuu7/dataioc)](https://github.com/dyuu7/dataioc/graphs/contributors)

Licensed under the [MIT License](https://github.com/dyuu7/dataioc/blob/main/LICENSE).
