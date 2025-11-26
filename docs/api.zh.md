# API 参考

本页提供接口签名与行为约定。完整建模过程见[快速开始](quickstart.zh.md)，来源替换与多采集通道的组织方式分别见 [Provider](providers.zh.md) 和[索引数据](indexed-data.zh.md)。

| 接口 | 在光伏购电模型中的用途 |
| --- | --- |
| `DataDescriptor` | 标识日照强度、光伏功率、购电量与费用，并为派生量定义公式 |
| `DataIoC` | 注册输入与 provider，按需计算并缓存结果 |
| `IndexedData` | 将传感器读数组织为带索引的数据对象 |
| `UniqueData` | 使电价等数据在多个采集通道之间共享 |
| `DataNDArray` | 将逐小时日照数据表示为支持索引的 NumPy 数组 |

## 核心

::: dataioc.DataIoC
    options:
      members:
        - with_data
        - add
        - add_provider
        - __getitem__
        - __setitem__
        - find_builder
        - logger
      show_root_heading: true
      show_source: false

::: dataioc.DataDescriptor
    options:
      show_root_heading: true
      show_source: false

::: dataioc.IndexedData
    options:
      show_root_heading: true
      show_source: false

::: dataioc.UniqueData
    options:
      show_root_heading: true
      show_source: false

## NumPy

::: dataioc.DataNDArray
    options:
      show_root_heading: true
      show_source: false
