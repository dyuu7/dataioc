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
    assert np.add.at(sensor, [0], 2) is None
    assert sensor[0] == 3


@pytest.mark.parametrize("output_type", [np.ndarray, Sensor])
def test_ufunc_out_preserves_output_identity(output_type):
    sensor = Sensor([1.0, 2.0])
    output = np.empty(2).view(output_type)

    result = np.add(sensor, 3, out=output)

    assert result is output
    np.testing.assert_array_equal(output, [4.0, 5.0])


def test_inplace_ufunc_preserves_registered_array_identity():
    sensor = Sensor([1.0, 2.0])
    container = DataIoC().with_data(sensor)
    sensor += 3

    assert sensor is container[Sensor]
    np.testing.assert_array_equal(sensor, [4.0, 5.0])


def test_multi_output_ufunc_preserves_homogeneous_subclasses():
    sensor = Sensor([1.5, -2.25])
    actual = np.modf(sensor)
    expected = np.modf(np.asarray(sensor))

    for result, reference in zip(actual, expected):
        assert isinstance(result, Sensor)
        np.testing.assert_array_equal(result, reference)


def test_multi_output_ufunc_preserves_provided_outputs_and_allocates_missing_ones():
    sensor = Sensor([1.5, -2.25])
    output = np.empty(2)
    fraction, integral = np.modf(sensor, out=(output, None))

    assert fraction is output
    assert isinstance(integral, Sensor)
    np.testing.assert_array_equal(fraction, [0.5, -0.25])
    np.testing.assert_array_equal(integral, [1.0, -2.0])


def test_ufunc_methods_match_numpy_shapes_and_outputs():
    sensor = Sensor([1.0, 2.0, 3.0])
    output = np.empty(())

    assert np.add.reduce(sensor, out=output) is output
    assert output == 6
    accumulated = np.add.accumulate(sensor)
    assert isinstance(accumulated, Sensor)
    np.testing.assert_array_equal(accumulated, [1.0, 3.0, 6.0])
    outer = np.add.outer(sensor, sensor)
    assert type(outer) is np.ndarray
    np.testing.assert_array_equal(
        outer, np.add.outer(np.asarray(sensor), np.asarray(sensor))
    )


@pytest.mark.parametrize(
    ("dtype", "scalar"),
    [(np.float32, 3.0), (np.float32, np.float64(3.0)), (np.int8, 255)],
)
def test_scalar_promotion_follows_the_installed_numpy_version(dtype, scalar):
    array = np.array([1, 2], dtype=dtype)
    sensor = Sensor(array)

    try:
        expected = np.add(array, scalar)
    except OverflowError:
        with pytest.raises(OverflowError):
            np.add(sensor, scalar)
    else:
        actual = np.add(sensor, scalar)
        assert actual.dtype == expected.dtype
        np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize(
    "array",
    [
        np.array([1.0]),
        np.array([True]),
        np.array(["text"]),
        np.array(["text"], dtype=object),
    ],
)
def test_scalar_indexing_preserves_numpy_or_python_scalar_type(array):
    scalar = Sensor(array)[0]
    assert type(scalar) is type(array[0])
    assert scalar == array[0]


@pytest.mark.skipif(
    not hasattr(np.dtypes, "StringDType"), reason="StringDType requires NumPy 2"
)
def test_numpy2_string_dtype_comparison_returns_plain_boolean_array():
    array = np.array(["a", "b"], dtype=np.dtypes.StringDType())
    sensor = Sensor(array)
    result = sensor == "a"

    assert type(result) is np.ndarray
    np.testing.assert_array_equal(result, array == "a")
    assert type(sensor[0]) is type(array[0])
    assert sensor[0] == array[0]


def test_array_conversion_preserves_copy_and_view_semantics():
    array = np.array([1.0, 2.0])
    sensor = Sensor(array)
    view = np.asarray(sensor)
    copied = np.array(sensor, copy=True)

    assert type(view) is np.ndarray
    assert np.shares_memory(array, sensor)
    assert np.shares_memory(sensor, view)
    assert not np.shares_memory(sensor, copied)
    np.testing.assert_array_equal(copied, sensor)


def test_missing_array_reports_sensor_id():
    with pytest.raises(NotImplementedError, match=r"Sensor\[2\].*provided"):
        DataIoC()[Sensor[2]]
