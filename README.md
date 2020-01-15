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
from better_choices import Choices
```

### Class definition
The choices can be defined with overriding `Choices` class.
```python
class STATUSES(Choices):
    CREATED = 'Created'
    PENDING = Choices.Choice('Pending', help_text='This set status to pending')
    ON_HOLD = Choices.Choice('On Hold', value='custom_on_hold')

    VALID = Choices.Subset('CREATED', ON_HOLD)

    class INTERNAL_STATUS(Choices):
        REVIEW = 'On Review'
```
> Overridden choices class cannot be initialised.

### Inline definition
Alternatively, the choices can be defined dynamically by creating new `Choices` object.
```python
STATUSES = Choices('STATUSES', SUCCESS='Success', FAIL='Error')
```
> The first `name` parameter of `Choices` constructor is optional and required only for better representation
> of the returned object.

### Choice accessors
You can access choices with dot and square-brackets notation.
```python
choice_created = STATUSES.CREATED
choice_on_hold = STATUSES['ON_HOLD']
```

### Choice parameters and inner choice accessors
By default, every choice has `value` and `display` parameters. Any other additional parameters can be specified
in `Choices.Choice` constructor (see class definition example).
```python
print( STATUSES.CREATED.value )             # 'created'
print( STATUSES.ON_HOLD.value )             # 'custom_on_hold'
print( STATUSES.PENDING.display )           # 'Pending'
print( STATUSES.PENDING.help_text )         # 'This set status to pending'
print( STATUSES.INTERNAL_STATUS.REVIEW )    # 'review'
```
> Every `Choices.Choice` object has a defined string representation of a `value` of the choice.
> `Choices.Choice` is a frozen data class, which object cannot be legally modified after the definition.

### Search in choices
Search in choices is performed by choice `value`.
```python
'created' in STATUSES                       # True
'custom_on_hold' in STATUSES                # True
'on_hold' in STATUSES                       # False
key, choice = STATUSES.find('created')      # ('CREATED', Choices.Choice)
```

### Search in subsets
Subsets are used to group several choices together (see class definition example) and perform search by a specific
choice or choice `value`.
```python
'custom_on_hold' in STATUSES.VALID          # True
STATUSES.CREATED in STATUSES.VALID          # True
```
> `Choices.Subset` is a `frozenset` that cannot be modified after the definition.

### Choices iteration
Choices class implements `__iter__` magic method, hence choices are iterable and return a tuple of `(value, display)`.
Methods `items`, `keys` and `choices` can be used to return tuples of keys and choices combinations.
```python
for value, display in STATUSES:
    print( value, display )

for key, choice in STATUSES.items():
    print( key, choice.value, choice.display )

for key in STATUSES.keys():
    print( key )

for choice in STATUSES.choices():
    print( choice.value, choice.display )
```

### Django model fields
Better choices are not different to the original Django choices in terms of usage in models.
```python
class MyModel(models.Model):
    status = models.CharField(choices=STATUSES, default=STATUSES.CREATED)
```
> Better choices are fully supported by Django migrations.

### Saving choices on models
Better choices are compatible with standard Django models manipulation.
```python
model = MyModel.objects.get(pk=1)
model.status = STATUSES.PENDING
model.save()
```

### Parameter extraction
The library provides a handy `extract` method to return specific parameters of the choices.
```python
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
```

## Tests
Run `python tests.py` for testing.

## License
Library is available under the MIT license. The included LICENSE file describes this in detail.
