"""Better choices library for Django web framework."""

from typing import Any, Dict, Iterator, Optional, Tuple, Union

try:
    from django.utils.functional import Promise
except ImportError:
    class Promise:
        pass

from .version import __version__


class __ChoicesMetaclass(type):
    def __contains__(self, value: str) -> bool:
        return self.find(value) is not None

    def __iter__(self) -> Iterator[Tuple[str, Union[str, Promise]]]:
        for choice in self.choices():
            yield choice.value, choice.display

    def __str__(self) -> str:
        return f'{self.__name__}({self.__str_kwargs()})'

    def __repr__(self) -> str:
        return f'Choices({self.__name__!r}, {self.__str_kwargs()})'

    def __str_kwargs(self) -> str:
        return ', '.join(f'{k}={v!r}' for k, v in self.extract('display', with_keys=True))


class Choices(metaclass=__ChoicesMetaclass):
    """
    Choices class that should be overridden or initialised for constant class definition.

    Example:
        # init via class definition
        class PAGE_STATUS(Choices):
            CREATED = 'Created'
            PENDING = Choices.Choice('Pending', help_text='This set status to pending')
            ON_HOLD = Choices.Choice('On Hold', value='custom_on_hold')

            VALID = Choices.Subset('CREATED', ON_HOLD)

            # supports inner choices
            class INTERNAL_STATUS(Choices):
                REVIEW = 'On Review'

        # init via inline definition
        PAGE_STATUS = Choices('PAGE_STATUS', SUCCESS='Success', FAIL='Error')

        # choice accessors
        choice_created = PAGE_STATUS.CREATED
        choice_review = PAGE_STATUS.INTERNAL_STATUS.REVIEW
        choice_on_hold = getattr(PAGE_STATUS, 'ON_HOLD')

        # choice parameters and inner choice accessors
        print( PAGE_STATUS.CREATED.value )              # 'created'
        print( PAGE_STATUS.ON_HOLD.value )              # 'custom_on_hold'
        print( PAGE_STATUS.PENDING.display )            # 'Pending'
        print( PAGE_STATUS.PENDING.help_text )          # 'This set status to pending'
        print( PAGE_STATUS.PENDING )                    # 'pending'

        # choice comparison
        PAGE_STATUS.ON_HOLD == 'custom_on_hold'         # True
        PAGE_STATUS.CREATED == PAGE_STATUS.CREATED      # True

        # search in choices
        'created' in PAGE_STATUS                        # True
        'custom_on_hold' in PAGE_STATUS                 # True
        'on_hold' in PAGE_STATUS                        # False
        choice = PAGE_STATUS['custom_on_hold']          # Choices.Choice
        key, choice = PAGE_STATUS.find('created')       # ('CREATED', Choices.Choice)

        # search in subsets
        'custom_on_hold' in PAGE_STATUS.VALID           # True
        PAGE_STATUS.CREATED in PAGE_STATUS.VALID        # True

        # choices iteration
        for value, display in PAGE_STATUS:
            print( value, display )
        for key, choice in PAGE_STATUS.items():
            print( key, choice.value, choice.display )
        for key in PAGE_STATUS.keys():
            print( key )
        for choice in PAGE_STATUS.choices():
            print( choice.value, choice.display )

        # Django model fields
        class Page(models.Model):
            status = models.CharField(choices=PAGE_STATUS, default=PAGE_STATUS.CREATED)

        # saving choices on models
        page = Page.objects.get(pk=1)
        page.status = PAGE_STATUS.PENDING
        page.save()
    """

    class Choice(str):
        """Immutable string class that contains choice configuration."""

        capitalize = casefold = center = count = encode = endswith = expandtabs = find = format = format_map = \
            index = isalnum = isalpha = isascii = isdecimal = isdigit = isidentifier = islower = isnumeric = \
            isprintable = isspace = istitle = isupper = join = ljust = lower = lstrip = maketrans = partition = \
            replace = rfind = rindex = rjust = rpartition = rsplit = rstrip = split = splitlines = startswith = \
            strip = swapcase = title = translate = upper = zfill = property()

        def __new__(cls, display: Union[str, Promise], *, value: str = '', **params: Any):
            """
            Custom data class definition to support extended functionality.

            Args:
                display (Union[str, Promise]): Text used to represent choice value.
                value (str): Overridden value of the choice (usually same as key lowercase).
                params: Additional choice parameters.
            """
            self = super().__new__(cls, value)
            self.__display = display
            self.__params = params
            return self

        def __getattr__(self, name: str) -> Any:
            try:
                return self.__params[name]
            except KeyError:
                raise AttributeError(f"'{self.__class__.__name__}' object has not attribute '{name}'") from None

        def __clone__(self, value: str) -> 'Choices.Choice':
            return self.__class__(self.__display, value=value, **self.__params)

        @property
        def value(self) -> str:
            return self.__str__()

        @property
        def display(self) -> Union[str, Promise]:
            return self.__display

        def deconstruct(self) -> Tuple[str, Tuple[str, ...], Dict[str, Any]]:
            """
            Django custom deconstruction method to be supported in model fields.

            See: https://docs.djangoproject.com/en/2.2/topics/migrations/#custom-deconstruct-method.
            """
            return 'builtins.str', (self.value,), {}

    class Subset(tuple):
        """Immutable subset of choices that is easy to search by using Choice object or value."""

        def __new__(cls, *choices: Union['Choices.Choice', str]):
            self = super().__new__(cls, dict.fromkeys(choices).keys())
            self.__index = {c.value for c in self if isinstance(c, Choices.Choice)}
            return self

        def __contains__(self, item: Union['Choices.Choice', str]) -> bool:
            return item in self.__index

        def extract(self, *params: str) -> Tuple[Any, ...]:
            """
            Return a tuple of extracted params of subset choices.

            Example:
                class CONST(Choices):
                    VAL1 = Choices.Choice('Value 1', par1='Param 1.1')
                    VAL2 = Choices.Choice('Value 2', par2='Param 2.2')
                    VAL3 = Choices.Choice('Value 3', par1='Param 3.1', par2='Param 3.2')

                    SUBSET = Choices.Subset(VAL1, VAL3)

                print( CONST.SUBSET.extract('value') )
                # ('val1', 'val3')

                print( CONST.SUBSET.extract('value', 'display', 'par2') )
                # (('val1', 'Value 1', None), ('val3', 'Value 3', 'Param 3.2'))

            Args:
                params (str): Names of parameters to extract.
            """
            return tuple(
                getattr(c, params[0], None) if len(params) == 1 else tuple(getattr(c, p, None) for p in params)
                for c in self
            )

    def __new__(cls, name: Optional[str] = None, **choices: Union['Choice', str, Promise]):
        if cls != Choices:
            raise RuntimeError(f"choices object '{cls.__name__}' cannot be initialized")
        if name is None:
            name = cls.__name__
        return type(name, (Choices,), choices)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.__index = {}
        cls.__choices = {}

        for key, choice in vars(cls).items():
            if callable(choice) or not key.isupper():
                continue

            if isinstance(choice, cls.Choice):
                if choice.value == '':
                    choice = choice.__clone__(key.lower())
                    setattr(cls, key, choice)
                elif choice.value in cls.__index:
                    raise ValueError(f"choice '{cls.__name__}.{key}' has duplicated value: {choice.value!r}")
                cls.__index[choice.value] = key
                cls.__choices[key] = choice
            elif isinstance(choice, (str, Promise)):
                choice = cls.Choice(choice, value=key.lower())
                cls.__index[choice.value] = key
                cls.__choices[key] = choice
                setattr(cls, key, choice)
            elif isinstance(choice, cls.Subset):
                if any(not isinstance(c, cls.Choice) for c in choice):
                    subset = cls.Subset(*map(lambda c: c if isinstance(c, cls.Choice) else getattr(cls, c), choice))
                    setattr(cls, key, subset)
            else:
                raise TypeError(f"choice '{cls.__name__}.{key}' has invalid type: '{type(choice).__name__}'")

    def __class_getitem__(cls, value: str) -> 'Choice':
        return cls.__choices[cls.__index[value]]

    @classmethod
    def items(cls) -> Tuple[Tuple[str, 'Choice'], ...]:
        """Return a tuple of key-choice tuples as ((K1, C1), (K2, C2), etc)."""
        return tuple((key, choice) for key, choice in cls.__choices.items())

    @classmethod
    def keys(cls) -> Tuple[str, ...]:
        """Return tuple of keys of choices."""
        return tuple(cls.__choices.keys())

    @classmethod
    def choices(cls) -> Tuple['Choice', ...]:
        """Return a tuple of choices."""
        return tuple(cls.__choices.values())

    @classmethod
    def find(cls, value: str) -> Optional[Tuple[str, 'Choice']]:
        """Return key-choice tuple if the given value exists in the choices, otherwise return None."""
        try:
            key = cls.__index[value]
        except KeyError:
            return None
        return key, cls.__choices[key]

    @classmethod
    def extract(cls, *params: str, with_keys: bool = False) -> Tuple[Any, ...]:
        """
        Return a tuple of extracted params of choices.

        Example:
            class CONST(Choices):
                VAL1 = Choices.Choice('Value 1', par1='Param 1.1')
                VAL2 = Choices.Choice('Value 2', par2='Param 2.2')
                VAL3 = Choices.Choice('Value 3', par1='Param 3.1', par2='Param 3.2')

            print( CONST.extract('par1') )
            # ('Param 1.1', None, 'Param 3.1')

            print( CONST.extract('value', 'par1') )
            # (('val1', 'Param 1.1'), ('val2', None), ('val3', 'Param 3.1'))

            print( CONST.extract('value', 'par1', with_keys=True) )
            # (('VAL1', ('val1', 'Param 1.1')), ('VAL2', ('val2', None)), ('VAL3', ('val3', 'Param 3.1')))

        Args:
            params (str): Names of parameters to extract.
            with_keys (Optional[bool]): If True return extracted values with choice keys.
        """
        values = tuple(
            getattr(c, params[0], None) if len(params) == 1 else tuple(getattr(c, p, None) for p in params)
            for c in cls.__choices.values()
        )
        if with_keys:
            return tuple(zip(cls.__choices.keys(), values))
        return values
