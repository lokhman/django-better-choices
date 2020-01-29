"""Better choices library for Django web framework."""

from typing import Any, Iterator, Optional, Tuple, Union

try:
    from django.utils.functional import Promise
except ImportError:
    class Promise:
        pass

from .version import __version__


class __ChoicesMetaclass(type):
    def __contains__(self, value: str) -> bool:
        return self.find(value) is not None

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        for value in self.values():
            yield value.__str__(), value.display

    def __str__(self) -> str:
        return f"{self.__name__}({', '.join(self.keys())})"

    def __repr__(self) -> str:
        kwargs = (f"'{self.__name__}'", *(f'{k}={v.display!r}' for k, v in self.items()))
        return f"Choices({', '.join(kwargs)})"


class Choices(metaclass=__ChoicesMetaclass):
    """
    Choices class that should be overridden or initialised for constant class definition.

    Example:
        # init via class definition
        class PAGE_STATUS(Choices):
            CREATED = 'Created'
            PENDING = Choices.Value('Pending', help_text='This set status to pending')
            ON_HOLD = Choices.Value('On Hold', value='custom_on_hold')

            VALID = Choices.Subset('CREATED', ON_HOLD)

            # supports inner choices
            class INTERNAL_STATUS(Choices):
                REVIEW = 'On Review'

        # init via inline definition
        PAGE_STATUS = Choices('PAGE_STATUS', SUCCESS='Success', FAIL='Error')

        # value accessors
        value_created = PAGE_STATUS.CREATED
        value_review = PAGE_STATUS.INTERNAL_STATUS.REVIEW
        value_on_hold = getattr(PAGE_STATUS, 'ON_HOLD')

        # values and value parameters
        print( PAGE_STATUS.CREATED )                # 'created'
        print( PAGE_STATUS.ON_HOLD )                # 'custom_on_hold'
        print( PAGE_STATUS.PENDING.display )        # 'Pending'
        print( PAGE_STATUS.PENDING.help_text )      # 'This set status to pending'

        # values comparison
        PAGE_STATUS.ON_HOLD == 'custom_on_hold'     # True
        PAGE_STATUS.CREATED == PAGE_STATUS.CREATED  # True

        # search in choices
        'created' in PAGE_STATUS                    # True
        'custom_on_hold' in PAGE_STATUS             # True
        'on_hold' in PAGE_STATUS                    # False
        value = PAGE_STATUS['custom_on_hold']       # Choices.Value
        key, value = PAGE_STATUS.find('created')    # ('CREATED', Choices.Value)

        # search in subsets
        'custom_on_hold' in PAGE_STATUS.VALID       # True
        PAGE_STATUS.CREATED in PAGE_STATUS.VALID    # True
        index = PAGE_STATUS.VALID.index('created')  # 0

        # choices iteration
        for value, display in PAGE_STATUS:
            print( value, display )
        for key, value in PAGE_STATUS.items():
            print( key, value, value.display )
        for key in PAGE_STATUS.keys():
            print( key )
        for value in PAGE_STATUS.values():
            print( value, value.display )
        for display in PAGE_STATUS.displays():
            print( display )
        for display in PAGE_STATUS.SUBSET.displays():
            print( display )

        # Django model fields
        class Page(models.Model):
            status = models.CharField(choices=PAGE_STATUS, default=PAGE_STATUS.CREATED)

        # saving choices values on models
        page = Page.objects.get(pk=1)
        page.status = PAGE_STATUS.PENDING
        page.save()
    """

    class Value(str):
        """Immutable string class that contains choices value configuration."""

        capitalize = casefold = center = count = encode = endswith = expandtabs = find = format = format_map = \
            index = isalnum = isalpha = isascii = isdecimal = isdigit = isidentifier = islower = isnumeric = \
            isprintable = isspace = istitle = isupper = join = ljust = lower = lstrip = maketrans = partition = \
            replace = rfind = rindex = rjust = rpartition = rsplit = rstrip = split = splitlines = startswith = \
            strip = swapcase = title = translate = upper = zfill = property()

        def __new__(cls, display: Union[str, Promise], *, value: str = '', **params: Any):
            """
            Custom value class definition to support extended functionality.

            Args:
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
                raise AttributeError(f"'Value' object has no attribute '{name}'") from None

        def __clone__(self, value: str) -> 'Choices.Value':
            return self.__class__(self.__display, value=value, **self.__params)

        @property
        def display(self) -> str:
            return str(self.__display)

    class Subset(frozenset):
        """Immutable subset of values that is easy to search by."""

        def __new__(cls, *values: str):
            self = super().__new__(cls, values)
            self.__index = {v: values.index(v) for v in values}
            return self

        def __iter__(self) -> Iterator[str]:
            yield from self.__index.keys()

        def index(self, value: str) -> int:
            """Return first index of value."""
            try:
                return self.__index[value]
            except KeyError:
                raise ValueError(f'{value!r} is not in subset') from None

        def displays(self) -> Tuple[str, ...]:
            """Return tuple of displays of subset values."""
            return tuple(v.display for v in self if isinstance(v, Choices.Value))

    def __new__(cls, name: Optional[str] = None, **values: Union['Value', str, Promise]):
        if cls != Choices:
            raise RuntimeError(f"choices object '{cls.__name__}' cannot be initialized")
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
                value = cls.Subset(*map(lambda v: v if isinstance(v, cls.Value) else getattr(cls, v), value))
                setattr(cls, key, value)
            else:
                raise TypeError(f"choices key '{cls.__name__}.{key}' has invalid value type: '{type(value).__name__}'")

    def __class_getitem__(cls, value: str) -> 'Value':
        return cls.__values[cls.__keys[value]]

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
