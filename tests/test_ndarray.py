import numpy as np
import pytest

from dataioc import DataIoC, DataNDArray


class Sensor(DataNDArray):
    pass


def test_array_construction_and_indexed_registration():
    sensor = Sensor([1, 2], [3, 4])
    np.testing.assert_array_equal(sensor, [[1, 3], [2, 4]])
    container = DataIoC().with_data(Sensor[1]([5, 6]))
    assert isinstance(container[Sensor[1]], Sensor)
    np.testing.assert_array_equal(container[Sensor[1]], [5, 6])
    assert Sensor([1, 2], force_column_stack=True).shape == (2, 1)


def test_array_construction_validates_inputs():
    with pytest.raises(ValueError, match="At least one"):
        Sensor()
    with pytest.raises(TypeError, match="dimension"):
        Sensor(1)
    with pytest.raises(ValueError, match="inconsistent"):
        Sensor([1], [2, 3])


def test_ufuncs_reductions_slices_and_reshape():
    sensor = Sensor([1.0, 2.0, 3.0])
    assert isinstance(sensor + 1, Sensor)
    assert type(sensor > 1) is np.ndarray
    assert sensor.sum() == 6
    assert type(sensor[:2]) is np.ndarray
    assert type(sensor.reshape(3, 1)) is np.ndarray
    assert sensor[0] == 1
    np.add.at(sensor, [0], 2)
    assert sensor[0] == 3


def test_missing_array_reports_sensor_id():
    with pytest.raises(NotImplementedError, match=r"Sensor\[2\].*provided"):
        DataIoC()[Sensor[2]]
