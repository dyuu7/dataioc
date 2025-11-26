# dataioc

**Declarative data dependency graphs for Python.**

Each `DataDescriptor` names a quantity and defines how it is derived from its direct dependencies. `DataIoC` composes these local rules into a graph, then resolves and caches only the subgraph required by the requested result. A provider binding replaces a quantity's source or derivation without changing downstream calculations.

## Start with the solar electricity model

These guides continue the README's solar example: estimate solar power from irradiance, then calculate the building's grid energy and electricity cost. Planning uses a formula to estimate power, while operational analysis uses measured power. Both sources use the same grid energy and cost formulas.

| Quantity | Meaning | Scalar model unit |
| --- | --- | --- |
| `Irradiance` | Solar irradiance | kW/m² |
| `SolarPower` | Solar power output | kW |
| `GridEnergy` | Purchased electricity | kWh |
| `ElectricityCost` | Cost of purchased electricity | CNY |

![Solar power is estimated from irradiance or supplied as a measurement by a provider, with the same downstream grid energy and cost formulas.](https://raw.githubusercontent.com/dyuu7/dataioc/main/docs/assets/data-flow.png)

[Quickstart](quickstart.md) reproduces the README's costs of 1.4 CNY and 1.8 CNY. Subsequent chapters extend this model with alternative derivations, multiple sensors, and arrays of hourly values. Each guide is self-contained; execute the code blocks within a page in order.

## Reading path

1. [Quickstart](quickstart.md): register irradiance data, define formulas, request electricity cost, and substitute measured power.
2. [Core concepts](concepts.md): understand quantities, builders, dependency resolution, caching, and failure behavior.
3. [Providers](providers.md): supply measured solar power or use a derivation that accounts for losses.
4. [Indexed data](indexed-data.md): distinguish multiple irradiance sensors, reuse calculation rules, and share a tariff.
5. [NumPy support](numpy.md): extend individual readings to hourly arrays and calculate the cost for the full period.
6. [API reference](api.md): look up the interfaces used by the model and their detailed contracts.

Providers select sources or derivation methods for the same physical quantity, while indices distinguish data from multiple acquisition channels. These mechanisms can be combined, for example, to configure a separate calibration method for each sensor.

A container represents a fixed set of inputs and provider bindings and can contain multiple indexed data groups. Computed results are cached; use a new container to recompute results after changes to inputs or bindings. See [Core concepts](concepts.md) for details.

## Install

```bash
python -m pip install dataioc
python -m pip install "dataioc[numpy]"
```

The core package has no mandatory numerical dependency. Install the `numpy` extra when using `DataNDArray`.

## Project links

- [GitHub repository and README](https://github.com/dyuu7/dataioc)
- [Contributors](https://github.com/dyuu7/dataioc#contributors)
