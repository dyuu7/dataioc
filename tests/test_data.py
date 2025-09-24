from dataclasses import dataclass
from functools import partial

import pytest

from dataioc import DataDescriptor, DataIoC, IndexedData, UniqueData


@dataclass
class Sensor(IndexedData):
    values: tuple[int, ...]

    @classmethod
    def __build__(cls, container):
        raise NotImplementedError("Sensor must be provided")


class Sum(DataDescriptor[int]):
    def __build__(self, container):
        return sum(container[Sensor].values)


class OffsetSensor0(DataDescriptor):
    def __build__(self, container):
        base = sum(container[Sensor[0]].values)
        return tuple(base + value for value in container[Sensor].values)


def test_weak_ids_follow_build_context_and_strong_ids_stay_fixed():
    container = DataIoC().with_data(Sensor((1, 1, 1)), Sensor[1]((2, 2, 2)))
    assert container[Sum[0]] == 3
    assert container[Sum] == 3
    assert container[Sum[1]] == 6
    assert container[OffsetSensor0[0]] == (4, 4, 4)
    assert container[OffsetSensor0[1]] == (5, 5, 5)
    assert container[Sensor] is container[Sensor[0]]


def test_explicit_reindexing_overrides_strong_id_without_mutation():
    original = Sum[1]
    assert original.index_implicit(2) is original
    assert original[2].id == 2
    assert original.index_explicit(3).id == 3
    assert original.id == 1
    assert Sum().index_implicit(2).id == 2
    assert Sum() == Sum[0]
    assert hash(Sum()) == hash(Sum[0])


@pytest.mark.parametrize("result", [None, False, 0, (), object()])
def test_lazy_builds_are_cached_even_when_result_is_none(result):
    calls = []

    def build(container):
        calls.append(container)
        return result

    container = DataIoC().add_provider(Sum[0], build)
    assert not calls
    assert container[Sum[0]] is result
    assert container[Sum[0]] is result
    assert len(calls) == 1


def test_explicit_data_and_strict_registration():
    container = DataIoC(allow_implicit_registering=False)
    with pytest.raises(RuntimeError, match="Builder.*not found"):
        container[Sum[1]]
    container.add(Sum[1]).with_data(Sensor[1]((2, 3)))
    assert container[Sum[1]] == 5
    container.add(str, "value").add(42)
    assert container[str] == "value"
    assert container[int] == 42
    container[Sensor[0]] = None
    assert container[Sensor] is None


def test_unique_and_ordinary_types_are_shared_between_ids():
    @dataclass
    class Calibration(IndexedData, UniqueData):
        offset: int

    class Adjusted(DataDescriptor):
        def __build__(self, container):
            return container[Calibration].offset + container[int] + container[Sum]

    container = DataIoC().with_data(
        Calibration(10), 100, Sensor[1]((1,)), Sensor[2]((2,))
    )
    assert container[Adjusted[1]] == 111
    assert container[Adjusted[2]] == 112
    assert container[Calibration[99]] is container[Calibration]


def test_class_provider_remaps_weak_dependencies_for_each_id():
    class Result(IndexedData):
        pass

    def doubled(container):
        return 2 * container[Sum]

    container = DataIoC(record_all=True).with_data(
        Sensor((1,)), Sensor[1]((3,)), Sensor[2]((5,))
    )
    container.add_provider(Result, doubled)
    container.add_provider(Result[2], lambda _: 99)
    assert container[Result] == 2
    assert container[Result[1]] == 6
    assert container[Result[2]] == 99
    assert "doubled" in str(container.logger)


def test_provider_replacement_before_resolution_preserves_existing_cache():
    container = DataIoC().add_provider(Sum[0], lambda _: 1)
    container.add_provider(Sum[0], lambda _: 2)
    assert container[Sum[0]] == 2
    container.add_provider(Sum[0], lambda _: 3)
    assert container[Sum[0]] == 2


def test_descriptor_and_callable_object_providers():
    class DoubleSum(DataDescriptor):
        def __build__(self, container):
            return 2 * container[Sum]

    container = DataIoC().with_data(Sensor[1]((3,)))

    class Result(IndexedData):
        pass

    container.add_provider(Result[1], DoubleSum())
    assert container[Result[1]] == 6
    container.add_provider(str, partial(lambda prefix, _: prefix, "value"))
    assert container[str] == "value"


def test_logger_records_dependencies_and_clears_successful_accesses():
    container = DataIoC(record_all=True).with_data(Sensor[1]((2,)))
    assert container[Sum[1]] == 2
    tree = str(container.logger)
    assert "Sum[1]" in tree
    assert "Sensor[1]" in tree
    assert "/Created/" in tree
    assert container.logger.at_root
    container.logger.clear()
    assert not container.logger.root
    container.record_all = False
    assert container[Sum[1]] == 2
    assert not container.logger.root


def test_failed_build_prints_dependency_tree_and_can_be_retried(capsys):
    container = DataIoC()
    with pytest.raises(NotImplementedError, match="Sensor must be provided"):
        container[Sum[1]]
    output = capsys.readouterr().out
    assert "Sum[1]" in output
    assert "Sensor[1]" in output
    assert "X" in output
    assert container.logger.at_root
    container.with_data(Sensor[1]((4,)))
    assert container[Sum[1]] == 4


def test_base_descriptor_requires_data():
    with pytest.raises(NotImplementedError, match="must be provided"):
        DataIoC()[DataDescriptor()]


def test_descriptor_class_access_matches_default_instance():
    container = DataIoC(allow_implicit_registering=False).with_data(Sensor((3,)))
    container.add(Sum)
    assert container[Sum] == container[Sum()] == 3


def test_invalid_provider_is_rejected_at_registration():
    with pytest.raises(TypeError, match="provider must"):
        DataIoC().add_provider(Sum[0], object())


def test_logger_manual_entry_uses_last_child_node():
    logger = DataIoC().logger
    with pytest.raises(RuntimeError, match="No dependency"):
        logger.enter()
    with logger.add(Sum[1]):
        assert not logger.at_root
    with logger:
        assert logger.at_level0
    assert logger.at_root
