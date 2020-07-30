"""Better choices library for Django web framework."""

from typing import Any, Iterable, Iterator, Optional, Tuple, Union

try:
    from django.utils.functional import Promise
except ImportError:
    class Promise:
        ...

from .version import __version__


class __ChoicesMetaclass(type):
    def __contains__(self, value: str) -> bool:
        return self.find(value) is not None

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        for value in self.values():
            yield value.__choice_entry__

    def __str__(self) -> str:
        return f"{self.__name__}({', '.join(self.keys())})"

    def __repr__(self) -> str:
        kwargs = (f"'{self.__name__}'", *(f'{k}={v.display!r}' for k, v in self.items()))
        return f"Choices({', '.join(kwargs)})"

    def __or__(self, other: 'Choices') -> 'Choices':
        return self.__operation(other, '|', (*self.items(), *other.items()))

    def __and__(self, other: 'Choices') -> 'Choices':
        return self.__operation(other, '&', ((k, v) for k, v in self.items() if other.has(k)))

    def __sub__(self, other: 'Choices') -> 'Choices':
        return self.__operation(other, '-', ((k, v) for k, v in self.items() if not other.has(k)))

    def __xor__(self, other: 'Choices') -> 'Choices':
        return self.__operation(other, '^', (
            *((k, v) for k, v in self.items() if not other.has(k)),
            *((k, v) for k, v in other.items() if not self.has(k))
        ))

    def __operation(self, other: 'Choices', op: str, items: Iterable[Tuple[str, 'Choices.Value']]) -> 'Choices':
        return type(f'{self.__name__}{op}{other.__name__}', (Choices,), dict(items))


class Choices(metaclass=__ChoicesMetaclass):
    """
    Choices class that should be overridden or initialised for constant class definition.

    Examples:
        https://pypi.org/project/django-better-choices/
    """

    class Value(str):
        """An immutable string class that contains choices value configuration."""

        capitalize = casefold = center = count = encode = endswith = expandtabs = find = format = format_map = \
            index = isalnum = isalpha = isascii = isdecimal = isdigit = isidentifier = islower = isnumeric = \
            isprintable = isspace = istitle = isupper = join = ljust = lower = lstrip = maketrans = partition = \
            replace = rfind = rindex = rjust = rpartition = rsplit = rstrip = split = splitlines = startswith = \
            strip = swapcase = title = translate = upper = zfill = property()

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
                raise AttributeError(f"'Value' object has no attribute '{name}'") from None

        def __clone__(self, value: str) -> 'Choices.Value':
            return Choices.Value(self.__display, value=value, **self.__params)

        @property
        def __choice_entry__(self) -> Tuple[str, str]:
            return self.__str__(), self.display

        @property
        def display(self) -> str:
            return str(self.__display)

    class Subset(tuple):
        """An immutable subset of values, which is translated to inner choices class."""

        def __new__(cls, *keys: str):
            return super().__new__(cls, dict.fromkeys(keys).keys())

    def __new__(cls, name: Optional[str] = None, **values: Union['Value', str, Promise]):
        if cls is not Choices:
            return tuple(cls)
        if name is None:
            name = cls.__name__
        return type(name, (Choices,), values)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.__keys = {}
        cls.__values = {}

        for key, value in vars(cls).items():
            if callable(value) or not key.isupper():
                continue

            if isinstance(value, cls.Value):
                if value == '':
                    value = value.__clone__(key.lower())
                    setattr(cls, key, value)
                elif value in cls.__keys:
                    raise ValueError(f"choices key '{cls.__name__}.{key}' has duplicated value: {value!r}")
                cls.__keys[value] = key
                cls.__values[key] = value
            elif isinstance(value, (str, Promise)):
                value = cls.Value(value, value=key.lower())
                setattr(cls, key, value)
                cls.__keys[value] = key
                cls.__values[key] = value
            elif isinstance(value, cls.Subset):
                setattr(cls, key, cls.extract(*value, name=key))
            else:
                raise TypeError(f"choices key '{cls.__name__}.{key}' has invalid value type: '{type(value).__name__}'")

    def __class_getitem__(cls, value: str) -> 'Value':
        return cls.__values[cls.__keys[value]]

    @classmethod
    def has(cls, key: str) -> bool:
        """Check if key exists in the choices class."""
        return key in cls.__values

    @classmethod
    def items(cls) -> Tuple[Tuple[str, 'Value'], ...]:
        """Return tuple of key-value tuples as ((K1, V1), (K2, V2), etc)."""
        return tuple(cls.__values.items())

    @classmethod
    def keys(cls) -> Tuple[str, ...]:
        """Return tuple of keys of choices as (K1, K2, etc)."""
        return tuple(cls.__values.keys())

    @classmethod
    def values(cls) -> Tuple['Value', ...]:
        """Return tuple of values as (V1, V2, etc)."""
        return tuple(cls.__values.values())

    @classmethod
    def displays(cls) -> Tuple[str, ...]:
        """Return tuple of displays of values."""
        return tuple(v.display for v in cls.__values.values())

    @classmethod
    def find(cls, value: str) -> Optional[Tuple[str, 'Value']]:
        """Return key-value tuple if the given value exists in the choices, otherwise return None."""
        try:
            key = cls.__keys[value]
        except KeyError:
            return None
        return key, cls.__values[key]

    @classmethod
    def extract(cls, *keys: str, name: str = 'Subset') -> 'Choices':
        """Dynamically extract a subset of values from the choices class."""
        return type(f'{cls.__name__}.{name}', (cls,), {k: cls.__values[k] for k in keys})
