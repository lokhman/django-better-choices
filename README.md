# Django Better Choices
Better [choices](https://docs.djangoproject.com/en/3.0/ref/models/fields/#choices) library for Django web framework.

## Requirements
This library was written for Python 3.7+ and will not work in earlier versions.

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
class ORDER_STATUS(Choices):
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
ORDER_STATUS = Choices('PAYMENT_STATUS', SUCCESS='Success', FAIL='Error')
```
> The first `name` parameter of `Choices` constructor is optional and required only for better representation
> of the returned object.

### Choice accessors
You can access choices with dot and square-brackets notation.
```python
choice_created = ORDER_STATUS.CREATED
choice_on_hold = ORDER_STATUS['ON_HOLD']
```

### Choice parameters and inner choice accessors
By default, every choice has `value` and `display` parameters. Any other additional parameters can be specified
in `Choices.Choice` constructor (see class definition example).
```python
print( ORDER_STATUS.CREATED.value )             # 'created'
print( ORDER_STATUS.ON_HOLD.value )             # 'custom_on_hold'
print( ORDER_STATUS.PENDING.display )           # 'Pending'
print( ORDER_STATUS.PENDING.help_text )         # 'This set status to pending'
print( ORDER_STATUS.INTERNAL_STATUS.REVIEW )    # 'review'
```
> Every `Choices.Choice` object has a defined string representation of a `value` of the choice.
> `Choices.Choice` is a frozen data class, which object cannot be legally modified after the definition.

### Search in choices
Search in choices is performed by choice `value`.
```python
'created' in ORDER_STATUS                       # True
'custom_on_hold' in ORDER_STATUS                # True
'on_hold' in ORDER_STATUS                       # False
key, choice = ORDER_STATUS.find('created')      # ('CREATED', Choices.Choice)
```

### Search in subsets
Subsets are used to group several choices together (see class definition example) and perform search by a specific
choice or choice `value`.
```python
'custom_on_hold' in ORDER_STATUS.VALID          # True
ORDER_STATUS.CREATED in ORDER_STATUS.VALID      # True
```
> `Choices.Subset` is a `frozenset` that cannot be modified after the definition.

### Choices iteration
Choices class implements `__iter__` magic method, hence choices are iterable and return a tuple of `(value, display)`.
Methods `items`, `keys` and `choices` can be used to return tuples of keys and choices combinations.
```python
for value, display in ORDER_STATUS:
    print( value, display )

for key, choice in ORDER_STATUS.items():
    print( key, choice.value, choice.display )

for key in ORDER_STATUS.keys():
    print( key )

for choice in ORDER_STATUS.choices():
    print( choice.value, choice.display )
```

### Django model fields
Better choices are not different to the original Django choices in terms of usage in models.
```python
class Order(models.Model):
    status = models.CharField(choices=ORDER_STATUS, default=ORDER_STATUS.CREATED)
```
> Better choices are fully supported by Django migrations.

### Saving choices on models
Better choices are compatible with standard Django models manipulation.
```python
order = Order.objects.get(pk=1)
order.status = ORDER_STATUS.PENDING
order.save()
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
