import unittest

from collections.abc import Iterable
from django_better_choices import Choices


class TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.CONST = Choices(
            # choices
            VAL1='Display 1',
            VAL2=Choices.Choice('Display 2'),
            VAL3=Choices.Choice('Display 3', value='value-3'),
            VAL4=Choices.Choice('Display 4', param1='Param 4.1'),
            VAL5=Choices.Choice('Display 5', param1='Param 5.1', param2='Param 5.2'),
            # subsets
            SUBSET=Choices.Subset('VAL1', 'VAL2', 'VAL3'),
            # nested choices
            NESTED=Choices('NESTED', VAL10='Display 10', VAL20='Display 20')
        )

    def test_init(self):
        class LOCAL(Choices):
            VAL1 = 'Display 1'
            VAL2 = Choices.Choice('Display 2')
            SUBSET = Choices.Subset('VAL1', VAL2)

        self.assertEqual('Choices', self.CONST.__name__)
        self.assertEqual('CONST_NAME', Choices('CONST_NAME').__name__)
        self.assertEqual('LOCAL', LOCAL.__name__)

        self.assertEqual("LOCAL(VAL1='Display 1', VAL2='Display 2')", str(LOCAL))
        self.assertEqual("Choices('LOCAL', VAL1='Display 1', VAL2='Display 2')", repr(LOCAL))

        self.assertEqual('val1', LOCAL.VAL1)
        self.assertEqual('val2', str(LOCAL.VAL2))
        self.assertEqual('', str(Choices.Choice('Standalone')))

        self.assertEqual(LOCAL.VAL1, LOCAL.VAL1)
        self.assertNotEqual(LOCAL.VAL1, self.CONST.VAL1)

        with self.assertRaises(RuntimeError):
            LOCAL()  # init class

        with self.assertRaises(TypeError):
            Choices(VAL1=123.45)  # invalid choice type

        with self.assertRaises(KeyError):
            Choices(SUBSET=Choices.Subset('VAL1'))  # invalid subset key

        with self.assertRaises(KeyError):
            class _(Choices):  # invalid subset key reference
                VAL1 = 'Display 1'
                SUBSET = Choices.Subset(VAL1)

    def test_accessors(self):
        self.assertIsInstance(self.CONST.VAL1, Choices.Choice)
        self.assertIsInstance(self.CONST['VAL2'], Choices.Choice)
        self.assertIsInstance(self.CONST.NESTED.VAL10, Choices.Choice)

        self.assertEqual('Display 1', self.CONST.VAL1.display)
        self.assertEqual('val2', self.CONST.VAL2.value)
        self.assertEqual('value-3', self.CONST.VAL3.value)
        self.assertEqual('Param 4.1', self.CONST.VAL4.param1)
        self.assertEqual('val20', str(self.CONST.NESTED.VAL20))

        with self.assertRaises(AttributeError):
            _ = self.CONST.VAL0

        with self.assertRaises(KeyError):
            _ = self.CONST['VAL0']

    def test_search(self):
        self.assertIn('val1', self.CONST)
        self.assertIn('value-3', self.CONST)
        self.assertNotIn('val3', self.CONST)

        key, choice = self.CONST.find('val2')
        self.assertEqual('VAL2', key)
        self.assertEqual('Display 2', choice.display)
        self.assertIsNone(self.CONST.find('val0'))

        self.assertIn('val2', self.CONST.SUBSET)
        self.assertNotIn('val4', self.CONST.SUBSET)
        self.assertIn(self.CONST.VAL1, self.CONST.SUBSET)

    def test_iteration(self):
        self.assertTupleEqual(('VAL1', 'VAL2', 'VAL3', 'VAL4', 'VAL5'), self.CONST.keys())
        self.assertTupleEqual(tuple(zip(self.CONST.keys(), self.CONST.choices())), self.CONST.items())

        self.assertIsInstance(self.CONST, Iterable)
        self.assertListEqual(
            [
                ('val1', 'Display 1'),
                ('val2', 'Display 2'),
                ('value-3', 'Display 3'),
                ('val4', 'Display 4'),
                ('val5', 'Display 5'),
            ],
            list(self.CONST)
        )

    def test_extract(self):
        self.assertTupleEqual(
            ('Display 1', 'Display 2', 'Display 3', 'Display 4', 'Display 5'),
            self.CONST.extract('display')
        )
        self.assertTupleEqual(
            (
                ('val1', None),
                ('val2', None),
                ('value-3', None),
                ('val4', 'Param 4.1'),
                ('val5', 'Param 5.1'),
            ),
            self.CONST.extract('value', 'param1')
        )
        self.assertTupleEqual(
            (
                ('VAL1', 'Display 1'),
                ('VAL2', 'Display 2'),
                ('VAL3', 'Display 3'),
                ('VAL4', 'Display 4'),
                ('VAL5', 'Display 5'),
            ),
            self.CONST.extract('display', with_keys=True)
        )
        self.assertTupleEqual(
            (
                ('VAL1', ('val1', None, None)),
                ('VAL2', ('val2', None, None)),
                ('VAL3', ('value-3', None, None)),
                ('VAL4', ('val4', 'Param 4.1', None)),
                ('VAL5', ('val5', 'Param 5.1', 'Param 5.2')),
            ),
            self.CONST.extract('value', 'param1', 'param2', with_keys=True)
        )

        self.assertTupleEqual(
            ('val1', 'val2', 'value-3'),
            self.CONST.SUBSET.extract('value')
        )
        self.assertTupleEqual(
            (
                ('val1', 'Display 1'),
                ('val2', 'Display 2'),
                ('value-3', 'Display 3'),
            ),
            self.CONST.SUBSET.extract('value', 'display')
        )


if __name__ == '__main__':
    unittest.main()
