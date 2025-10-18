from typing import get_type_hints

import pytest

from dataioc import DataIoC, DataNDArray


@pytest.mark.parametrize(
    "method",
    [
        DataIoC.add,
        DataIoC.add_provider,
        DataIoC.with_data,
        DataIoC.__setitem__,
        DataIoC.find_builder,
        DataNDArray.__build__,
    ],
    ids=lambda method: method.__qualname__,
)
def test_public_method_annotations_can_be_resolved_at_runtime(method):
    assert get_type_hints(method)
