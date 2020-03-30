import unittest

from collections.abc import Iterable
from django_better_choices import Choices


class TestCase(unittest.TestCase):
    class CONST(Choices):
        # values
        VAL1 = 'Display 1'
        VAL2 = Choices.Value('Display 2')
        VAL3 = Choices.Value('Display 3', value='value-3')
        VAL4 = Choices.Value('Display 4', param1='Param 4.1')
        VAL5 = Choices.Value('Display 5', param1='Param 5.1', param2='Param 5.2')

        # subsets
        SUBSET = Choices.Subset('VAL1', 'VAL2', 'VAL3')

        # nested choices
        class NESTED(Choices):
            VAL10 = 'Display 10'
            VAL20 = 'Display 20'

    def test_init(self):
        LOCAL = Choices(
            VAL1='Display 1',
            VAL2=Choices.Value('Display 2'),
            SUBSET=Choices.Subset('VAL1', 'VAL2', 'VAL1'),
        )

        self.assertEqual('CONST', self.CONST.__name__)
        self.assertEqual('CONST_NAME', Choices('CONST_NAME').__name__)
        self.assertEqual('CONST.SUBSET', self.CONST.SUBSET.__name__)
        self.assertEqual('Choices', LOCAL.__name__)

        self.assertEqual('Choices(VAL1, VAL2)', str(LOCAL))
        self.assertEqual("Choices('Choices', VAL1='Display 1', VAL2='Display 2')", repr(LOCAL))
        self.assertEqual('Choices.SUBSET(VAL1, VAL2)', str(LOCAL.SUBSET))
        self.assertEqual("Choices('TEST')", repr(Choices('TEST')))

        self.assertEqual('val1', LOCAL.VAL1)
        self.assertEqual('val2', str(LOCAL.VAL2))
        self.assertEqual('', Choices.Value('Standalone'))

        self.assertEqual(LOCAL.VAL1, str(LOCAL.VAL1))
        self.assertEqual(LOCAL.VAL1, self.CONST.VAL1)

        with self.assertRaises(RuntimeError):  # init class
            LOCAL()

        with self.assertRaises(TypeError):  # invalid value type
            Choices(VAL1=123.45)

        with self.assertRaises(ValueError):  # duplicated value
            Choices(VAL1='Display 1', VAL2=Choices.Value('Display 2', value='val1'))

        with self.assertRaises(KeyError):  # invalid subset key
            Choices(SUBSET=Choices.Subset('VAL1'))

        with self.assertRaises(KeyError):  # invalid subset key reference
            class _(Choices):
                VAL1 = 'Display 1'
                SUBSET = Choices.Subset(VAL1)

    def test_accessors(self):
        self.assertIsInstance(self.CONST.VAL1, Choices.Value)
        self.assertIsInstance(self.CONST.NESTED.VAL10, str)

        self.assertEqual('Display 1', self.CONST.VAL1.display)
        self.assertEqual('val2', self.CONST.VAL2)
        self.assertEqual('value-3', self.CONST.VAL3)
        self.assertEqual('Param 4.1', self.CONST.VAL4.param1)
        self.assertEqual('val20', self.CONST.NESTED.VAL20)
        self.assertEqual('val4', getattr(self.CONST, 'VAL4'))

        with self.assertRaises(AttributeError):  # invalid key
            _ = self.CONST.VAL0

        with self.assertRaises(AttributeError):  # invalid value parameter
            _ = self.CONST.VAL5.param3

    def test_search(self):
        self.assertIn('val1', self.CONST)
        self.assertIn('value-3', self.CONST)
        self.assertNotIn('val3', self.CONST)
        self.assertIn(self.CONST.VAL1, self.CONST)

        key, value = self.CONST.find('val2')
        self.assertEqual('VAL2', key)
        self.assertEqual('Display 2', value.display)
        self.assertIsNone(self.CONST.find('val0'))
        self.assertEqual(value, self.CONST['val2'])
        self.assertIsNotNone(self.CONST.find(self.CONST.VAL2))

        with self.assertRaises(KeyError):
            _ = self.CONST['val0']

        self.assertIn('val2', self.CONST.SUBSET)
        self.assertNotIn('val4', self.CONST.SUBSET)
        self.assertIn(self.CONST.VAL1, self.CONST.SUBSET)

    def test_iteration(self):
        self.assertTupleEqual(('VAL1', 'VAL2', 'VAL3', 'VAL4', 'VAL5'), self.CONST.keys())
        self.assertTupleEqual(('val1', 'val2', 'value-3', 'val4', 'val5'), self.CONST.values())
        self.assertTupleEqual(tuple(zip(self.CONST.keys(), self.CONST.values())), self.CONST.items())
        self.assertTupleEqual(('Display 1', 'Display 2', 'Display 3', 'Display 4', 'Display 5'), self.CONST.displays())

        self.assertIsInstance(self.CONST, Iterable)
        self.assertTupleEqual(
            (
                ('val1', 'Display 1'),
                ('val2', 'Display 2'),
                ('value-3', 'Display 3'),
                ('val4', 'Display 4'),
                ('val5', 'Display 5'),
            ),
            tuple(self.CONST)
        )

        self.assertTupleEqual(
            (
                ('val1', 'Display 1'),
                ('val2', 'Display 2'),
                ('value-3', 'Display 3'),
            ),
            tuple(self.CONST.SUBSET)
        )

        self.assertTupleEqual(('VAL1', 'VAL2', 'VAL3'), self.CONST.SUBSET.keys())
        self.assertTupleEqual(('val1', 'val2', 'value-3'), self.CONST.SUBSET.values())
        self.assertTupleEqual(
            tuple(zip(self.CONST.SUBSET.keys(), self.CONST.SUBSET.values())),
            self.CONST.SUBSET.items()
        )

        self.assertTupleEqual(('Display 1', 'Display 2', 'Display 3'), self.CONST.SUBSET.displays())

    def test_extract(self):
        choices_extract = self.CONST.extract('VAL2', 'VAL5')
        self.assertEqual('CONST.Subset', choices_extract.__name__)
        self.assertTupleEqual(('val2', 'val5'), choices_extract.values())

        subset_extract = self.CONST.SUBSET.extract('VAL1', 'VAL3', name='SPECIAL')
        self.assertEqual('CONST.SUBSET.SPECIAL', subset_extract.__name__)
        self.assertTupleEqual(('val1', 'value-3'), subset_extract.values())


if __name__ == '__main__':
    unittest.main()
