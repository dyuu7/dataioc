from __future__ import annotations

import contextlib
import copy
import inspect
import sys
from collections.abc import Callable
from typing import (
    Any,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    Union,
    cast,
    overload,
    runtime_checkable,
)

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

DataT = TypeVar("DataT")


@runtime_checkable
class SupportsBuild(Protocol):
    """Protocol for objects that can build a value from a data container."""

    def __build__(self, container: DataIoC) -> Any:
        """Build and return a value using ``container``."""
        ...


class DataDescriptor(Generic[DataT]):
    """Identify a value in ``DataIoC`` and optionally define how to build it.

    Parameters
    ----------
    id
        Data ID. When omitted, the descriptor is a weak reference to ID 0.

    Notes
    -----
    A ``DataDescriptor`` is used as a dictionary key, so its subclasses must remain
    hashable and comparable. A subclass satisfies this requirement automatically
    when each of its attributes is itself hashable and comparable.

    IDs distinguish multiple values of the same type. The default ID is ``0`` when
    no ID is specified. For example, readings from three sensors of the same type
    can be identified by ``Sensor``, ``Sensor[1]``, and ``Sensor[2]`` and mapped to
    different values in ``DataIoC``.

    Examples
    --------
    An unindexed descriptor such as ``SensorData`` has a weak ID and identifies a
    data type. When used to retrieve data inside ``__build__``, it is automatically
    rebound to the concrete ID currently being built.

    >>> from dataioc import DataDescriptor, DataIoC, DataNDArray
    >>>
    >>> class SensorData(DataNDArray):
    ...     def __new__(cls, data, **kwargs):
    ...         return super().__new__(cls, data, **kwargs)
    >>>
    >>> class Sum(DataDescriptor):
    ...     def __build__(self, container: DataIoC):
    ...         return container[SensorData].sum()  # SensorData follows Sum's ID
    >>>
    >>> container = DataIoC().with_data(
    ...     SensorData([1, 1, 1]), SensorData[1]([2, 2, 2])
    ... )
    >>> print(container[Sum[0]], container[Sum[1]])
    3 6

    An explicitly indexed descriptor such as ``SensorData[1]`` has a strong ID and
    identifies one specific data group. It is not rebound inside ``__build__``.

    >>> class OffsetSensor0(DataDescriptor):
    ...     def __build__(self, container: DataIoC):
    ...         base = container[SensorData[0]].sum()  # Explicitly read ID 0
    ...         return base + container[SensorData]
    >>>
    >>> print(container[OffsetSensor0[0]], container[OffsetSensor0[1]])
    [4 4 4] [5 5 5]
    """

    __slots__ = ["_id"]
    DefaultWeakID = -1
    DefaultID = -DefaultWeakID - 1

    def __init__(self, id=DefaultWeakID) -> None:
        self.id = id

    @property
    def id(self):
        """The non-negative data ID represented by this descriptor."""
        if self.signed_id < 0:
            return -self.signed_id - 1
        else:
            return self.signed_id

    @id.setter
    def id(self, val):
        self._id = val

    @property
    def signed_id(self):
        """The internal signed ID, where a negative value marks a weak binding."""
        return self._id

    @property
    def is_weak_id(self):
        """Whether this descriptor may inherit the current build ID."""
        return self.signed_id < 0

    def __build__(self, container: DataIoC) -> DataT:
        """Build the value identified by this descriptor.

        Subclasses override this method to request dependencies from ``container``
        and return the resulting value. The base implementation requires the value
        to be provided explicitly.

        Parameters
        ----------
        container
            Container used to resolve dependencies.

        Returns
        -------
        DataT
            The constructed value.

        Raises
        ------
        NotImplementedError
            If the subclass does not provide a builder.
        """
        raise NotImplementedError(f"{self!r} must be provided.")

    def index_implicit(self, new_index):
        """Weakly rebind to ``new_index``, preserving an existing strong ID."""
        return self.index(new_index, weak=True)

    def index_explicit(self, new_index):
        """Explicitly rebind to ``new_index``, overriding any existing ID."""
        return self.index(new_index, weak=False)

    def index(self, new_index, weak=True):
        """Bind this descriptor to another ID for related values of the same type.

        For example, readings from three sensors of the same type can be identified
        by:

        * ``Sensor[0]``
        * ``Sensor[1]``
        * ``Sensor[2]``

        Parameters
        ----------
        new_index
            New data ID.
        weak
            Whether the rebinding is weak. A weak rebinding has no effect when this
            descriptor already has a strong ID.

        Returns
        -------
        DataDescriptor
            This descriptor if a weak rebinding is blocked by a strong ID;
            otherwise, a copy bound to ``new_index``.
        """
        ret = self
        if not weak or self.is_weak_id:
            # Explicit rebinding, or rebinding a weak ID, may select the new ID.
            ret = copy.copy(ret)
            ret.id = new_index

        return ret

    def __getitem__(self, index) -> DataDescriptor[DataT]:
        """Return a descriptor explicitly rebound to ``index``.

        Parameters
        ----------
        index
            New data ID.

        Returns
        -------
        DataDescriptor
            A copy bound to ``index``.

        Notes
        -----
        Internal code should prefer ``index_implicit`` so weak IDs can inherit the
        current build ID automatically.
        """
        return self.index_explicit(index)

    def __class_getitem__(cls, id, *args):
        if isinstance(id, int):
            return cls(*args, id=id)
        else:
            # Generic supplies this method at runtime, outside the typed MRO.
            return cast(Any, super()).__class_getitem__(id, *args)

    def __hash__(self):
        return hash(tuple(getattr(self, k) for k in sorted(self.keys)))

    def __eq__(self, other):
        if type(self) is not type(other):
            return False

        for k in self.keys:
            if getattr(self, k) != getattr(other, k):
                return False
        else:
            return True

    @property
    def keys(self):
        """Attribute names that participate in equality and hashing."""
        keys = []
        for c in reversed(inspect.getmro(type(self))):
            keys.extend(getattr(c, "__slots__", []))
        keys.extend(getattr(self, "__dict__", []))

        keys = set(keys)
        keys.remove("_id")
        keys.add("id")  # Keep the public ID non-negative.

        return keys

    @property
    def params(self):
        """Constructor parameters reconstructed from the descriptor state."""
        return {k.strip("_"): getattr(self, k) for k in sorted(self.keys)}

    def __repr__(self):
        params = self.params
        del params["id"]

        id_str = f"[{self.id}]" if self.id > 0 else ""
        param_str = ", ".join([f"{k}={repr(v)}" for k, v in params.items()])

        return f"{type(self).__name__}{id_str}({param_str})"

    def __copy__(self):
        return type(self)(**self.params)


class IndexedDataTypeDescriptor(DataDescriptor[DataT]):
    """Bind an indexed data type to a data ID."""

    __slots__ = ["_dtype"]

    @classmethod
    def of(cls, dtype, id=DataDescriptor.DefaultWeakID):
        """Create the appropriate descriptor for ``dtype`` and ``id``."""
        if isinstance(dtype, IndexedDataMeta):
            return type(dtype).__getitem__(dtype, id)
        elif issubclass(dtype, DataDescriptor):
            return dtype(id=id)
        else:
            # Ordinary types cannot be indexed and always use the default ID.
            return cls(dtype, id=DataDescriptor.DefaultID)

    def __init__(self, dtype: type, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._dtype = dtype

    @property
    def dtype(self):
        """The data type bound by this descriptor."""
        return self._dtype

    def __build__(self, container: DataIoC) -> DataT:
        builder = _extract_builder_with_context(self.dtype, self)
        if builder is None:
            raise TypeError(f"No builder for {self.dtype!r}")
        ret = builder(container)
        return ret

    def __call__(self, *args, **kwargs):
        """Construct a value and associate it with this descriptor."""
        return DescribedData(self, self.dtype(*args, **kwargs))

    def __repr__(self):
        id_str = f"[{self.id}]" if self.id > 0 else ""
        return f"{self.dtype.__name__}{id_str}"


class DescribedData:
    """Pair a value with the descriptor under which it should be registered."""

    def __init__(self, desc: DataDescriptor[DataT], data: DataT):
        self.desc = desc
        self.data = data


class IndexedDataMeta(type):
    """Make a data type indexable so ``DataIoC`` can bind related data groups.

    Notes
    -----
    A derived class can define ``__class_index__`` to customize its indexing
    behavior.

    A derived class can inherit ``UniqueData`` to indicate that the type is unique
    and does not require indexing.

    Every type that is not an ``IndexedData`` subclass is treated as unique and is
    not indexed.
    """

    def __getitem__(self, id=DataDescriptor.DefaultWeakID, *args):
        class_getitem = getattr(self, "__class_index__", None)
        if class_getitem is not None:
            return class_getitem(id, *args)
        else:
            return IndexedDataTypeDescriptor(self, *args, id=id)

    def __repr__(self):
        return f"{self.__name__}"


class IndexedData(metaclass=IndexedDataMeta):
    """Marker base class for data types that can have one value per ID."""

    pass


class UniqueData:
    """Make an indexed data type share one value across all build IDs."""

    @classmethod
    def __class_index__(cls, id, *args):
        # Bind to the default ID so every implicit access resolves the same value.
        return IndexedDataTypeDescriptor(cls, *args, id=DataDescriptor.DefaultID)


class DataIoC:
    """Resolve data dependencies on demand and cache constructed values."""

    def __init__(self, allow_implicit_registering=True, record_all=False):
        """Initialize a data IoC container.

        Parameters
        ----------
        allow_implicit_registering
            Allow a requested target's own builder to be registered on first
            access. If false, only explicitly registered data and builders can be
            retrieved or built.
        record_all
            Retain all container access records. By default, only dependencies from
            the current access are retained for diagnostic output. If true, the
            complete access tree is retained and may add overhead.
        """
        self._collection: dict[Union[DataDescriptor, type], Any] = {}
        self._lazy_collection: dict[
            Union[DataDescriptor, type], Callable[[DataIoC], Any]
        ] = {}
        self.allow_implicit_register = allow_implicit_registering
        self.record_all = record_all

        self._logger = _DataIoCAccessLogger(key=self)

    def with_data(self, *data: Any) -> Self:
        """Register existing values and return this container.

        Parameters
        ----------
        *data
            Values to register by their types. Values created through an indexed
            type, such as ``Sensor[1](...)``, retain their descriptors.

        Returns
        -------
        DataIoC
            This container, allowing chained registration calls.
        """
        for d in data:
            if isinstance(d, DescribedData):
                self[d.desc] = d.data
            else:
                self[type(d)] = d

        return self

    def add(
        self,
        data_type: Union[DataT, type[DataT], DataDescriptor[DataT]],
        data: Optional[DataT] = None,
    ) -> Self:
        """Register existing data or a target's own lazy builder.

        Passing a type or descriptor without ``data`` registers the builder defined
        by that target. Passing an existing value as ``data_type`` registers it by
        type. Passing both a key and a non-``None`` value registers that value under
        the key.

        Parameters
        ----------
        data_type
            Existing value to register, or the type or descriptor used as a key.
        data
            Existing non-``None`` value to register under ``data_type``. Because
            ``None`` selects builder registration, assign through ``container[key]``
            to store an explicit ``None`` value.

        Returns
        -------
        DataIoC
            This container, allowing chained registration calls.

        Raises
        ------
        TypeError
            If no builder can be found or the supplied key is invalid.
        """
        data_type = _descriptor_instance(data_type)
        if data is None:
            if isinstance(data_type, DataDescriptor) or isinstance(data_type, type):
                builder = _extract_builder_with_context(data_type)
                if builder is None:
                    raise TypeError(f"No builder for {data_type!r}")
                self._lazy_collection[data_type] = builder
            else:
                self.with_data(data_type)
        else:
            if not isinstance(data_type, (type, DataDescriptor)):
                raise TypeError("A data key must be a type or DataDescriptor.")
            self[data_type] = data

        return self

    def add_provider(
        self,
        data_type: Union[type[DataT], DataDescriptor[DataT]],
        provider: Union[SupportsBuild, Callable],
    ) -> Self:
        """Register an alternative lazy builder for a data key.

        Registering another provider for the same key replaces the builder used by
        future uncached requests. Existing cached values are retained.

        Parameters
        ----------
        data_type
            Type or descriptor whose value the provider builds.
        provider
            Callable accepting a container, or an object that defines
            ``__build__``.

        Returns
        -------
        DataIoC
            This container, allowing chained registration calls.

        Raises
        ------
        TypeError
            If ``provider`` is neither callable nor an object with ``__build__``.
        """
        data_type = _descriptor_instance(data_type)
        initiator = None
        if isinstance(data_type, DataDescriptor):
            initiator = data_type

        builder = _extract_builder(provider)
        if builder is None:
            raise TypeError("A provider must be callable or define __build__.")
        self._lazy_collection[data_type] = Provider(
            initiator=initiator, builder=builder, target=provider
        )

        return self

    @property
    def logger(self):
        """The dependency access logger used for diagnostics."""
        return self._logger

    @overload
    def __getitem__(self, dtype: DataDescriptor[DataT]) -> DataT: ...

    @overload
    def __getitem__(self, dtype: type[DataDescriptor[DataT]]) -> DataT: ...

    @overload
    def __getitem__(self, dtype: type[DataT]) -> DataT: ...

    def __getitem__(self, dtype: Any) -> Any:
        """Resolve and return the value identified by ``dtype``.

        A cached value is returned immediately. Otherwise, the registered or
        implicit builder is called and a successful result, including ``None``, is
        cached under the requested key.

        Parameters
        ----------
        dtype
            Data type or descriptor to resolve.

        Returns
        -------
        Any
            The registered or constructed value.

        Raises
        ------
        RuntimeError
            If implicit registration is disabled and no builder is registered.
        TypeError
            If no suitable builder exists.
        """
        dtype = _descriptor_instance(dtype)
        ret: Any = None
        with self._logger.add(dtype):
            if dtype in self._collection:
                ret = self._collection[dtype]
            else:
                builder = self.find_builder(dtype)

                if builder is None:
                    if not self.allow_implicit_register:
                        raise RuntimeError(
                            f"Builder for {dtype!r} not found in DataIoC."
                        )
                    else:
                        self.add(dtype)
                        builder = self.find_builder(dtype)

                if builder is None:
                    raise TypeError(f"No builder for {dtype!r}")
                if builder is not None:
                    if isinstance(builder, Provider):
                        self._logger.mark_overwrite(builder.target)

                    try:
                        ret = builder(self)
                    except Exception:
                        self._logger.mark_failed()
                        if self._logger.at_level0:
                            print(self._logger)
                        raise

                    self._logger.mark_new()
                    self[dtype] = ret

        if self._logger.at_root and not self.record_all:
            self._logger.clear()

        return ret

    def __setitem__(
        self, data_type: Union[type[DataT], DataDescriptor[DataT]], data: DataT
    ):
        """Store ``data`` under a type or descriptor key.

        Assigning to an indexed ID 0 key also makes the value available through an
        unindexed class lookup. Assigning to a class creates the corresponding ID 0
        mapping as well.
        """
        data_type = _descriptor_instance(data_type)
        self._collection[data_type] = data
        if isinstance(data_type, IndexedDataTypeDescriptor) and data_type.id == 0:
            self._collection[data_type.dtype] = data
        if isinstance(data_type, type):
            # A class binding also supplies the corresponding ID 0 value.
            self._collection[IndexedDataTypeDescriptor.of(data_type)] = data

    def find_builder(self, dtype: Union[type[DataT], DataDescriptor[DataT]]):
        """Find the registered builder for a type or descriptor.

        A builder registered by class can be reused by
        ``IndexedDataTypeDescriptor`` instances at every ID. A builder registered
        for a specific ``DataDescriptor`` applies only to that descriptor.

        Parameters
        ----------
        dtype
            Type or descriptor whose builder should be found.

        Returns
        -------
        Callable or None
            The matching builder, with indexed context bound when necessary, or
            ``None`` if no builder is registered.
        """
        # Class reads target ID 0; class registrations remain fallbacks for all IDs.
        if isinstance(dtype, IndexedDataMeta):
            dtype = IndexedDataTypeDescriptor.of(dtype, id=DataDescriptor.DefaultID)

        builder = self._lazy_collection.get(dtype, None)
        if builder is None:
            if isinstance(dtype, IndexedDataTypeDescriptor):
                # For an indexed type, also search for its type-wide builder.
                builder = self._lazy_collection.get(dtype.dtype, None)
                if builder is not None:
                    builder = _bind_builder_context(initiator=dtype, builder=builder)

        return builder

    def __str__(self):
        return type(self).__name__


class IndexedDataIoC(DataIoC):
    """Container view that rebinds weak dependencies to the active build ID."""

    def __init__(self, base_container: DataIoC, initiator=None):
        """Initialize an indexed view over ``base_container``.

        Parameters
        ----------
        base_container
            Container that stores and resolves the underlying values.
        initiator
            Descriptor whose signed ID supplies the current build context.
        """
        super().__init__()
        self._base_container = base_container
        self._initiator = initiator

    @property
    def id(self):
        """The signed ID used when implicitly rebinding dependencies."""
        if self._initiator is None:
            return DataDescriptor.DefaultWeakID
        else:
            return self._initiator.signed_id

    def __getattr__(self, item):
        return getattr(self._base_container, item)

    @overload
    def __getitem__(self, dtype: DataDescriptor[DataT]) -> DataT: ...

    @overload
    def __getitem__(self, dtype: type[DataDescriptor[DataT]]) -> DataT: ...

    @overload
    def __getitem__(self, dtype: type[DataT]) -> DataT: ...

    def __getitem__(self, dtype: Any) -> Any:
        """Resolve ``dtype`` after applying the current indexed context."""
        item = dtype
        if isinstance(item, type):
            item = IndexedDataTypeDescriptor.of(item, id=self.id)
        elif isinstance(item, DataDescriptor):
            item = item.index_implicit(self.id)

        ret = self._base_container[item]

        return ret


class _DataIoCDependency:
    def __init__(self, parent: Optional[_DataIoCDependency], key, new=False):
        self._children: list[tuple[Any, _DataIoCDependency]] = []
        self._parent = parent
        self._key = key
        self._new = new
        self._overwrite = None
        self._failed = False

    def __iter__(self):
        return iter(self._children)

    def __len__(self):
        return len(self._children)

    def clear(self):
        self._children.clear()

    def mark_new(self):
        self._new = True

    def mark_overwrite(self, key):
        self._overwrite = key

    def mark_failed(self):
        self._failed = True

    def add(self, key):
        ret = self.get(key, None)
        if ret is None:
            ret = _DataIoCDependency(parent=self, key=key)
            self[key] = ret

        return ret

    @property
    def parent(self):
        return self._parent

    @property
    def last_child(self):
        if len(self) == 0:
            return None

        return self._children[-1][1]

    def __contains__(self, item):
        for k, _v in self:
            if item == k:
                return True
        else:
            return False

    def __setitem__(self, key, value):
        self._children.append((key, value))

    def __getitem__(self, item):
        for k, v in self:
            if item == k:
                return v
        else:
            raise KeyError(item)

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default

    def to_str(
        self, prefix=None, indent="", table_prefix="", align_first_non_blank=True
    ):
        if prefix is None:
            prefix = " * "

        this_prefix = prefix
        properties = []
        if self._failed:
            this_prefix = this_prefix.replace("*", "X")
            if this_prefix == prefix:
                properties.append(" X <--- Failed here ")
        if self._new:
            properties.append("Created")

        if len(properties) == 0:
            props = ""
        else:
            props = " /" + ", ".join(properties) + "/"

        key = str(self._key)
        if self._overwrite is not None:
            key = str(self._overwrite) + f" ( <- {key})"

        ret = table_prefix + this_prefix + key + props + "\n"

        if align_first_non_blank:
            for c in prefix:
                if c == " ":
                    indent += " "
                else:
                    break

        remaining = len(self)
        for _k, v in self:
            if remaining > 1:
                ret += v.to_str(
                    prefix=prefix, table_prefix=indent + "├─", indent=indent + "│ "
                )
            else:
                ret += v.to_str(
                    prefix=prefix, table_prefix=indent + "└─", indent=indent + "  "
                )

            remaining -= 1

        return ret

    def __str__(self):
        return self.to_str()


class _DataIoCAccessLogger:
    def __init__(self, key: Any = "root"):
        self.root = _DataIoCDependency(None, key)
        self.current = self.root

    @property
    def at_level0(self):
        """Whether the current node is the root of a child access tree."""
        return self.current.parent is self.root

    @property
    def at_root(self):
        """Whether the logger is positioned at the root node."""
        return self.current is self.root

    @contextlib.contextmanager
    def add(self, key):
        child = self.current.add(key)

        try:
            self.enter(child)
            yield
        finally:
            self.exit()

    def clear(self):
        self.root.clear()

    def mark_new(self):
        self.current.mark_new()

    def mark_overwrite(self, key):
        self.current.mark_overwrite(key)

    def mark_failed(self):
        self.current.mark_failed()

    def __enter__(self):
        self.enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exit()

    def enter(self, node=None):
        if node is None:
            node = self.current.last_child
        if node is None:
            raise RuntimeError("No dependency to enter.")
        self.current = node

    def exit(self):
        parent = self.current.parent
        if parent is None:
            raise RuntimeError("Cannot exit the dependency tree root.")
        self.current = parent

    def to_str(self, prefix=None):
        return self.root.to_str(prefix=prefix)

    def __str__(self):
        return self.to_str()


def _descriptor_instance(dtype: Any) -> Any:
    if isinstance(dtype, type) and issubclass(dtype, DataDescriptor):
        return dtype()
    return dtype


def _extract_builder_with_context(
    dtype: Union[DataDescriptor, SupportsBuild, Callable], initiator=None
):
    dtype = _descriptor_instance(dtype)
    if initiator is None:
        if isinstance(dtype, DataDescriptor):
            initiator = dtype

    builder = _extract_builder(dtype)

    if builder is None:
        return builder
    else:
        return _bind_builder_context(builder, initiator=initiator)


def _extract_builder(dtype: Union[DataDescriptor, SupportsBuild, Callable]):
    if isinstance(dtype, SupportsBuild):
        builder = dtype.__build__
    elif callable(dtype):
        # Either a type constructor or a direct builder function.
        # TODO: Validate that the callable can be used by DataIoC.
        builder = dtype
    else:
        builder = None

    return builder


def _bind_builder_context(builder, initiator):
    if initiator is None:
        return builder
    elif isinstance(builder, BuilderWithContext):
        return builder.with_initiator(initiator)
    else:
        return BuilderWithContext(initiator, builder)


class BuilderWithContext:
    def __init__(self, initiator, builder):
        self.initiator = initiator
        self.builder = builder

    def __call__(self, container: DataIoC):
        return self.builder(IndexedDataIoC(container, initiator=self.initiator))

    def with_initiator(self, initiator):
        ret = copy.copy(self)
        ret.initiator = initiator

        return ret


class Provider(BuilderWithContext):
    def __init__(self, initiator, builder, target):
        super().__init__(initiator, builder)
        self._target = target

    @property
    def target(self):
        if isinstance(self._target, DataDescriptor):
            return self._target
        else:
            return getattr(self._target, "__name__", type(self._target).__name__)
