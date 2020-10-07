import unittest

from collections.abc import Iterable

from django_better_choices import Choices


class TestCase(unittest.TestCase):
    class Const(Choices):
        # values
        VAL1 = 'Display 1'
        VAL2 = Choices.Value('Display 2')
        VAL3 = Choices.Value('Display 3', value='value-3')
        VAL4 = Choices.Value('Display 4', param1='Param 4.1', strip='Custom')
        VAL5 = Choices.Value('Display 5', param1='Param 5.1', param2='Param 5.2', strip='Custom')

        # subsets
        SUBSET1 = Choices.Subset('VAL1', 'VAL2', 'VAL3')
        SUBSET2 = Choices.Subset('VAL3', 'VAL5')

        # arbitrary data
        DATA1 = 123.45
        data2 = [1, 2, 3]

        # nested choices
        class Nested(Choices):
            VAL10 = 'Display 10'
            VAL20 = 'Display 20'

    def test_init(self):
        local = Choices(
            VAL1='Display 1',
            VAL2=Choices.Value('Display 2'),
            SUBSET=Choices.Subset('VAL1', 'VAL2', 'VAL1'),
        )

        self.assertEqual('Const', self.Const.__name__)
        self.assertEqual('CONST_NAME', Choices('CONST_NAME').__name__)
        self.assertEqual('Const.SUBSET1', self.Const.SUBSET1.__name__)
        self.assertEqual('Choices', local.__name__)

        self.assertEqual('Choices(VAL1, VAL2)', str(local))
        self.assertEqual("Choices('Choices', VAL1='Display 1', VAL2='Display 2')", repr(local))
        self.assertEqual('Choices.SUBSET(VAL1, VAL2)', str(local.SUBSET))
        self.assertEqual("Choices('TEST')", repr(Choices('TEST')))

        self.assertEqual('val1', local.VAL1)
        self.assertEqual('val2', str(local.VAL2))
        self.assertEqual('', Choices.Value('Standalone'))

        self.assertEqual(local.VAL1, str(local.VAL1))
        self.assertEqual(local.VAL1, self.Const.VAL1)

        self.assertEqual(123.45, self.Const.DATA1)
        self.assertEqual([1, 2, 3], self.Const.data2)

        with self.assertRaises(ValueError):  # duplicated value
            Choices(VAL1='Display 1', VAL2=Choices.Value('Display 2', value='val1'))

        with self.assertRaises(KeyError):  # invalid subset key
            Choices(SUBSET1=Choices.Subset('VAL1'))

        with self.assertRaises(KeyError):  # invalid subset key reference
            class _(Choices):
                VAL1 = 'Display 1'
                SUBSET1 = Choices.Subset(VAL1)

        copy = self.Const.__copy__()
        self.assertIsNot(self.Const, copy)
        self.assertIsNot(self.Const.VAL1, copy.VAL1)
        self.assertEqual('Const', copy.__name__)
        self.assertEqual(len(self.Const.items()), len(copy.items()))

        copy.insert('val123', 'Whatever')
        self.assertEqual('Whatever', copy.val123.display)

        with self.assertRaises(AssertionError):
            copy.insert('', 'test')

        with self.assertRaises(AssertionError):
            copy.insert('invalid!', 'test')

        with self.assertRaises(AssertionError):
            copy.insert('val', 123.45)

    def test_accessors(self):
        self.assertIsInstance(self.Const.VAL1, Choices.Value)
        self.assertIsInstance(self.Const.Nested.VAL10, str)

        self.assertEqual('Display 1', self.Const.VAL1.display)
        self.assertEqual('val2', self.Const.VAL2)
        self.assertEqual('value-3', self.Const.VAL3)
        self.assertEqual('Param 4.1', self.Const.VAL4.param1)
        self.assertEqual('val20', self.Const.Nested.VAL20)
        self.assertEqual('val4', getattr(self.Const, 'VAL4'))

        self.assertTrue('xal4', self.Const.VAL4.replace('v', 'x'))
        self.assertEqual('Custom', self.Const.VAL5.strip)

        with self.assertRaises(AttributeError):  # invalid key
            _ = self.Const.VAL0

        with self.assertRaises(AttributeError):  # invalid value parameter
            _ = self.Const.VAL5.param3

    def test_search(self):
        self.assertIn('val1', self.Const)
        self.assertIn('value-3', self.Const)
        self.assertNotIn('val3', self.Const)
        self.assertIn(self.Const.VAL1, self.Const)

        self.assertIsInstance(self.Const.get('val2'), Choices.Value)
        self.assertEqual('val2', self.Const.get(self.Const.VAL2))
        self.assertEqual('Display 2', self.Const.get('val2').display)
        self.assertEqual('VAL2', self.Const.get_key('val2'))
        self.assertIs(self.Const.get('val2'), self.Const['val2'])

        self.assertIsNone(self.Const.get('val0'))
        self.assertEqual(123.45, self.Const.get('val0', 123.45))
        self.assertIsNone(self.Const.get_key('val0'))
        self.assertEqual(123.45, self.Const.get_key('val0', 123.45))

        with self.assertRaises(KeyError):
            _ = self.Const['val0']

        self.assertIn('val2', self.Const.SUBSET1)
        self.assertNotIn('val4', self.Const.SUBSET1)
        self.assertIn(self.Const.VAL1, self.Const.SUBSET1)

    def test_iteration(self):
        self.assertEqual(('VAL1', 'VAL2', 'VAL3', 'VAL4', 'VAL5'), self.Const.keys())
        self.assertEqual(('val1', 'val2', 'value-3', 'val4', 'val5'), self.Const.values())
        self.assertEqual(tuple(zip(self.Const.keys(), self.Const.values())), self.Const.items())
        self.assertEqual(('Display 1', 'Display 2', 'Display 3', 'Display 4', 'Display 5'), self.Const.displays())

        self.assertIsInstance(self.Const, Iterable)
        self.assertEqual(
            (
                ('val1', 'Display 1'),
                ('val2', 'Display 2'),
                ('value-3', 'Display 3'),
                ('val4', 'Display 4'),
                ('val5', 'Display 5'),
            ),
            tuple(self.Const)
        )
        self.assertTrue(callable(self.Const))
        self.assertEqual(tuple(self.Const), self.Const())

        self.assertEqual(
            (
                ('val1', 'Display 1'),
                ('val2', 'Display 2'),
                ('value-3', 'Display 3'),
            ),
            tuple(self.Const.SUBSET1)
        )
        self.assertTrue(callable(self.Const.SUBSET1))
        self.assertEqual(tuple(self.Const.SUBSET1), self.Const.SUBSET1())

        self.assertEqual(('VAL1', 'VAL2', 'VAL3'), self.Const.SUBSET1.keys())
        self.assertEqual(('val1', 'val2', 'value-3'), self.Const.SUBSET1.values())
        self.assertEqual(
            tuple(zip(self.Const.SUBSET1.keys(), self.Const.SUBSET1.values())),
            self.Const.SUBSET1.items()
        )
        self.assertEqual(('Display 1', 'Display 2', 'Display 3'), self.Const.SUBSET1.displays())

        self.assertEqual(
            (
                ('val4', 'Display 4'),
                ('val5', 'Display 5'),
            ),
            self.Const(strip='Custom')
        )
        self.assertEqual(('VAL4', 'VAL5'), self.Const.keys(strip='Custom'))
        self.assertEqual(('val4', 'val5'), self.Const.values(strip='Custom'))
        self.assertEqual(
            tuple(zip(self.Const.keys(strip='Custom'), self.Const.values(strip='Custom'))),
            self.Const.items(strip='Custom')
        )
        self.assertEqual(('Display 4', 'Display 5'), self.Const.displays(strip='Custom'))

        self.assertEqual((), self.Const.values(strip='Custom', param0='Unknown'))
        self.assertEqual(('val5',), self.Const.values(strip='Custom', param2='Param 5.2'))

    def test_extract(self):
        choices_extract = self.Const.extract('VAL2', 'VAL5')
        self.assertEqual('Const.Subset', choices_extract.__name__)
        self.assertEqual(('val2', 'val5'), choices_extract.values())

        subset_extract = self.Const.SUBSET1.extract('VAL1', 'VAL3', name='SPECIAL')
        self.assertEqual('Const.SUBSET1.SPECIAL', subset_extract.__name__)
        self.assertEqual(('val1', 'value-3'), subset_extract.values())

    def test_operations(self):
        union = self.Const.SUBSET1 | self.Const.SUBSET2
        self.assertEqual('Const.SUBSET1|Const.SUBSET2', union.__name__)
        self.assertEqual(('VAL1', 'VAL2', 'VAL3', 'VAL5'), union.keys())
        self.assertEqual((self.Const.VAL1, self.Const.VAL2, self.Const.VAL3, self.Const.VAL5), union.values())

        intersection = self.Const.SUBSET1 & self.Const.SUBSET2
        self.assertEqual('Const.SUBSET1&Const.SUBSET2', intersection.__name__)
        self.assertEqual(('VAL3',), intersection.keys())
        self.assertEqual((self.Const.VAL3, ), intersection.values())

        difference = self.Const.SUBSET1 - self.Const.SUBSET2
        self.assertEqual('Const.SUBSET1-Const.SUBSET2', difference.__name__)
        self.assertEqual(('VAL1', 'VAL2'), difference.keys())
        self.assertEqual((self.Const.VAL1, self.Const.VAL2), difference.values())

        symmetric_difference = self.Const.SUBSET1 ^ self.Const.SUBSET2
        self.assertEqual('Const.SUBSET1^Const.SUBSET2', symmetric_difference.__name__)
        self.assertEqual(('VAL1', 'VAL2', 'VAL5'), symmetric_difference.keys())
        self.assertEqual((self.Const.VAL1, self.Const.VAL2, self.Const.VAL5), symmetric_difference.values())

    def test_str_methods(self):
        for method in (fn for fn in dir(str) if not fn.startswith('__')):
            self.assertIn(method, Choices.Value.__dict__)


if __name__ == '__main__':
    unittest.main()
