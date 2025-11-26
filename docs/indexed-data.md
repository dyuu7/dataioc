# Indexed data

Multiple sensors of the same type may measure the same physical quantity. Indices distinguish these data instances so that the same calculation rules can be applied to each acquisition channel. This page applies the solar model from [Quickstart](quickstart.md) to two irradiance sensors and compares the electricity costs associated with their readings. Panel area, efficiency, load power, duration, and price are identical.

## Register multiple acquisition channels

For the scalar descriptor in Quickstart, values can be registered separately with `add(Irradiance[0], 0.8)` and `add(Irradiance[1], 0.6)`. When existing data is organized into objects, `IndexedData` supports registration by object type and index through `with_data`.

Here `Irradiance` is defined as a data object with a `value` field, which `SolarPower` reads. The grid energy and cost formulas are the same as in the README:

```python
from dataclasses import dataclass

from dataioc import DataDescriptor, DataIoC, IndexedData, UniqueData


@dataclass
class Irradiance(IndexedData):
    value: float  # kW/m²


class SolarPower(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        efficiency = 0.2
        panel_area = 10.0  # m²
        return efficiency * panel_area * data[Irradiance].value  # kW


class GridEnergy(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        load_power = 3.0  # kW
        duration = 1.0  # h
        return max(load_power - data[SolarPower], 0.0) * duration  # kWh


class ElectricityCost(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        price = 1.0  # CNY/kWh
        return data[GridEnergy] * price  # CNY


data = DataIoC().with_data(
    Irradiance(0.8),
    Irradiance[1](0.6),
)
```

IDs 0 and 1 represent two sensors. A descriptor dependency without an explicit index is a weak reference during a build and inherits the current target's ID. A request for `ElectricityCost[1]` therefore resolves `GridEnergy[1]`, `SolarPower[1]`, and `Irradiance[1]`, without specifying the sensor in every calculation rule.

```python
assert round(data[ElectricityCost[0]], 2) == 1.40
assert round(data[ElectricityCost[1]], 2) == 1.80
assert data[Irradiance] is data[Irradiance[0]]
```

The two readings produce solar power estimates of 1.6 kW and 1.2 kW, with electricity costs of 1.4 CNY and 1.8 CNY, respectively. These model results are cached separately for each acquisition channel.

Outside a build, an unindexed `Irradiance` refers to ID 0. Values created with `Irradiance[1](...)` carry the corresponding descriptor, and `with_data` registers them under that key.

## Refer to one group explicitly

A comparison between sensor results can use a fixed baseline channel. This derived quantity calculates the difference in electricity cost between the current channel and channel 0, in CNY:

```python
class CostDifferenceFromBaseline(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        baseline = data[ElectricityCost[0]]
        current = data[ElectricityCost]
        return current - baseline


assert round(data[CostDifferenceFromBaseline[0]], 2) == 0.00
assert round(data[CostDifferenceFromBaseline[1]], 2) == 0.40
```

`ElectricityCost[0]` is a strong reference and always selects group 0. The unindexed `ElectricityCost` remains weak and inherits the ID of `CostDifferenceFromBaseline`. The cost for index 1 is 0.4 CNY higher than the baseline.

## Rebind a descriptor

`index_implicit(id)` preserves an existing strong ID. Subscription explicitly rebinds the descriptor and leaves the original unchanged:

```python
original = ElectricityCost[1]
assert original.index_implicit(2) is original
assert original[2].id == 2
assert original.id == 1
```

## Share data across groups

Ordinary Python types are shared across build IDs. Mix `UniqueData` into an indexed class when it should also have one shared value. For example, the price previously fixed in the cost formula can be represented by a shared `Tariff`:

```python
@dataclass
class Tariff(IndexedData, UniqueData):
    price: float  # CNY/kWh


def cost_with_tariff(data: DataIoC) -> float:
    return data[GridEnergy] * data[Tariff].price


shared = DataIoC().with_data(
    Irradiance(0.8),
    Irradiance[1](0.6),
    Tariff(1.0),
)
shared.add_provider(ElectricityCost[0], cost_with_tariff)
shared.add_provider(ElectricityCost[1], cost_with_tariff)

assert shared[Tariff[0]] is shared[Tariff[1]]
assert round(shared[ElectricityCost[0]], 2) == 1.40
assert round(shared[ElectricityCost[1]], 2) == 1.80
```

Each acquisition channel uses its own `GridEnergy` and accesses the same tariff object. All inputs and provider bindings are configured in a new container before any results are requested.

Providers select sources or derivation methods, while indices distinguish data groups. These mechanisms can be combined, for example, to configure different calibration methods for different sensors; see [Providers](providers.md). Changes to inputs or bindings do not automatically invalidate existing cached results; see [Container lifetime and cache](concepts.md#container-lifetime-and-cache).

Continue with [NumPy support](numpy.md) to extend each sensor's single irradiance reading to an array of hourly values. See [API](api.md) for interface details.
