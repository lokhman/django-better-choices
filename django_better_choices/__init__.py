"""Better choices library for Django web framework."""

from __future__ import annotations

import copy
import types

from abc import abstractmethod
from collections.abc import Hashable, Iterator, Mapping
from sys import version_info
from typing import Any, Dict, NamedTuple, Tuple, Type, TypeVar, Union, cast

from .version import __version__

PY38 = version_info >= (3, 8)

if PY38:
    from functools import cached_property
    from typing import Protocol, runtime_checkable
else:

    def cached_property(func):
        return func

    def runtime_checkable(cls):
        return cls

    class Protocol:
        pass

try:
    from django.utils.functional import Promise
except ImportError:

    class Promise:
        pass


BaseClass = TypeVar("BaseClass")
Display = Union[str, Promise]
ChoicesEntry = Tuple[Hashable, Display]


@runtime_checkable
class Choices(Protocol):
    @abstractmethod
    def __getattribute__(self, attr: str) -> Union[Value, Choices]: ...

    @abstractmethod
    def __getitem__(self, value: Hashable) -> Value: ...

    @abstractmethod
    def __len__(self) -> int: ...

    @abstractmethod
    def __iter__(self) -> Iterator[Hashable]: ...

    @abstractmethod
    def __or__(self, other: Choices) -> Choices: ...

    @abstractmethod
    def __and__(self, other: Choices) -> Choices: ...

    @abstractmethod
    def __sub__(self, other: Choices) -> Choices: ...

    @abstractmethod
    def __xor__(self, other: Choices) -> Choices: ...

    @abstractmethod
    def keys(self) -> Tuple[Hashable, ...]: ...

    @abstractmethod
    def values(self) -> Tuple[Hashable, ...]: ...

    def items(self) -> Tuple[Tuple[Hashable, Value], ...]: ...

    @abstractmethod
    def displays(self) -> Tuple[Display, ...]: ...

    @abstractmethod
    def choices(self) -> Tuple[ChoicesEntry, ...]: ...

    @abstractmethod
    def extract(self, __attr: str, *attrs: str, name: str = "Subset") -> Choices: ...

    @abstractmethod
    def exclude(self, __attr: str, *attrs: str, name: str = "Subset") -> Choices: ...


@runtime_checkable
class Value(Hashable, Protocol):
    """Interface for compiled choices value to be used for type checking."""

    @abstractmethod
    def __getattribute__(self, param: str) -> Any: ...

    @property
    @abstractmethod
    def __choices_attr__(self) -> str: ...

    @property
    @abstractmethod
    def __choices_entry__(self) -> ChoicesEntry: ...

    @property
    @abstractmethod
    def display(self) -> Display: ...


class ValueAttribute(NamedTuple):
    """Choices value configuration that is compiled to the value of type `Value`."""

    base_value: Hashable
    display: Display
    params: Dict[str, Any]


class SubsetAttribute(tuple):
    """A container for values that is compiled to the inner choices class."""


class BaseChoices(Mapping):
    def __init__(self):
        cls, __dict__ = self.__class__, {}
        if not getattr(self, "__subset", False):
            for base_class in reversed(cls.__mro__[: cls.__mro__.index(BaseChoices)]):
                __dict__.update(base_class.__dict__)
        __dict__.update(cls.__dict__)

        __choices_ignore__ = set(getattr(cls, "__choices_ignore__", ()))
        if not getattr(self, "__subset", False):
            unknown_ignored_attrs = __choices_ignore__ - __dict__.keys()
            if unknown_ignored_attrs:
                raise ValueError(
                    f"unknown attribute(s) in '{cls.__qualname__}.__choices_ignore__': "
                    f"{', '.join(unknown_ignored_attrs)}"
                )

        self.__values = {}
        for attr_name, attr_value in __dict__.items():
            if attr_name.startswith("_") or attr_name in __choices_ignore__:
                continue

            if isinstance(attr_value, Value):
                base_value = attr_value.__class__.__base__(attr_value)
                value = copy.copy(attr_value)
                setattr(value, "__choices_attr__", attr_name)
                self.__values[base_value] = value
            elif isinstance(attr_value, ValueAttribute):
                base_value = attr_value.base_value
                if base_value is None:
                    base_value = attr_name.lower()

                value = self.__value_factory(attr_name, base_value, attr_value.display, **attr_value.params)
                if base_value in self.__values:
                    raise ValueError(
                        f"choices class '{cls.__qualname__}' has a duplicated "
                        f"value '{base_value}' for attribute '{attr_name}'"
                    )

                self.__values[base_value] = value
                setattr(self, attr_name, value)
            elif isinstance(attr_value, (str, Promise)):
                base_value = attr_name.lower()
                value = self.__value_factory(attr_name, base_value, attr_value)
                self.__values[base_value] = value
                setattr(self, attr_name, value)
            elif isinstance(attr_value, SubsetAttribute):
                setattr(self, attr_name, self.extract(*attr_value, name=attr_name))

    def __mro_entries__(self, bases: Tuple[Type]) -> Tuple[Type, ...]:
        return ()

    def __getitem__(self, value: Hashable) -> Value:
        return self.__values[value]

    def __len__(self) -> int:
        return len(self.__values)

    def __iter__(self) -> Iterator[Hashable]:
        yield from self.__values

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(self.__attrs)})"

    def __repr__(self) -> str:
        kwargs = (f"{self.__class__.__name__!r}", *(f"{a}={v!r}" for a, v in self.__attrs.items()))
        return f"Choices({', '.join(kwargs)})"

    def __or__(self, other: Choices) -> Choices:
        return self.__op_def(other, "|", {**self.__attrs, **other.__attrs})

    def __and__(self, other: Choices) -> Choices:
        return self.__op_def(other, "&", {a: v for a, v in self.__attrs.items() if a in other.__attrs})

    def __sub__(self, other: Choices) -> Choices:
        return self.__op_def(other, "-", {a: v for a, v in self.__attrs.items() if a not in other.__attrs})

    def __xor__(self, other: Choices) -> Choices:
        return self.__op_def(
            other,
            "^",
            {
                **{a: v for a, v in self.__attrs.items() if a not in other.__attrs},
                **{a: v for a, v in other.__attrs.items() if a not in self.__attrs},
            },
        )

    def __op_def(self, other: Choices, op: str, attrs: Dict[str, Value]) -> Choices:
        return choices.new(f"<{self.__class__.__name__}{op}{other.__class__.__name__}>", **attrs)

    @classmethod
    def __value_factory(cls, attr: str, base_value: Hashable, display: Display, **params: Any) -> Value:
        try:
            hash(base_value)
            value_class = type(
                f"{cls.__qualname__.replace('.', '_')}_{attr}",
                (type(base_value),) if PY38 else (type(base_value), Value),
                {
                    **params,
                    "display": display,
                    "__choices_attr__": attr,
                    "__choices_entry__": (base_value, display),
                },
            )
        except TypeError:
            raise TypeError(
                f"type '{type(base_value).__name__}' is not acceptable "
                f"for choices class value '{cls.__qualname__}.{attr}'"
            ) from None

        globals()[value_class.__name__] = value_class  # pickle support
        return value_class(base_value)

    @cached_property
    def __attrs(self) -> Dict[str, Value]:
        return {v.__choices_attr__: v for v in self.values()}

    def keys(self) -> Tuple[Hashable, ...]:
        return tuple(super().keys())

    def values(self) -> Tuple[Value, ...]:
        return tuple(super().values())

    def items(self) -> Tuple[Tuple[Hashable, Value], ...]:
        return tuple(super().items())

    def displays(self) -> Tuple[Display, ...]:
        return tuple(v.display for v in self.values())

    def choices(self) -> Tuple[ChoicesEntry, ...]:
        return tuple(v.__choices_entry__ for v in self.values())

    def extract(self, __attr: str, *attrs: str, name: str = "Subset") -> Choices:
        return choices.new(
            f"{self.__class__.__name__}.{name}",
            (self.__class__,),
            **{a: getattr(self, a) for a in (__attr, *attrs)},
            __subset=True,
        )

    def exclude(self, __attr: str, *attrs: str, name: str = "Subset") -> Choices:
        return choices.new(
            f"{self.__class__.__name__}.{name}",
            (self.__class__,),
            **{a: getattr(self, a) for a in self.__attrs if a not in {__attr, *attrs}},
            __subset=True,
        )


class choices:
    """
    Choices class decorator.

    Documentation:
        https://pypi.org/project/django-better-choices/
    """

    def __new__(cls, __choices_class: Union[Type[BaseClass], Type]) -> Union[BaseClass, Choices]:
        bases = []
        if hasattr(__choices_class, "__orig_bases__"):
            for base_class in __choices_class.__orig_bases__:
                if isinstance(base_class, BaseChoices):
                    base_class = base_class.__class__
                bases.append(base_class)
        elif __choices_class.__bases__ != (object,):
            bases.extend(__choices_class.__bases__)

        __dict__ = {k: v for k, v in __choices_class.__dict__.items() if k not in {"__dict__", "__orig_bases__"}}
        __dict__.setdefault("__qualname__", __choices_class.__qualname__)

        return type(__choices_class.__name__, (*bases, BaseChoices), __dict__)()

    @staticmethod
    def new(__name: str = "Choices", __bases: Tuple[Type, ...] = (), **attrs: Any) -> Choices:
        return choices(types.new_class(__name, __bases, exec_body=lambda ns: ns.update(attrs)))

    @staticmethod
    def value(display: Display, *, value: Hashable = None, **params: Any) -> Value:
        return cast(Value, ValueAttribute(base_value=value, display=display, params=params))

    @staticmethod
    def subset(__attr: str, *attrs: str) -> Choices:
        return cast(Choices, SubsetAttribute(dict.fromkeys((__attr, *attrs)).keys()))


__all__ = ("Choices", "Value", "choices")
