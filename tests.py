import copy
import unittest

from collections.abc import Iterable

from django_better_choices import Choices, ValueType


class TestConst(Choices):
    # values
    VAL1 = 'Display 1'
    VAL2 = Choices.Value('Display 2')
    VAL3 = Choices.Value('Display 3', value='value-3')
    VAL4 = Choices.Value('Display 4', param1='Param 4.1', strip='Custom')
    VAL5 = Choices.Value('Display 5', param1='Param 5.1', param2='Param 5.2', strip='Custom')
    VAL6 = Choices.Value('Display 6', value=(1, 2, 3), param3='Param 6.1')
    VAL7 = Choices.Value('Display 7', value=7)

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


class TestCase(unittest.TestCase):
    def test_init(self):
        local = Choices(
            VAL1='Display 1',
            VAL2=Choices.Value('Display 2'),
            SUBSET=Choices.Subset('VAL1', 'VAL2', 'VAL1'),
        )

        self.assertEqual('TestConst', TestConst.__name__)
        self.assertEqual('CONST_NAME', Choices('CONST_NAME').__name__)
        self.assertEqual('TestConst.SUBSET1', TestConst.SUBSET1.__name__)
        self.assertEqual('Choices', local.__name__)

        self.assertEqual('Choices(VAL1, VAL2)', str(local))
        self.assertEqual("Choices('Choices', VAL1='Display 1', VAL2='Display 2')", repr(local))
        self.assertEqual('Choices.SUBSET(VAL1, VAL2)', str(local.SUBSET))
        self.assertEqual("Choices('TEST')", repr(Choices('TEST')))

        self.assertEqual('val1', local.VAL1)
        self.assertEqual('val2', str(local.VAL2))

        self.assertEqual(local.VAL1, str(local.VAL1))
        self.assertEqual(local.VAL1, TestConst.VAL1)

        self.assertEqual(123.45, TestConst.DATA1)
        self.assertEqual([1, 2, 3], TestConst.data2)

        with self.assertRaises(ValueError) as ctx:  # duplicated value
            Choices(VAL1='Display 1', VAL2=Choices.Value('Display 2', value='val1'))
        self.assertEqual("choices class 'Choices' has a duplicated value 'val1' for key 'VAL2'", str(ctx.exception))

        with self.assertRaises(KeyError) as ctx:  # invalid subset key
            class _(Choices):
                VAL1 = 'Display 1'
                SUBSET1 = Choices.Subset(VAL1)
        self.assertEqual("'Display 1'", str(ctx.exception))

        with self.assertRaises(TypeError) as ctx:  # invalid value type
            Choices(VAL=Choices.Value('Display', value=True))
        self.assertEqual("type 'bool' is not acceptable for choices class value 'Choices.VAL'", str(ctx.exception))

    def test_accessors(self):
        for _type in (ValueType, str):
            self.assertIsInstance(TestConst.VAL1, _type)
            self.assertIsInstance(TestConst.Nested.VAL10, _type)

        for _type in (ValueType, tuple):
            self.assertIsInstance(TestConst.VAL6, _type)

        self.assertEqual('Display 1', TestConst.VAL1.display)
        self.assertEqual('val2', TestConst.VAL2)
        self.assertEqual('value-3', TestConst.VAL3)
        self.assertEqual(7, TestConst[7])
        self.assertEqual((1, 2, 3), TestConst[1, 2, 3])
        self.assertEqual('Display 7', TestConst[7].display)
        self.assertEqual('Param 4.1', TestConst.VAL4.param1)
        self.assertEqual('val20', TestConst.Nested.VAL20)
        self.assertEqual('val4', getattr(TestConst, 'VAL4'))

        self.assertTrue('xal4', TestConst.VAL4.replace('v', 'x'))
        self.assertEqual('Custom', TestConst.VAL5.strip)

        with self.assertRaises(AttributeError) as ctx:  # invalid key
            _ = TestConst.VAL0
        self.assertEqual("type object 'TestConst' has no attribute 'VAL0'", str(ctx.exception))

        with self.assertRaises(AttributeError) as ctx:  # invalid value parameter
            _ = TestConst.VAL5.param3
        self.assertEqual("'TestConst.VAL5' object has no attribute 'param3'", str(ctx.exception))

    def test_search(self):
        self.assertIn('val1', TestConst)
        self.assertIn('value-3', TestConst)
        self.assertIn((1, 2, 3), TestConst)
        self.assertNotIn('val3', TestConst)
        self.assertNotIn((1, 2, 3, 4), TestConst)
        self.assertIn(TestConst.VAL1, TestConst)

        self.assertIsInstance(TestConst.get('val2'), ValueType)
        self.assertEqual('val2', TestConst.get(TestConst.VAL2))
        self.assertEqual('Display 2', TestConst.get('val2').display)
        self.assertEqual('VAL2', TestConst.get_key('val2'))
        self.assertIs(TestConst.get('val2'), TestConst['val2'])

        self.assertIsNone(TestConst.get('val0'))
        self.assertEqual(123.45, TestConst.get('val0', 123.45))
        self.assertIsNone(TestConst.get_key('val0'))
        self.assertEqual(123.45, TestConst.get_key('val0', 123.45))

        with self.assertRaises(ValueError) as ctx:
            _ = TestConst['val0']
        self.assertEqual("value 'val0' is not found in choices class 'TestConst'", str(ctx.exception))

        self.assertIn('val2', TestConst.SUBSET1)
        self.assertNotIn('val4', TestConst.SUBSET1)
        self.assertIn(TestConst.VAL1, TestConst.SUBSET1)

    def test_iteration(self):
        self.assertEqual(('VAL1', 'VAL2', 'VAL3', 'VAL4', 'VAL5', 'VAL6', 'VAL7'), TestConst.keys())
        self.assertEqual(('val1', 'val2', 'value-3', 'val4', 'val5', (1, 2, 3), 7), TestConst.values())
        self.assertEqual(tuple(zip(TestConst.keys(), TestConst.values())), TestConst.items())

        self.assertEqual(
            ('Display 1', 'Display 2', 'Display 3', 'Display 4', 'Display 5', 'Display 6', 'Display 7'),
            TestConst.displays(),
        )

        self.assertIsInstance(TestConst, Iterable)
        self.assertEqual(
            (
                ('val1', 'Display 1'),
                ('val2', 'Display 2'),
                ('value-3', 'Display 3'),
                ('val4', 'Display 4'),
                ('val5', 'Display 5'),
                ((1, 2, 3), 'Display 6'),
                (7, 'Display 7'),
            ),
            tuple(TestConst)
        )
        self.assertTrue(callable(TestConst))
        self.assertEqual(tuple(TestConst), TestConst())

        self.assertEqual(
            (
                ('val1', 'Display 1'),
                ('val2', 'Display 2'),
                ('value-3', 'Display 3'),
            ),
            tuple(TestConst.SUBSET1)
        )
        self.assertTrue(callable(TestConst.SUBSET1))
        self.assertEqual(tuple(TestConst.SUBSET1), TestConst.SUBSET1())

        self.assertEqual(('VAL1', 'VAL2', 'VAL3'), TestConst.SUBSET1.keys())
        self.assertEqual(('val1', 'val2', 'value-3'), TestConst.SUBSET1.values())
        self.assertEqual(
            tuple(zip(TestConst.SUBSET1.keys(), TestConst.SUBSET1.values())),
            TestConst.SUBSET1.items()
        )
        self.assertEqual(('Display 1', 'Display 2', 'Display 3'), TestConst.SUBSET1.displays())

        self.assertEqual(
            (
                ('val4', 'Display 4'),
                ('val5', 'Display 5'),
            ),
            TestConst(strip='Custom')
        )
        self.assertEqual(('VAL4', 'VAL5'), TestConst.keys(strip='Custom'))
        self.assertEqual(('val4', 'val5'), TestConst.values(strip='Custom'))
        self.assertEqual(
            tuple(zip(TestConst.keys(strip='Custom'), TestConst.values(strip='Custom'))),
            TestConst.items(strip='Custom')
        )
        self.assertEqual(('Display 4', 'Display 5'), TestConst.displays(strip='Custom'))

        self.assertEqual((), TestConst.values(strip='Custom', param0='Unknown'))
        self.assertEqual(('val5',), TestConst.values(strip='Custom', param2='Param 5.2'))

    def test_extract(self):
        choices_extract = TestConst.extract('VAL2', 'VAL5')
        self.assertEqual('TestConst.Subset', choices_extract.__name__)
        self.assertEqual(('val2', 'val5'), choices_extract.values())

        subset_extract = TestConst.SUBSET1.extract('VAL1', 'VAL3', name='SPECIAL')
        self.assertEqual('TestConst.SUBSET1.SPECIAL', subset_extract.__name__)
        self.assertEqual(('val1', 'value-3'), subset_extract.values())

    def test_operations(self):
        union = TestConst.SUBSET1 | TestConst.SUBSET2
        self.assertEqual('TestConst.SUBSET1|TestConst.SUBSET2', union.__name__)
        self.assertEqual(('VAL1', 'VAL2', 'VAL3', 'VAL5'), union.keys())
        self.assertEqual((TestConst.VAL1, TestConst.VAL2, TestConst.VAL3, TestConst.VAL5), union.values())

        intersection = TestConst.SUBSET1 & TestConst.SUBSET2
        self.assertEqual('TestConst.SUBSET1&TestConst.SUBSET2', intersection.__name__)
        self.assertEqual(('VAL3',), intersection.keys())
        self.assertEqual((TestConst.VAL3, ), intersection.values())

        difference = TestConst.SUBSET1 - TestConst.SUBSET2
        self.assertEqual('TestConst.SUBSET1-TestConst.SUBSET2', difference.__name__)
        self.assertEqual(('VAL1', 'VAL2'), difference.keys())
        self.assertEqual((TestConst.VAL1, TestConst.VAL2), difference.values())

        symmetric_difference = TestConst.SUBSET1 ^ TestConst.SUBSET2
        self.assertEqual('TestConst.SUBSET1^TestConst.SUBSET2', symmetric_difference.__name__)
        self.assertEqual(('VAL1', 'VAL2', 'VAL5'), symmetric_difference.keys())
        self.assertEqual((TestConst.VAL1, TestConst.VAL2, TestConst.VAL5), symmetric_difference.values())

    def test_copy(self):
        self.assertEqual('val1', copy.copy(TestConst.VAL1))
        self.assertEqual('value-3', copy.copy(TestConst.VAL3))
        self.assertEqual('val2', copy.deepcopy(TestConst.VAL2))
        self.assertEqual((1, 2, 3), copy.deepcopy(TestConst.VAL6))
        self.assertEqual('Param 6.1', copy.deepcopy(TestConst.VAL6).param3)

        self.assertIsNot(TestConst.VAL4, copy.copy(TestConst.VAL4))
        self.assertIsNot(TestConst.VAL7, copy.deepcopy(TestConst.VAL7))


if __name__ == '__main__':
    unittest.main()
