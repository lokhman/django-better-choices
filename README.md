# Django Better Choices

[![PyPI](https://img.shields.io/pypi/v/django-better-choices)](https://pypi.org/project/django-better-choices)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-better-choices)
[![Build Status](https://travis-ci.org/lokhman/django-better-choices.svg?branch=master)](https://travis-ci.org/lokhman/django-better-choices)
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
        REVIEW = 'On Review'

    @classmethod
    def get_help_text(cls):
        return tuple(
            value.help_text
            for value in cls.values()
            if hasattr(value, 'help_text')
        )
```
> Overridden choices classes cannot be initialised to obtain a new instance. Initialisation will return a tuple of choice entries.

### Inline definition
Alternatively, the choices can be defined dynamically by creating new `Choices` object.
```python
PageStatus = Choices('PageStatus', SUCCESS='Success', FAIL='Error')
```
> The first `name` parameter of `Choices` constructor is optional and required only for better representation of the returned object.

### Value accessors
You can access choices values using dot notation and with `getattr()`.
```python
value_created = PageStatus.CREATED
value_review = PageStatus.InternalStatus.REVIEW
value_on_hold = getattr(PageStatus, 'ON_HOLD')
```

### Values and value parameters
`Choices.Value` is a subclass of `str` and equals to its value. In addition to `display` parameter, other optional parameters can be specified in `Choices.Value` constructor (see class definition example).
```python
print( PageStatus.CREATED )                # 'created'
print( PageStatus.ON_HOLD )                # 'custom_on_hold'
print( PageStatus.PENDING.display )        # 'Pending'
print( PageStatus.PENDING.help_text )      # 'This set status to pending'

PageStatus.ON_HOLD == 'custom_on_hold'     # True
PageStatus.CREATED == PageStatus.CREATED   # True
```
> `Choices.Value` is an immutable string class, which object cannot be modified after initialisation. Native non-magic `str` methods can be overridden in `Choices.Value` custom parameters. `Choices.Value` behaves like a normal string, e.g. `{'val1': 'something'}[CHOICES.VAL1] == 'something'`.

### Search in choices
Search in choices is performed by value.
```python
'created' in PageStatus                    # True
'custom_on_hold' in PageStatus             # True
'on_hold' in PageStatus                    # False
value = PageStatus['custom_on_hold']       # Choices.Value
key, value = PageStatus.find('created')    # ('CREATED', Choices.Value)
```

### Search in subsets
Subsets are used to group several values together (see class definition example) and search by a specific value.
```python
'custom_on_hold' in PageStatus.VALID       # True
PageStatus.CREATED in PageStatus.VALID     # True
```
> `Choices.Subset` is a subclass of `tuple`, which is translated to inner choices class after definition. All internal or custom choices class methods or properties will be available in a subset class (see "Custom methods" section).

### Extract subset
Subsets of choices can be dynamically extracted using a special `extract()` method.
```python
PageStatus.extract('CREATED', 'ON_HOLD')   # ~= PageStatus.VALID
PageStatus.VALID.extract('ON_HOLD')        # Choices('PageStatus.VALID.Subset', ON_HOLD)
```

### Choices iteration
Choices class implements `__iter__` magic method, hence choices are iterable that yield choice entries (i.e. `(value, display)`). Methods `items()`, `keys()` and `values()` can be used to return tuples of keys and values combinations.
```python
for value, display in PageStatus:
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

### Set operations
Choices class supports standard set operations: *union* (`|`), *intersection* (`&`), *difference* (`-`), and *symmetric difference* (`^`).
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
Better choices are not different to the original Django choices in terms of usage in models.
```python
class Page(models.Model):
    status = models.CharField(choices=PageStatus, default=PageStatus.CREATED)
```
> Better choices are fully supported by Django migrations.

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
