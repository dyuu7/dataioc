# dataioc

**Declarative data dependency graphs for Python.**

Each `DataDescriptor` names a quantity and defines how it is derived from its direct dependencies. `DataIoC` composes these local rules into a graph, then resolves and caches only the subgraph required by the result you request. Bind a provider to any quantity to replace that part of the graph without changing downstream calculations.

[English](https://github.com/dyuu7/dataioc/blob/main/README.md) | [简体中文](https://github.com/dyuu7/dataioc/blob/main/README.zh-CN.md) | [Documentation](https://dyuu7.github.io/dataioc/) | [PyPI](https://pypi.org/project/dataioc/)

[![CI](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml/badge.svg)](https://github.com/dyuu7/dataioc/actions/workflows/ci.yml)

## Example

The raw readings `10`, `20`, and `60` represent measurements of `1`, `2`, and `6`.

<img src="https://raw.githubusercontent.com/dyuu7/dataioc/main/docs/assets/data-flow.png" width="720" alt="By default, RawReadings are converted into Measurements. When a provider binds recorded data to Measurements, that default derivation is replaced while Statistics and Report remain unchanged." />

```python
from dataioc import DataDescriptor, DataIoC


class RawReadings(DataDescriptor):
    pass


class Measurements(DataDescriptor):
    def __build__(self, data):
        return tuple(value / 10 for value in data[RawReadings])


class Statistics(DataDescriptor):
    def __build__(self, data):
        values = data[Measurements]
        return sum(values) / len(values), max(values)


class Report(DataDescriptor):
    def __build__(self, data):
        mean, peak = data[Statistics]
        return f"mean={mean:g}, peak={peak:g}"


data = DataIoC().add(RawReadings, (10, 20, 60))
assert data[Report] == "mean=3, peak=6"
assert data[Measurements] is data[Measurements]
```

`data[Report]` is the only request the caller has to make. The container follows the dependencies and caches each value it builds.

To use recorded measurements instead, bind a provider for `Measurements`:

```python
recorded = DataIoC().add_provider(Measurements, lambda _: (1.0, 2.0, 6.0))
assert recorded[Report] == "mean=3, peak=6"
```

`RawReadings` is no longer needed; `Statistics` and `Report` stay as they are.

## When it helps

If both the inputs and the calculation path are fixed, ordinary function calls are simpler. Use `dataioc` when the relationships stay stable but a value may come from live measurements, recorded data, a simulation, or an estimate.

`dataioc` grew out of [deinterf](https://github.com/dyuu7/deinterf). In its [direction-cosine example](https://github.com/dyuu7/deinterf/blob/main/examples/replace_direction_cosine_source_tmi.py), the same compensation terms work whether direction cosines are derived from magnetic-vector measurements or supplied by an INS estimate. [dvmss](https://github.com/dyuu7/dvmss) applies the pattern to simulation: supply the inputs, request `Tmi`, and let the container resolve the intermediate quantities.

## Scope

`dataioc` resolves data dependencies synchronously in the current process; it is not a workflow scheduler. Use a fresh container for each dataset or provider configuration. See [Core concepts](https://dyuu7.github.io/dataioc/concepts/) for caching, diagnostics, and other runtime limits.

## Install

```bash
python -m pip install dataioc
python -m pip install "dataioc[numpy]"
```

## Documentation

- [Quickstart](https://dyuu7.github.io/dataioc/quickstart/): build a result from local dependency rules.
- [Core concepts](https://dyuu7.github.io/dataioc/concepts/): understand descriptors, builders, caching, and failure behavior.
- [Providers](https://dyuu7.github.io/dataioc/providers/): bind a quantity to another source or derivation.
- [Indexed data](https://dyuu7.github.io/dataioc/indexed-data/): reuse one model across related data groups.
- [NumPy](https://dyuu7.github.io/dataioc/numpy/): use array subclasses.
- [API](https://dyuu7.github.io/dataioc/api/): look up interfaces.

## Contributors

[yanang007](https://github.com/yanang007) wrote the original container. [dyuu7](https://github.com/dyuu7) shaped the design, extracted it into `dataioc`, and maintains the project.

[![Contributors](https://contrib.rocks/image?repo=dyuu7/dataioc)](https://github.com/dyuu7/dataioc/graphs/contributors)

Licensed under the [MIT License](https://github.com/dyuu7/dataioc/blob/main/LICENSE).
