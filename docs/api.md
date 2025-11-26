# API reference

This page provides interface signatures and behavioral contracts. See [Quickstart](quickstart.md) for the complete model, [Providers](providers.md) for source substitution, and [Indexed data](indexed-data.md) for organizing multiple acquisition channels.

| Interface | Role in the solar electricity model |
| --- | --- |
| `DataDescriptor` | Identify irradiance, solar power, grid energy, and cost, and define formulas for derived quantities |
| `DataIoC` | Register inputs and providers, then compute and cache results on demand |
| `IndexedData` | Represent sensor readings as indexed data objects |
| `UniqueData` | Share data such as the electricity tariff across acquisition channels |
| `DataNDArray` | Represent hourly irradiance as an indexed NumPy array |

## Core

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
