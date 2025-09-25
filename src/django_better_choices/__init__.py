"""Better choices library for Django web framework."""

import collections.abc
import enum
import sys
import types
import typing

if sys.version_info >= (3, 11):
    from typing import Self as _Self  # pragma: no cover
else:  # pragma: no cover
    from typing_extensions import Self as _Self  # pragma: no cover

try:
    from django.utils.functional import Promise as _Promise  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover

    class _Promise: ...  # type: ignore[no-redef]  # pragma: no cover


__all__ = ["Choices"]  # pragma: no cover

_auto = object()

_AnyPromise = typing.TypeVar("_AnyPromise", bound=_Promise)
_Display = typing.Union[str, _AnyPromise]


class _ValueAttribute:
    __slots__ = ("display", "params", "value")

    def __init__(
        self,
        display: _Display,
        /,
        *,
        value: collections.abc.Hashable = _auto,
        **params: typing.Any,
    ) -> None:
        self.value = value
        self.display = display
        self.params = params


class _SubsetAttribute:
    __slots__ = ("names",)

    def __init__(self, *choice_names: str) -> None:
        self.names = tuple(dict.fromkeys(choice_names))

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self.names)


class _AttributeMixin:
    Value = _ValueAttribute
    Subset = _SubsetAttribute


class _Choice(str):  # noqa: SLOT000
    __choices_param_names__: set[str]

    display: _Display

    def __new__(cls, value_attr: _ValueAttribute) -> _Self:
        self = super().__new__(cls, value_attr.value)
        self.__choices_param_names__ = set(value_attr.params)
        for param_name, param_value in value_attr.params.items():
            setattr(self, param_name, param_value)
        self.display = value_attr.display
        return self


class _ChoicesDict(enum._EnumDict):  # noqa: SLF001
    def __setitem__(self, attr: str, value: typing.Any) -> None:
        if attr.startswith("_choices_") or isinstance(value, _SubsetAttribute):
            dict.__setitem__(self, attr, value)
        else:
            super().__setitem__(attr, value)

    @property
    def member_names(self) -> typing.Iterable[str]:
        return self._member_names  # type: ignore[attr-defined]


class _ChoicesMeta(enum.EnumMeta):
    @classmethod
    def __prepare__(  # type: ignore[override]
        metacls,  # noqa: N804
        class_name: str,
        bases: tuple[type, ...],
        **kwargs: typing.Any,
    ) -> _ChoicesDict:
        class_dict = super().__prepare__(class_name, bases, **kwargs)
        class_dict.__class__ = _ChoicesDict
        return typing.cast("_ChoicesDict", class_dict)

    def __new__(
        metacls,
        class_name: str,
        bases: tuple[type, ...],
        class_dict: _ChoicesDict,
        **kwargs: typing.Any,
    ) -> "_ChoicesMeta":
        value_factory = class_dict.pop("_choices_value_factory_", metacls.default_value_factory)

        for choice_name in class_dict.member_names:
            choice = class_dict[choice_name]
            if isinstance(choice, _ValueAttribute):
                if choice.value is _auto:
                    choice.value = value_factory(choice_name, display=choice.display)
            elif isinstance(choice, _Choice):
                choice_params = {name: getattr(choice, name) for name in choice.__choices_param_names__}
                choice = _ValueAttribute(
                    choice.display,
                    value=choice.value,  # type: ignore[attr-defined]
                    **choice_params,
                )
                dict.__setitem__(class_dict, choice_name, choice)
            elif isinstance(choice, (str, _Promise)):
                choice = _ValueAttribute(choice, value=value_factory(choice_name, display=choice))
                dict.__setitem__(class_dict, choice_name, choice)
            else:
                raise TypeError(
                    f"Unexpected type '{choice.__class__.__name__}' for choices: {class_name}.{choice_name}",
                )

        for attr, value in class_dict.items():
            if isinstance(value, _SubsetAttribute):
                names = {name: class_dict[name] for name in value.names}
                choice = _create_subset(f"{class_name}.{attr}", class_dict, names)
                dict.__setitem__(class_dict, attr, choice)

        cls = super().__new__(metacls, class_name, bases, class_dict, **kwargs)
        if sys.version_info >= (3, 11):
            cls._value_repr_ = None  # pragma: no cover
        return cls

    def __repr__(cls) -> str:
        return f"<choices {cls.__name__!r}>"

    def __contains__(cls, value: typing.Any) -> bool:
        if isinstance(value, collections.abc.Hashable) and not isinstance(value, _Choice):
            return value in cls._value2member_map_
        return super().__contains__(value)

    @staticmethod
    def default_value_factory(choice_name: str, **choice_params: typing.Any) -> str:  # noqa: ARG004
        return str.lower(choice_name)


class Choices(_AttributeMixin, _Choice, enum.Enum, metaclass=_ChoicesMeta):
    """
    Choices class.

    Documentation:
        https://pypi.org/project/django-better-choices/
    """

    _choices_value_factory_: typing.Callable[[str], str]

    def __new__(cls, value_attr: _ValueAttribute) -> _Self:  # noqa: D102
        choice = _Choice.__new__(cls, value_attr)
        choice._value_ = value_attr.value
        return choice

    def __getattr__(self, name: str) -> typing.Any:
        raise AttributeError(f"'{enum.Enum.__str__(self)}' object has no attribute '{name}'")

    def __str__(self) -> str:
        return str(self._value_)

    @classmethod
    def choices(cls) -> list[tuple[collections.abc.Hashable, _Display]]:
        """Return a list of tuples representing value and display of class choices."""
        return [(choice._value_, choice.display) for choice in cls]

    @classmethod
    def extract(cls, *choice_names: typing.Union[str, _Self], class_name: str = "") -> _Self:
        """Extract specified choices to a new subset."""
        if not class_name:
            class_name = f"{cls.__name__}.Subset"

        extracted_names = dict.fromkeys(_flatten_choice_names(choice_names))
        names = {name: getattr(cls, name) for name in extracted_names}
        return _create_subset(class_name, cls.__dict__, names)

    @classmethod
    def exclude(cls, *choice_names: typing.Union[str, _Self], class_name: str = "") -> _Self:
        """Exclude specified choices and return a new subset."""
        if not class_name:
            class_name = f"{cls.__name__}.Subset"

        excluded_names = set(_flatten_choice_names(choice_names))
        names = {name: getattr(cls, name) for name in cls._member_names_ if name not in excluded_names}
        return _create_subset(class_name, cls.__dict__, names)


def _get_public_methods(class_dict: typing.Mapping[str, typing.Any]) -> dict[str, typing.Any]:
    return {
        name: obj
        for name, obj in class_dict.items()
        if not name.startswith("_") and isinstance(obj, (types.FunctionType, staticmethod, classmethod))
    }


def _create_subset(
    class_name: str,
    class_dict: typing.Mapping[str, typing.Any],
    names: dict[str, typing.Any],
) -> typing.Any:
    choices_class = types.new_class(
        class_name,
        (Choices,),
        exec_body=lambda ns: ns.update(_get_public_methods(class_dict)),
    )
    return choices_class(class_name, names)


def _flatten_choice_names(choice_names: typing.Any) -> list[str]:
    names: list[str] = []
    for choice_name in choice_names:
        if isinstance(choice_name, type) and issubclass(choice_name, Choices):
            names.extend(choice.name for choice in choice_name)
        elif isinstance(choice_name, Choices):
            names.append(choice_name.name)
        else:
            names.append(choice_name)
    return names
