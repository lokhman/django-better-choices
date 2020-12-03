"""Better choices library for Django web framework."""

from abc import abstractmethod
from typing import Any, ClassVar, Dict, Hashable, Iterable, Iterator, Optional, Tuple, Type, TypeVar, Union, overload

try:
    from django.utils.functional import Promise
except ImportError:
    class Promise:
        pass

from .version import __version__


_DisplayType = Union[str, Promise]


class ValueType:
    """Interface for compiled choices value to be used for type checking."""

    @property
    @abstractmethod
    def __choice_entry__(self) -> Tuple[Hashable, _DisplayType]: ...

    @property
    @abstractmethod
    def display(self) -> _DisplayType: ...


class _ChoicesValue:
    """Choices value configuration that is compiled to the value of type `ValueType`."""

    def __init__(self, display: _DisplayType, *, value: Optional[Hashable] = None, **params: Any):
        self.__value, self.__display, self.__params = value, display, params

    @property
    def __choice_entry__(self) -> Tuple[Hashable, _DisplayType, Dict[str, Any]]:
        return self.__value, self.__display, self.__params


class _ChoicesSubset(tuple):
    """A container for values that are compiled to the inner choices class."""

    def __new__(cls: Type[Tuple], *keys: str):
        return super().__new__(cls, dict.fromkeys(keys).keys())


class __ChoicesMetaclass(type):
    def __iter__(self: "Choices") -> Iterator[Tuple[Hashable, _DisplayType]]:
        for value in self.values():
            yield value.__choice_entry__

    def __contains__(self: "Choices", value: Hashable) -> bool:
        try:
            self[value]
        except ValueError:
            return False
        return True

    def __str__(self: "Choices") -> str:
        return f"{self.__name__}({', '.join(self.keys())})"

    def __repr__(self: "Choices") -> str:
        kwargs = (f"{self.__name__!r}", *(f"{k}={v.display!r}" for k, v in self.items()))
        return f"Choices({', '.join(kwargs)})"

    def __or__(self: "Choices", other: "Choices") -> "Choices":
        return self.__op_def(other, "|", (*self.items(), *other.items()))

    def __and__(self: "Choices", other: "Choices") -> "Choices":
        return self.__op_def(other, "&", ((k, v) for k, v in self.items() if other.has_key(k)))

    def __sub__(self: "Choices", other: "Choices") -> "Choices":
        return self.__op_def(other, "-", ((k, v) for k, v in self.items() if not other.has_key(k)))

    def __xor__(self: "Choices", other: "Choices") -> "Choices":
        return self.__op_def(other, "^", (
            *((k, v) for k, v in self.items() if not other.has_key(k)),
            *((k, v) for k, v in other.items() if not self.has_key(k)),
        ))

    def __op_def(self: "Choices", other: "Choices", op: str, items: Iterable[Tuple[str, ValueType]]) -> Type["Choices"]:
        return type(f"{self.__name__}{op}{other.__name__}", (Choices,), dict(items))


class Choices(metaclass=__ChoicesMetaclass):
    """
    Choices class that should be overridden or initialised for constant class definition.

    Documentation:
        https://pypi.org/project/django-better-choices/
    """

    __ClassValueType = Union[_ChoicesValue, _ChoicesSubset, _DisplayType, ValueType]
    __DefaultType = TypeVar("__DefaultType")

    __keys: ClassVar[Dict[ValueType, str]]
    __values: ClassVar[Dict[str, ValueType]]

    @overload
    def __new__(cls) -> "Choices": ...
    @overload
    def __new__(cls, __name: str) -> "Choices": ...
    @overload
    def __new__(cls, __name: str, **values: __ClassValueType) -> "Choices": ...
    @overload
    def __new__(cls, **values: __ClassValueType) -> "Choices": ...
    @overload
    def __new__(cls, **params: Any) -> Tuple[Tuple[ValueType, _DisplayType], ...]: ...
    def __new__(cls, __name: Optional[str] = None, **kwargs: Any):
        if cls is not Choices:  # x = Choices(...); x(**params)
            return tuple(v.__choice_entry__ for _, v in cls.__iter_items(**kwargs))
        return type(cls.__name__ if __name is None else __name, (Choices,), kwargs)

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)

        cls.__keys = {}
        cls.__values = {}

        for key, value in cls.__dict__.items():
            if key.startswith("_"):
                continue

            if isinstance(value, ValueType):
                setattr(cls, key, value)
                cls.__keys[value] = key
                cls.__values[key] = value
            elif isinstance(value, cls.Value):
                value, display, params = value.__choice_entry__
                if value is None:
                    value = key.lower()

                value = cls.__value_factory(key, value, display, **params)
                if value in cls.__keys:
                    raise ValueError(
                        f"choices class {cls.__qualname__!r} has " 
                        f"a duplicated value {value!r} for key {key!r}"
                    )

                setattr(cls, key, value)
                cls.__keys[value] = key
                cls.__values[key] = value
            elif isinstance(value, (str, Promise)):
                value = cls.__value_factory(key, key.lower(), value)
                setattr(cls, key, value)
                cls.__keys[value] = key
                cls.__values[key] = value
            elif isinstance(value, cls.Subset):
                setattr(cls, key, cls.extract(*value, name=key))

    def __class_getitem__(cls, value: Hashable) -> ValueType:
        try:
            return cls.__values[cls.__keys[value]]
        except KeyError:
            raise ValueError(f"value {value!r} is not found in choices class {cls.__qualname__!r}") from None

    def __getattr__(self, _): ...  # not implemented

    @classmethod
    def __value_factory(cls, key: str, value: Hashable, display: _DisplayType, **params: Any) -> ValueType:
        try:
            hash(value)
            _type = type(
                f"{cls.__qualname__.replace('.', '_')}_{key}",
                (type(value), ValueType),
                {**params, "display": display, "__choice_entry__": (value, display)},
            )
        except TypeError:
            raise TypeError(
                f"type {type(value).__name__!r} is not acceptable "
                f"for choices class value {cls.__qualname__ + '.' + key!r}"
            ) from None

        globals()[_type.__name__] = _type  # pickle support
        return _type(value)

    @classmethod
    def __iter_items(cls, **params: Any) -> Iterator[Tuple[str, ValueType]]:
        for key, value in cls.__values.items():
            if all(hasattr(value, k) and getattr(value, k) == v for k, v in params.items()):
                yield key, value

    @overload
    @classmethod
    def get(cls, __value: Hashable) -> Optional[ValueType]: ...
    @overload
    @classmethod
    def get(cls, __value: Hashable, default: __DefaultType) -> Union[ValueType, __DefaultType]: ...
    @classmethod
    def get(cls, __value: Hashable, default: Optional[__DefaultType] = None) -> Union[ValueType, __DefaultType]:
        """Return value if it exists in choices class, otherwise return default or None."""
        try:
            return cls.__values[cls.__keys[__value]]
        except KeyError:
            return default

    @overload
    @classmethod
    def get_key(cls, __value: Hashable) -> Optional[ValueType]: ...
    @overload
    @classmethod
    def get_key(cls, __value: Hashable, default: __DefaultType) -> Union[ValueType, __DefaultType]: ...
    @classmethod
    def get_key(cls, __value: Hashable, default: Optional[__DefaultType] = None) -> Union[ValueType, __DefaultType]:
        """Return key if value exists in choices class, otherwise return default or None."""
        return cls.__keys.get(__value, default)

    @classmethod
    def has_key(cls, __key: str) -> bool:
        """Check if key exists in choices class."""
        return __key in cls.__values

    @classmethod
    def items(cls, **params: Any) -> Tuple[Tuple[str, ValueType], ...]:
        """Return tuple of key-value tuples as ((K1, V1), (K2, V2), etc)."""
        return tuple(cls.__iter_items(**params))

    @classmethod
    def keys(cls, **params: Any) -> Tuple[str, ...]:
        """Return tuple of keys of choices as (K1, K2, etc)."""
        return tuple(k for k, _ in cls.__iter_items(**params))

    @classmethod
    def values(cls, **params: Any) -> Tuple[ValueType, ...]:
        """Return tuple of values as (V1, V2, etc)."""
        return tuple(v for _, v in cls.__iter_items(**params))

    @classmethod
    def displays(cls, **params: Any) -> Tuple[_DisplayType, ...]:
        """Return tuple of displays of choices values."""
        return tuple(v.display for _, v in cls.__iter_items(**params))

    @classmethod
    def extract(cls, __key: str, *keys: str, name: str = "Subset") -> Type["Choices"]:
        """Dynamically extract subset of values from choices class."""
        return type(f"{cls.__name__}.{name}", (cls,), {k: cls.__values[k] for k in (__key, *keys)})

    Value = _ChoicesValue
    Subset = _ChoicesSubset


__all__ = ("Choices", "ValueType")
