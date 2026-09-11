from __future__ import annotations

from typing import Any, Union

import numpy as np
from numpy.typing import ArrayLike

from ._data import DataIoC, IndexedData, IndexedDataIoC


def is_homogeneous(inp: np.ndarray, out: np.ndarray):
    """Whether a ufunc result can safely retain the input array subclass."""
    if inp.shape != out.shape:
        # Array shape changes do not preserve the data type's structure.
        return False
    try:
        promoted_dtype = np.promote_types(inp.dtype, out.dtype)
    except TypeError:
        # Dtypes such as StringDType and bool have no common promoted dtype.
        return False
    if out.dtype != promoted_dtype:
        # Results may retain the subclass only through dtype promotion.
        return False

    return True


class DataNDArray(np.ndarray, IndexedData):
    """NumPy array base class that participates in indexed data resolution.

    A single input array is viewed as the subclass without an unnecessary copy.
    Multiple input arrays must have the same sample count and are stacked as
    columns. Shape-preserving ufunc results retain the subclass when their dtype is
    the promoted input/output dtype. Slices and reshaped arrays are returned as
    plain ``numpy.ndarray`` instances.
    """

    def __new__(cls, *arrays: ArrayLike, force_column_stack=False, **kwargs):
        """Construct an indexed array from one or more array-like objects.

        Parameters
        ----------
        *arrays
            One or more array-like objects. Multiple inputs are stacked as columns.
        force_column_stack
            Stack a single input as one column instead of preserving its shape.
        **kwargs
            Additional arguments accepted by subclass constructors.

        Raises
        ------
        ValueError
            If no arrays are provided or their sample counts differ.
        TypeError
            If an input is scalar.
        """
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
            kwargs["out"] = tuple(
                np.asarray(o) if isinstance(o, typ) else o for o in out
            )

        ret = getattr(ufunc, method)(*inputs, **kwargs)

        if ret is NotImplemented:
            return NotImplemented

        results = ret if isinstance(ret, tuple) else (ret,)
        outputs = out if out is not None else (None,) * len(results)
        wrapped = []
        for result, output in zip(results, outputs):
            # Explicit outputs must retain their identity, including in-place updates.
            if output is not None:
                wrapped.append(output)
            elif isinstance(result, np.ndarray) and is_homogeneous(self, result):
                wrapped.append(result.view(typ))
            else:
                wrapped.append(result)
        return tuple(wrapped) if isinstance(ret, tuple) else wrapped[0]

    def reshape(self, *shape, **kwargs) -> Any:
        """Return a reshaped plain ``numpy.ndarray``."""
        return self.view(np.ndarray).reshape(*shape, **kwargs)

    def __getitem__(self, key):
        """Return slices as plain arrays while preserving NumPy scalar behavior."""
        result = super().__getitem__(key)
        return result.view(np.ndarray) if isinstance(result, np.ndarray) else result

    @classmethod
    def __build__(cls, container: Union[DataIoC, IndexedDataIoC]):
        """Require instances of the array subclass to be provided explicitly."""
        id_str = f"[{container.id}]" if isinstance(container, IndexedDataIoC) else ""
        raise NotImplementedError(f"{cls.__name__}{id_str} must be provided.")
