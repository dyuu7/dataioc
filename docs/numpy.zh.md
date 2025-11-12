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

支持范围是 `numpy>=1.26,<3`，包括 NumPy 1.26 和 2.x。解析器会根据 Python 版本选择兼容的最新版本。

当结果形状不变且 dtype 兼容时，`DataNDArray` 会保留数组子类。支持多输出 ufunc、显式 `out`数组和原地操作。

切片、reshape 和标量索引遵循 [API 参考](api.zh.md)中的行为说明。数值提升遵循当前安装的NumPy 版本，因此 NumPy 1.x 和 2.x 的结果 dtype 可能不同。
