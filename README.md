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
class PAGE_STATUS(Choices):
    CREATED = 'Created'
    PENDING = Choices.Value('Pending', help_text='This set status to pending')
    ON_HOLD = Choices.Value('On Hold', value='custom_on_hold')

    VALID = Choices.Subset('CREATED', ON_HOLD)

    class INTERNAL_STATUS(Choices):
        REVIEW = 'On Review'
```
> Overridden choices classes cannot be initialised.

### Inline definition
Alternatively, the choices can be defined dynamically by creating new `Choices` object.
```python
PAGE_STATUS = Choices('PAGE_STATUS', SUCCESS='Success', FAIL='Error')
```
> The first `name` parameter of `Choices` constructor is optional and required only for better representation
> of the returned object.

### Value accessors
You can access choices values using dot notation and with `getattr()`.
```python
value_created = PAGE_STATUS.CREATED
value_review = PAGE_STATUS.INTERNAL_STATUS.REVIEW
value_on_hold = getattr(PAGE_STATUS, 'ON_HOLD')
```

### Values and value parameters
`Choices.Value` is a subclass of `str` and equals to its value. In addition to `display` parameter,
other optional parameters can be specified in `Choices.Value` constructor (see class definition example).
```python
print( PAGE_STATUS.CREATED )                # 'created'
print( PAGE_STATUS.ON_HOLD )                # 'custom_on_hold'
print( PAGE_STATUS.PENDING.display )        # 'Pending'
print( PAGE_STATUS.PENDING.help_text )      # 'This set status to pending'

PAGE_STATUS.ON_HOLD == 'custom_on_hold'     # True
PAGE_STATUS.CREATED == PAGE_STATUS.CREATED  # True
```
> `Choices.Value` is an immutable string class, which object cannot be modified after initialisation.
> Standard non-magic `str` methods are not supported in `Choices.Value`, in other cases its object behaves
> like a normal string, e.g. `{'val1': 'something'}[CHOICES.VAL1] == 'something'`.

### Search in choices
Search in choices is performed by value.
```python
'created' in PAGE_STATUS                    # True
'custom_on_hold' in PAGE_STATUS             # True
'on_hold' in PAGE_STATUS                    # False
value = PAGE_STATUS['custom_on_hold']       # Choices.Value
key, value = PAGE_STATUS.find('created')    # ('CREATED', Choices.Value)
index = PAGE_STATUS.index('pending')        # 1
```

### Search in subsets
Subsets are used to group several values together (see class definition example) and search by a specific value.
```python
'custom_on_hold' in PAGE_STATUS.VALID       # True
PAGE_STATUS.CREATED in PAGE_STATUS.VALID    # True
index = PAGE_STATUS.VALID.index('created')  # 0
```
> `Choices.Subset` is a subclass of `frozetset`, which cannot be modified after initialisation.
> Unlike original Python sets, instances of `Choices.Subset` maintain the order of values.

### Choices iteration
Choices class implements `__iter__` magic method, hence choices are iterable that yield `(value, display)`.
Methods `items()`, `keys()` and `values()` can be used to return tuples of keys and values combinations.
```python
for value, display in PAGE_STATUS:
    print( value, display )

for key, value in PAGE_STATUS.items():
    print( key, value, value.display )

for key in PAGE_STATUS.keys():
    print( key )

for value in PAGE_STATUS.values():
    print( value, value.display )
```
Additional `displays()` method is provided for choices and subsets to extract values display strings.
```python
for display in PAGE_STATUS.displays():
    print( display )

for display in PAGE_STATUS.SUBSET.displays():
    print( display )
```

### Django model fields
Better choices are not different to the original Django choices in terms of usage in models.
```python
class Page(models.Model):
    status = models.CharField(choices=PAGE_STATUS, default=PAGE_STATUS.CREATED)
```
> Better choices are fully supported by Django migrations.

### Saving choices on models
Better choices are compatible with standard Django models manipulation.
```python
page = Page.objects.get(pk=1)
page.status = PAGE_STATUS.PENDING
page.save()
```

## Tests
Run `python tests.py` for testing.

## License
Library is available under the MIT license. The included LICENSE file describes this in detail.
