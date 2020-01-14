# Django Better Choices
Better choices library for Django web framework.

## Install

    pip install django-better-choices
    
## Usage
To start defining better choices, you need first to import the `Choices` class.
```python
from better_choices import Choices
```

### Class definition
Your choices can be defined with overriding `Choices` class.
```python
class ORDER_STATUS(Choices):
    CREATED = 'Created'
    PENDING = Choices.Choice('Pending', help_text='This set status to pending')
    ON_HOLD = Choices.Choice('On Hold', value='custom_on_hold')

    VALID = Choices.Subset('CREATED', ON_HOLD)

    # supports inner choices
    class INTERNAL_STATUS(Choices):
        REVIEW = 'On Review'
```

### Inline definition
Alternatively, your choices can be defined by creating new `Choices` object.
```python
ORDER_STATUS = Choices('PAYMENT_STATUS', SUCCESS='Success', FAIL='Error')
```
> The first `name` argument of `Choices` constructor is optional and is required only for better
> representation of the returned object.

### Choice accessors
You can access choices using dot and square-brackets notation.
```python
choice_created = ORDER_STATUS.CREATED
choice_on_hold = ORDER_STATUS['ON_HOLD']
```

### Choice parameters and inner choice accessors
By default, every choice, as a data class, has `value` and `display` parameters.
Any other additional parameters can be specified in `Choices.Choice` constructor (see class definition example).
```python
print( ORDER_STATUS.CREATED.value )             # 'created'
print( ORDER_STATUS.ON_HOLD.value )             # 'custom_on_hold'
print( ORDER_STATUS.PENDING.display )           # 'Pending'
print( ORDER_STATUS.PENDING.help_text )         # 'This set status to pending'
print( ORDER_STATUS.INTERNAL_STATUS.REVIEW )    # 'review'
```
> Every `Choices.Choice` object has defined string representation as a `value` of the choice.
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
> `Choices.Subset` is a `frozenset` and cannot be modified after the definition.

### Choices iteration
Choices class implements `__iter__` magic method, hence choices are iterable and return a tuple of `(value, display)`.
Methods `items`, `keys` and `choices` can be used to return tuples of keys and choices.
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
They are also fully supported by Django migrations.
```python
class Order(models.Model):
    status = models.CharField(choices=ORDER_STATUS, default=ORDER_STATUS.CREATED)
```

### Saving choices on models
Better choices are entirely compatible with standard Django models manipulation.
```python
order = Order.objects.get(pk=1)
order.status = ORDER_STATUS.PENDING
order.save()
```

### Parameter extraction
The library provides a handy `extract` method to return specific choices parameters.
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
