# Django Better Choices

[![PyPI](https://img.shields.io/pypi/v/django-better-choices)](https://pypi.org/project/django-better-choices)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-better-choices)
[![Build Status](https://img.shields.io/github/workflow/status/lokhman/django-better-choices/CI/master)](https://github.com/lokhman/django-better-choices/actions?query=workflow%3ACI)
[![codecov](https://codecov.io/gh/lokhman/django-better-choices/branch/master/graph/badge.svg)](https://codecov.io/gh/lokhman/django-better-choices)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Better [choices](https://docs.djangoproject.com/en/3.0/ref/models/fields/#choices) library for Django web framework.

## Requirements
This library was written for Python 3.7+ and will not work in any earlier versions.

## Install

    pip install django-better-choices
    
## Usage
To start defining better choices, you need first to import the `Choices` class.
```python
from django_better_choices import Choices
```

### Class definition
The choices can be defined with overriding `Choices` class.
```python
class PageStatus(Choices):
    CREATED = 'Created'
    PENDING = Choices.Value('Pending', help_text='This set status to pending')
    ON_HOLD = Choices.Value('On Hold', value='custom_on_hold')

    VALID = Choices.Subset('CREATED', 'ON_HOLD')
    INVISIBLE = Choices.Subset('PENDING', 'ON_HOLD')

    class InternalStatus(Choices):
        REVIEW = _('On Review')

    @classmethod
    def get_help_text(cls):
        return tuple(
            value.help_text
            for value in cls.values()
            if hasattr(value, 'help_text')
        )
```
> Choices class key can be any *public* identifier (i.e. not starting with underscore `_`).
> Overridden choices classes cannot be initialised to obtain a new instance, calling the instance will return a tuple of choice entries.

### Inline definition
Alternatively, the choices can be defined dynamically by creating a new `Choices` instance.
```python
PageStatus = Choices('PageStatus', SUCCESS='Success', FAIL='Error', VALID=Choices.Subset('SUCCESS'))
```
> The first `name` parameter of `Choices` constructor is optional and required only for better representation of the returned instance.

### Value accessors
You can access choices values using dot notation and with `getattr()`.
```python
value_created = PageStatus.CREATED
value_review = PageStatus.InternalStatus.REVIEW
value_on_hold = getattr(PageStatus, 'ON_HOLD')
```

### Values and value parameters
`Choices.Value` can hold any `typing.Hashable` value and once compiled equals to this value. In addition to `display` parameter, other optional parameters can be specified in `Choices.Value` constructor (see class definition example).
```python
print( PageStatus.CREATED )                # 'created'
print( PageStatus.ON_HOLD )                # 'custom_on_hold'
print( PageStatus.PENDING.display )        # 'Pending'
print( PageStatus.PENDING.help_text )      # 'This set status to pending'

PageStatus.ON_HOLD == 'custom_on_hold'     # True
PageStatus.CREATED == PageStatus.CREATED   # True


class Rating(Choices):
    VERY_POOR = Choices.Value('Very poor', value=1)
    POOR = Choices.Value('Poor', value=2)
    OKAY = Choices.Value('Okay', value=3, alt='Not great, not terrible')
    GOOD = Choices.Value('Good', value=4)
    VERY_GOOD = Choices.Value('Very good', value=5)

print( Rating.VERY_GOOD )                  # 5
print( Rating.OKAY.alt )                   # 'Not great, not terrible'
print( {4: 'Alright'}[Rating.GOOD] )       # 'Alright'
```
> Instance of `Choices.Value` class cannot be modified after initialisation. All native non-magic methods can be overridden in `Choices.Value` custom parameters.

### Search in choices
Search in choices is performed by value.
```python
'created' in PageStatus                    # True
'custom_on_hold' in PageStatus             # True
'on_hold' in PageStatus                    # False
value = PageStatus['custom_on_hold']       # ValueType('custom_on_hold')
value = PageStatus.get('on_hold', 123.45)  # 123.45
key = PageStatus.get_key('created')        # 'CREATED'
```

### Search in subsets
Subsets are used to group several values together (see class definition example) and search by a specific value.
```python
'custom_on_hold' in PageStatus.VALID       # True
PageStatus.CREATED in PageStatus.VALID     # True
```
> `Choices.Subset` is a subclass of `tuple`, which is compiled to inner choices class after its definition. All internal or custom choices class methods or properties will be available in a subset class (see "Custom methods" section).

### Extract subset
Subsets of choices can be dynamically extracted with `extract()` method.
```python
PageStatus.extract('CREATED', 'ON_HOLD')   # ~= PageStatus.VALID
PageStatus.VALID.extract('ON_HOLD')        # Choices('PageStatus.VALID.Subset', ON_HOLD)
```

### Choices iteration
Choices class implements `__iter__` magic method, hence choices are iterable that yield choice entries (i.e. `(value, display)`). Methods `items()`, `keys()` and `values()` can be used to return tuples of keys and values combinations.
```python
for value, display in PageStatus:  # can also be used as callable, i.e. PageStatus()
    print( value, display )

for key, value in PageStatus.items():
    print( key, value, value.display )

for key in PageStatus.keys():
    print( key )

for value in PageStatus.values():
    print( value, value.display, value.__choice_entry__ )
```
Additional `displays()` method is provided for choices and subsets to extract values display strings.
```python
for display in PageStatus.displays():
    print( display )

for display in PageStatus.SUBSET.displays():
    print( display )
```
> Iteration methods `items()`, `keys()`, `values()`, `displays()`, as well as class constructor can accept keyword arguments to filter collections based on custom parameters, e.g. `PageStatus.values(help_text='Some', special=123)`.

### Set operations
Choices class and subsets support standard set operations: *union* (`|`), *intersection* (`&`), *difference* (`-`), and *symmetric difference* (`^`).
```python
PageStatus.VALID | PageStatus.INVISIBLE     # Choices(CREATED, ON_HOLD, PENDING)
PageStatus.VALID & PageStatus.INVISIBLE     # Choices(ON_HOLD)
PageStatus.VALID - PageStatus.INVISIBLE     # Choices(CREATED)
PageStatus.VALID ^ PageStatus.INVISIBLE     # Choices(CREATED, PENDING)
```

### Custom methods
All custom choices class methods or properties (non-values) will be available in all subsets.
```python
PageStatus.get_help_text()
PageStatus.VALID.get_help_text()
PageStatus.extract('PENDING', 'ON_HOLD').get_help_text()
PageStatus.VALID.extract('ON_HOLD').get_help_text()
```

### Django model fields
Better choices are not different from the original Django choices in terms of usage in models.
```python
class Page(models.Model):
    status = models.CharField(choices=PageStatus, default=PageStatus.CREATED)
```
> Better choices are fully supported by Django migrations and debug toolbar.

### Saving choices on models
Better choices are compatible with standard Django models manipulation.
```python
page = Page.objects.get(pk=1)
page.status = PageStatus.PENDING
page.save()
```

## Tests
Run `python tests.py` for testing.

## License
Library is available under the MIT license. The included LICENSE file describes this in detail.
