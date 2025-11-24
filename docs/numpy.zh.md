# NumPy 支持

安装可选 extra：

```bash
python -m pip install "dataioc[numpy]"
```

继承 `DataNDArray` 定义数组类型：

```python
from dataioc import DataIoC, DataNDArray


class SensorArray(DataNDArray):
    pass


container = DataIoC().with_data(
    SensorArray([1, 1, 1]),
    SensorArray[1]([2, 2, 2]),
)
assert container[SensorArray[1]].sum() == 6
```

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
