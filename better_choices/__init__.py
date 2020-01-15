"""Better choices library for Django web framework."""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Union

try:
    from django.utils.functional import Promise
except ImportError:
    class Promise:
        pass

from .version import __version__


class __ChoicesMetaclass(type):
    def __contains__(self, value: str) -> bool:
        for choice in self.choices():
            if choice.value == value:
                return True
        return False

    def __iter__(self):
        for choice in self.choices():
            yield choice.value, choice.display

    def __str__(self):
        return f'{self.__name__}({self.__str_kwargs()})'

    def __repr__(self):
        return f'Choices({self.__name__!r}, {self.__str_kwargs()})'

    def __str_kwargs(self) -> str:
        return ', '.join(f'{k}={v!r}' for k, (v,) in self.extract('display'))


class Choices(metaclass=__ChoicesMetaclass):
    """
    Choices class that should be overridden or initialised for constant class definition.

    Example:
        # init via class definition
        class STATUSES(Choices):
            CREATED = 'Created'
            PENDING = Choices.Choice('Pending', help_text='This set status to pending')
            ON_HOLD = Choices.Choice('On Hold', value='custom_on_hold')

            VALID = Choices.Subset('CREATED', ON_HOLD)

            # supports inner choices
            class INTERNAL_STATUS(Choices):
                REVIEW = 'On Review'

        # init via inline definition
        STATUSES = Choices('STATUSES', SUCCESS='Success', FAIL='Error')

        # choice accessors
        choice_created = STATUSES.CREATED
        choice_on_hold = STATUSES['ON_HOLD']

        # choice parameters and inner choice accessors
        print( STATUSES.CREATED.value )             # 'created'
        print( STATUSES.ON_HOLD.value )             # 'custom_on_hold'
        print( STATUSES.PENDING.display )           # 'Pending'
        print( STATUSES.PENDING.help_text )         # 'This set status to pending'
        print( STATUSES.INTERNAL_STATUS.REVIEW )    # 'review'

        # search in choices
        'created' in STATUSES                       # True
        'custom_on_hold' in STATUSES                # True
        'on_hold' in STATUSES                       # False
        key, choice = STATUSES.find('created')      # ('CREATED', Choices.Choice)

        # search in subsets
        'custom_on_hold' in STATUSES.VALID          # True
        STATUSES.CREATED in STATUSES.VALID          # True

        # choices iteration
        for value, display in STATUSES:
            print( value, display )
        for key, choice in STATUSES.items():
            print( key, choice.value, choice.display )
        for key in STATUSES.keys():
            print( key )
        for choice in STATUSES.choices():
            print( choice.value, choice.display )

        # Django model fields
        class MyModel(models.Model):
            status = models.CharField(choices=STATUSES, default=STATUSES.CREATED)

        # saving choices on models
        model = MyModel.objects.get(pk=1)
        model.status = STATUSES.PENDING
        model.save()
    """

    @dataclass(init=False, frozen=True)
    class Choice:
        """Immutable data class that contains choice configuration."""

        display: Union[str, Promise]
        value: Optional[str]

        def __init__(self, display: Union[str, Promise], *, value: Optional[str] = None, **params: Any):
            """
            Custom data class constructor to support nice syntax.

            Note:
                Frozen data classes can be modified only via `__setattr__` (even in the constructor).

            Args:
                display (Union[str, Promise]): Text used to represent choice value.
                value (Optional[str]): Overridden value of the choice (usually same as key).
                params: Additional choice parameters.
            """
            params['display'] = display
            params['value'] = value

            for key, value in params.items():
                object.__setattr__(self, key, value)

        def __hash__(self):
            return super().__hash__()

        def __str__(self) -> str:
            if self.value is None:
                return ''
            return self.value

        def deconstruct(self) -> Tuple[str, Tuple[str, ...], Dict[str, Any]]:
            """
            Django custom deconstruction method to be supported in model fields.

            See: https://docs.djangoproject.com/en/2.2/topics/migrations/#custom-deconstruct-method.
            """
            return f'builtins.str', (self.__str__(),), {}

    class Subset(frozenset):
        """Immutable subset of choices that is easy to search by using Choice object or value."""

        def __new__(cls, *choices: Union['Choices.Choice', str]):
            return super().__new__(cls, choices)

        def __contains__(self, item: Union['Choices.Choice', str]) -> bool:
            if isinstance(item, Choices.Choice):
                return super().__contains__(item)

            for choice in self:
                if choice.value == item:
                    return True
            return False

    def __new__(cls, name: Optional[str] = None, **choices: Union['Choice', str, Promise]):
        """This will dynamically create a custom choices class from parameters (see inline definition example)."""
        if cls != Choices:
            raise RuntimeError(f"choices object '{cls.__name__}' cannot be initialized")
        if name is None:
            name = cls.__name__
        return type(name, (Choices,), choices)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls.__choices = {}
        for key, choice in vars(cls).items():
            if callable(choice) or not key.isupper():
                continue

            if isinstance(choice, cls.Choice):
                if choice.value is None:
                    object.__setattr__(choice, 'value', key.lower())
                cls.__choices[key] = choice
            elif isinstance(choice, (str, Promise)):
                choice = cls.Choice(choice, value=key.lower())
                cls.__choices[key] = choice
                setattr(cls, key, choice)
            elif isinstance(choice, cls.Subset):
                if any(not isinstance(c, cls.Choice) for c in choice):
                    setattr(cls, key, cls.Subset(*map(lambda c: c if isinstance(c, cls.Choice) else cls[c], choice)))
            else:
                raise TypeError(f"choice '{cls.__name__}.{key}' has invalid type: '{type(choice).__name__}'")

    def __class_getitem__(cls, key: str) -> 'Choice':
        return cls.__choices[key]

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
        for key, choice in cls.__choices.items():
            if choice.value == value:
                return key, choice
        return None

    @classmethod
    def extract(cls, *params: str, flat: bool = False) -> Tuple[Tuple, ...]:
        """
        Return a tuple of extracted params of choices.

        Example:
            class CONST(Choices):
                VAL1 = Choices.Choice('Value 1', par1='Param 1.1')
                VAL2 = Choices.Choice('Value 2', par2='Param 2.2')
                VAL3 = Choices.Choice('Value 3', par1='Param 3.1', par2='Param 3.2')

            print( CONST.extract('value', 'par1') )
            # (('VAL1', ('val1', 'Param 1.1')), ('VAL2', ('val2', None)), ('VAL3', ('val3', 'Param 3.1')))

            print( CONST.extract('value', 'par1', flat=True) )
            # (('val1', 'Param 1.1'), ('val2', None), ('val3', 'Param 3.1'))

            print( CONST.extract('par1', flat=True) )
            # ('Param 1.1', None, 'Param 3.1')

        Args:
            params: Names of parameters to extract.
            flat (Optional[bool]): If True return extracted values without choice keys.
        """
        extracted = []
        for key, choice in cls.__choices.items():
            values = tuple(getattr(choice, param, None) for param in params)
            extracted.append((values[0] if len(values) == 1 else values) if flat else (key, values))
        return tuple(extracted)
