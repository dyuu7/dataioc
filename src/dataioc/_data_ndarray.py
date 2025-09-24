from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import ArrayLike

from ._data import DataIoC, IndexedData, IndexedDataIoC


def is_homogeneous(inp: np.ndarray, out: np.ndarray):
    if inp.shape != out.shape:
        # 不允许数组尺寸发生改变
        return False
    if out.dtype != np.promote_types(inp.dtype, out.dtype):
        # 输出只允许类型抬升
        return False

    return True


class DataNDArray(np.ndarray, IndexedData):
    def __new__(cls, *arrays: ArrayLike, force_column_stack=False, **kwargs):
        if not arrays:
            raise ValueError("At least one array is required.")
        converted = [np.asarray(array) for array in arrays]
        if any(array.ndim == 0 for array in converted):
            raise TypeError("Arrays must have at least one dimension.")
        if len({len(array) for array in converted}) != 1:
            raise ValueError("Arrays have inconsistent numbers of samples.")
        if force_column_stack or len(arrays) > 1:
            return np.column_stack(converted).view(cls)
        else:
            return converted[0].view(cls)

    def __array_finalize__(self, obj, **__):
        pass

    def __array_ufunc__(self, ufunc, method, *inputs, out=None, **kwargs):
        typ = type(self)

        inputs = tuple(
            np.asarray(inp) if isinstance(inp, typ) else inp for inp in inputs
        )
        if out is not None:
            out = tuple(np.asarray(o) if isinstance(o, typ) else o for o in out)
            kwargs["out"] = out

        ret = getattr(ufunc, method)(*inputs, **kwargs)

        if ret is NotImplemented:
            return NotImplemented

        if isinstance(ret, np.ndarray) and is_homogeneous(self, ret):
            return ret.view(typ)
        else:
            return ret

    def reshape(self, *shape, **kwargs) -> Any:
        return self.view(np.ndarray).reshape(*shape, **kwargs)

    def __getitem__(self, item):
        return super().__getitem__(item).view(np.ndarray)

    @classmethod
    def __build__(cls, container: DataIoC | IndexedDataIoC):
        id_str = f"[{container.id}]" if isinstance(container, IndexedDataIoC) else ""
        raise NotImplementedError(f"{cls.__name__}{id_str} must be provided.")
