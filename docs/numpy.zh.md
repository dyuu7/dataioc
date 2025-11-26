# NumPy 支持

本页将[索引数据](indexed-data.zh.md)中的单次日照读数扩展为逐小时数组，继续使用 `Irradiance → SolarPower → GridEnergy → ElectricityCost` 模型，并增加时段总费用 `TotalElectricityCost`。

安装可选 extra：

```bash
python -m pip install "dataioc[numpy]"
```

## 逐小时计算购电费用

每个数组元素代表一个小时内的恒定功率条件，日照强度单位为 kW/m²。两个数组分别来自两个日照传感器，时间位置一一对应。面板面积为 10 m²，效率为 20%，用电功率为 3 kW，电价为 1 元/kWh；不考虑储能与余电上网收益。

`Irradiance` 继承 `DataNDArray`，可通过 `with_data` 注册带索引的数组。公式逐元素计算，`np.maximum` 对应标量模型中的 `max`：

```python
import numpy as np

from dataioc import DataDescriptor, DataIoC, DataNDArray


class Irradiance(DataNDArray):
    pass


class SolarPower(DataDescriptor[np.ndarray]):
    def __build__(self, data: DataIoC) -> np.ndarray:
        efficiency = 0.2
        panel_area = 10.0  # m²
        return efficiency * panel_area * np.asarray(data[Irradiance])  # kW


class GridEnergy(DataDescriptor[np.ndarray]):
    def __build__(self, data: DataIoC) -> np.ndarray:
        load_power = 3.0  # kW
        duration = 1.0  # h per element
        return np.maximum(load_power - data[SolarPower], 0.0) * duration  # kWh


class ElectricityCost(DataDescriptor[np.ndarray]):
    def __build__(self, data: DataIoC) -> np.ndarray:
        price = 1.0  # CNY/kWh
        return data[GridEnergy] * price  # CNY per element


class TotalElectricityCost(DataDescriptor[float]):
    def __build__(self, data: DataIoC) -> float:
        return float(data[ElectricityCost].sum())


data = DataIoC().with_data(
    Irradiance([0.8, 0.6, 0.0]),
    Irradiance[1]([0.6, 0.4, 0.0]),
)
np.testing.assert_allclose(data[ElectricityCost[0]], [1.4, 1.8, 3.0])
np.testing.assert_allclose(data[ElectricityCost[1]], [1.8, 2.2, 3.0])
assert round(data[TotalElectricityCost[0]], 2) == 6.20
assert round(data[TotalElectricityCost[1]], 2) == 7.00
```

索引区分传感器，数组元素区分时段。第一组输入在首小时得到与 README 相同的 1.4 元费用；第三小时日照为零，全部用电由电网提供，费用为 3 元。两组读数对应的三小时总费用分别为 6.2 元和 7 元。

`SolarPower` 使用 `np.asarray` 将输入作为普通数组参与计算，后续派生数组由各自的描述符标识。请求 `TotalElectricityCost` 后，逐小时费用及其依赖也已缓存，可直接复用。

## 使用实测功率数组

Provider 的使用方式与标量模型相同。输入为对应三个小时的实测功率时，可直接替换 `SolarPower`：

```python
measured = DataIoC().add_provider(
    SolarPower,
    lambda _: np.array([1.2, 1.0, 0.0]),  # kW
)
np.testing.assert_allclose(measured[ElectricityCost], [1.8, 2.0, 3.0])
assert round(measured[TotalElectricityCost], 2) == 6.80
```

此时无需提供日照数组，购电量与费用公式继续复用。三个小时的费用分别为 1.8 元、2 元和 3 元，总费用为 6.8 元。

数组长度、时段对应关系与单位由模型代码约定，容器不负责自动对齐时序数据。不同数据或 provider 配置需要重新求值时，应创建新容器；缓存行为见[核心概念](concepts.zh.md)。

## 兼容范围

支持范围是 `numpy>=1.26,<3`。Python 3.9 支持 NumPy 1.26 和 2.0；更新的 NumPy 版本需要更新的 Python。安装工具会选择兼容版本。

CI 测试 NumPy 1.26.0、最新 1.26、2.0.0 和最新稳定 2.x，同时覆盖 Python 3.9 至 3.14 的锁定依赖组合。

## 数组行为

| 操作 | 行为 |
| --- | --- |
| 多个输入数组 | 检查样本数量后按列拼接 |
| 形状保持的数值 ufunc | 结果 dtype 兼容时保留子类 |
| 多输出 ufunc | 对每个结果分别应用子类保留规则 |
| 显式 `out` 或原地操作 | 保持输出对象身份不变 |
| 切片或 reshape | 返回普通 NumPy 数组 |
| 标量索引或归约 | 遵循 NumPy 的标量行为 |

数值提升和溢出行为遵循当前安装的 NumPy 版本，因此 1.x 和 2.x 的结果 dtype 可能不同。

核心导入和 `from dataioc import *` 都不会导入 NumPy。显式导入 `DataNDArray` 才加载可选集成，此时需要已经安装 NumPy。

接口签名见 [API 参考](api.zh.md)。
