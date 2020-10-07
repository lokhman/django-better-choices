"""Better choices library for Django web framework."""

import sys
import warnings

from typing import Any, ClassVar, Dict, Iterable, Iterator, Optional, Tuple, TypeVar, Union, overload

try:
    from django.utils.functional import Promise
except ImportError:
    class Promise:
        pass

from .version import __version__


class _Value(str):
    """An immutable string class that contains choices value configuration."""

    capitalize = casefold = center = count = encode = endswith = expandtabs = find = format = format_map = \
        index = isalnum = isalpha = isascii = isdecimal = isdigit = isidentifier = islower = isnumeric = \
        isprintable = isspace = istitle = isupper = join = ljust = lower = lstrip = maketrans = partition = \
        replace = rfind = rindex = rjust = rpartition = rsplit = rstrip = split = splitlines = startswith = \
        strip = swapcase = title = translate = upper = zfill = property()

    if sys.version_info >= (3, 9):
        removeprefix = removesuffix = property()

    def __new__(cls, display: Union[str, Promise], *, value: str = '', **params: Any):
        """
        Custom value class definition to support extended functionality.

        Arguments:
            display (Union[str, Promise]): Text used to represent the value.
            value (str): Custom value of the value (if empty, choices key lowercase will be used).
            params: Additional value parameters.
        """
        self = super().__new__(cls, value)
        self.__display = display
        self.__params = params
        return self

    def __getattr__(self, name: str) -> Any:
        try:
            return self.__params[name]
        except KeyError:
            if hasattr(str, name):
                def wrapper(*args, **kwargs):  # native str method
                    return getattr(str, name)(self, *args, **kwargs)
                return wrapper
            raise AttributeError(f'choices class value {self!r} has no attribute {name!r}') from None

    def __clone__(self, __value: str = None) -> '_Value':
        return _Value(
            self.__display,
            value=self.__str__() if __value is None else __value,
            **self.__params
        )

    @property
    def __choice_entry__(self) -> Tuple[str, str]:
        return self.__str__(), self.display

    @property
    def display(self) -> str:
        return str(self.__display)


class _Subset(tuple):
    """An immutable subset of values, which is translated to inner choices class."""

    def __new__(cls, *keys: str):
        return super().__new__(cls, dict.fromkeys(keys).keys())


class __ChoicesMetaclass(type):
    def __iter__(self) -> Iterator[Tuple[str, str]]:
        for value in self.values():
            yield value.__choice_entry__

    def __contains__(self, value: str) -> bool:
        try:
            _ = self[value]
        except KeyError:
            return False
        return True

    def __copy__(self) -> 'Choices':
        return Choices(self.__name__, **{k: v.__clone__() for k, v in self.items()})

    def __str__(self) -> str:
        return f"{self.__name__}({', '.join(self.keys())})"

    def __repr__(self) -> str:
        kwargs = (f'{self.__name__!r}', *(f'{k}={v.display!r}' for k, v in self.items()))
        return f"Choices({', '.join(kwargs)})"

    def __or__(self, other: 'Choices') -> 'Choices':
        return self.__operation(other, '|', (*self.items(), *other.items()))

    def __and__(self, other: 'Choices') -> 'Choices':
        return self.__operation(other, '&', ((k, v) for k, v in self.items() if other.has_key(k)))

    def __sub__(self, other: 'Choices') -> 'Choices':
        return self.__operation(other, '-', ((k, v) for k, v in self.items() if not other.has_key(k)))

    def __xor__(self, other: 'Choices') -> 'Choices':
        return self.__operation(other, '^', (
            *((k, v) for k, v in self.items() if not other.has_key(k)),
            *((k, v) for k, v in other.items() if not self.has_key(k))
        ))

    def __operation(self, other: 'Choices', op: str, items: Iterable[Tuple[str, _Value]]) -> 'Choices':
        return type(f'{self.__name__}{op}{other.__name__}', (Choices,), dict(items))


class Choices(metaclass=__ChoicesMetaclass):
    """
    Choices class that should be overridden or initialised for constant class definition.

    Examples:
        https://pypi.org/project/django-better-choices/
    """

    Value = _Value
    Subset = _Subset

    __DefaultType = TypeVar('__DefaultType')
    __ValueType = Union[_Value, str, Promise]

    __keys: ClassVar[Dict[_Value, str]]
    __values: ClassVar[Dict[str, _Value]]

    @overload
    def __new__(cls) -> 'Choices': ...
    @overload
    def __new__(cls, __name: str) -> 'Choices': ...
    @overload
    def __new__(cls, __name: str, **values: __ValueType) -> 'Choices': ...
    @overload
    def __new__(cls, **values: __ValueType) -> 'Choices': ...
    @overload
    def __new__(cls, **params: Any) -> Tuple[Tuple[str, str], ...]: ...
    def __new__(cls, __name: str = None, **kwargs: Union[__ValueType, Any]):
        if cls is not Choices:
            return tuple(v.__choice_entry__ for _, v in cls.__items_iter(**kwargs))
        return type(cls.__name__ if __name is None else __name, (Choices,), kwargs)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.__keys = {}
        cls.__values = {}

        for key, value in cls.__dict__.items():
            if not key.startswith('_') and isinstance(value, (str, Promise, _Subset)):
                cls.insert(key, value)

    def __class_getitem__(cls, value: str) -> _Value:
        try:
            return cls.__values[cls.__keys[value]]
        except KeyError:
            raise KeyError(f'value {value!r} is not found in choices class {cls.__qualname__!r}') from None

    def __getattr__(self, _): ...
    def __getitem__(self, _): ...

    @classmethod
    def __items_iter(cls, **params: Any) -> Iterator[Tuple[str, _Value]]:
        if not params:
            yield from cls.__values.items()
        else:
            for key, value in cls.__values.items():
                if all(hasattr(value, k) and getattr(value, k) == v for k, v in params.items()):
                    yield key, value

    @classmethod
    def insert(cls, key: str, value: Union[_Value, str, Promise, _Subset]) -> None:
        """Insert a new value to choices class using given key."""
        assert key.isidentifier(), \
            f'choices class key {key!r} should be a valid identifier'
        assert not key.startswith('_'), \
            f'choices class key {key!r} should not start with underscore'
        assert isinstance(value, (str, Promise, _Subset)), \
            f"choices class key {cls.__qualname__ + '.' + key!r} has invalid value type {type(value).__name__!r}"

        if isinstance(value, _Value):
            if value == '':
                value = value.__clone__(key.lower())
                setattr(cls, key, value)
            elif value in cls.__keys:
                raise ValueError(
                    f"choices class key {cls.__qualname__ + '.' + key!r} "
                    f'has a duplicated value {value!r}'
                )
            cls.__keys[value] = key
            cls.__values[key] = value
        elif isinstance(value, (str, Promise)):
            value = _Value(value, value=key.lower())
            setattr(cls, key, value)
            cls.__keys[value] = key
            cls.__values[key] = value
        elif isinstance(value, _Subset):
            setattr(cls, key, cls.extract(*value, name=key))

    @overload
    @classmethod
    def get(cls, __value: str) -> Optional[_Value]: ...
    @overload
    @classmethod
    def get(cls, __value: str, default: __DefaultType) -> Union[_Value, __DefaultType]: ...
    @classmethod
    def get(cls, __value: str, default: __DefaultType = None) -> Union[_Value, __DefaultType]:
        """Return value if it exists in choices class, otherwise return default or None."""
        try:
            return cls.__values[cls.__keys[__value]]
        except KeyError:
            return default

    @overload
    @classmethod
    def get_key(cls, __value: str) -> Optional[_Value]: ...
    @overload
    @classmethod
    def get_key(cls, __value: str, default: __DefaultType) -> Union[_Value, __DefaultType]: ...
    @classmethod
    def get_key(cls, __value: str, default: __DefaultType = None) -> Union[_Value, __DefaultType]:
        """Return key if value exists in choices class, otherwise return default or None."""
        return cls.__keys.get(__value, default)

    @classmethod
    def has_key(cls, __key: str) -> bool:
        """Check if key exists in choices class."""
        return __key in cls.__values

    @classmethod
    def items(cls, **params: Any) -> Tuple[Tuple[str, _Value], ...]:
        """Return tuple of key-value tuples as ((K1, V1), (K2, V2), etc)."""
        return tuple(cls.__items_iter(**params))

    @classmethod
    def keys(cls, **params: Any) -> Tuple[str, ...]:
        """Return tuple of keys of choices as (K1, K2, etc)."""
        return tuple(k for k, _ in cls.__items_iter(**params))

    @classmethod
    def values(cls, **params: Any) -> Tuple[_Value, ...]:
        """Return tuple of values as (V1, V2, etc)."""
        return tuple(v for _, v in cls.__items_iter(**params))

    @classmethod
    def displays(cls, **params: Any) -> Tuple[str, ...]:
        """Return tuple of displays of choices values."""
        return tuple(v.display for _, v in cls.__items_iter(**params))

    @classmethod
    def extract(cls, __key: str, *keys: str, name: str = 'Subset') -> 'Choices':
        """Dynamically extract subset of values from choices class."""
        return type(f'{cls.__name__}.{name}', (cls,), {k: cls.__values[k] for k in (__key, *keys)})

    @classmethod
    def has(cls, key: str) -> bool:  # pragma: no cover
        """Check if key exists in choices class."""
        warnings.warn(
            "'Choices.has()' method is deprecated, use 'Choices.has_key()'",
            DeprecationWarning
        )
        return cls.has_key(key)

    @classmethod
    def find(cls, value: str) -> Optional[Tuple[str, _Value]]:  # pragma: no cover
        """Return key-value tuple if the given value exists in the choices, otherwise return None."""
        warnings.warn(
            "'Choices.find()' method is deprecated, use 'Choices.get()' and 'Choices.get_key()'",
            DeprecationWarning
        )
        try:
            key = cls.__keys[value]
        except KeyError:
            return None
        return key, cls.__values[key]


__all__ = ('Choices',)
