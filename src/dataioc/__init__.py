"""Lazy, indexed data dependency injection without mandatory numerical libraries."""

from typing import TYPE_CHECKING

from ._data import (
    DataDescriptor,
    DataIoC,
    DescribedData,
    IndexedData,
    IndexedDataIoC,
    IndexedDataMeta,
    IndexedDataTypeDescriptor,
    SupportsBuild,
    UniqueData,
)

if TYPE_CHECKING:
    from ._data_ndarray import DataNDArray as DataNDArray

__version__ = "0.1.0"

__all__ = [
    "DataDescriptor",
    "DataIoC",
    "DescribedData",
    "IndexedData",
    "IndexedDataIoC",
    "IndexedDataMeta",
    "IndexedDataTypeDescriptor",
    "SupportsBuild",
    "UniqueData",
]


def __getattr__(name: str):
    if name == "DataNDArray":
        from ._data_ndarray import DataNDArray

        return DataNDArray
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
