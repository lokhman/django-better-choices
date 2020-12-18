import copy
import json
import pickle
import unittest

from collections.abc import Iterable

from django_better_choices import Choices, ValueType


class TestChoices(Choices):
    # values
    VAL1 = "Display 1"
    VAL2 = Choices.Value("Display 2")
    VAL3 = Choices.Value("Display 3", value="value-3")
    VAL4 = Choices.Value("Display 4", param1="Param 4.1", strip="Custom")
    VAL5 = Choices.Value("Display 5", param1="Param 5.1", param2="Param 5.2", strip="Custom")
    VAL6 = Choices.Value("Display 6", value=(1, 2, 3), param3="Param 6.1")
    VAL7 = Choices.Value("Display 7", value=7)

    # subsets
    SUBSET1 = Choices.Subset("VAL1", "VAL2", "VAL3")
    SUBSET2 = Choices.Subset("VAL3", "VAL5")

    # arbitrary data
    DATA1 = 123.45
    data2 = [1, 2, 3]

    # nested choices
    class Nested(Choices):
        VAL10 = "Display 10"
        VAL20 = "Display 20"

    @classmethod
    def get_upper_displays(cls):
        return tuple(map(str.upper, cls.displays()))


class TestCase(unittest.TestCase):
    def test_init(self):
        local = Choices(
            VAL1="Display 1",
            VAL2=Choices.Value("Display 2"),
            SUBSET=Choices.Subset("VAL1", "VAL2", "VAL1"),
        )

        self.assertEqual("TestChoices", TestChoices.__name__)
        self.assertEqual("CONST_NAME", Choices("CONST_NAME").__name__)
        self.assertEqual("TestChoices.SUBSET1", TestChoices.SUBSET1.__name__)
        self.assertEqual("Choices", local.__name__)

        self.assertEqual("Choices(VAL1, VAL2)", str(local))
        self.assertEqual("Choices('Choices', VAL1='Display 1', VAL2='Display 2')", repr(local))
        self.assertEqual("Choices.SUBSET(VAL1, VAL2)", str(local.SUBSET))
        self.assertEqual("Choices('TEST')", repr(Choices("TEST")))

        self.assertEqual("val1", local.VAL1)
        self.assertEqual("val2", str(local.VAL2))

        self.assertEqual(local.VAL1, str(local.VAL1))
        self.assertEqual(local.VAL1, TestChoices.VAL1)

        self.assertEqual(123.45, TestChoices.DATA1)
        self.assertEqual([1, 2, 3], TestChoices.data2)

        with self.assertRaises(ValueError) as ctx:  # duplicated value
            Choices(VAL1="Display 1", VAL2=Choices.Value("Display 2", value="val1"))
        self.assertEqual("choices class 'Choices' has a duplicated value 'val1' for key 'VAL2'", str(ctx.exception))

        with self.assertRaises(KeyError) as ctx:  # invalid subset key
            class _(Choices):
                VAL1 = "Display 1"
                SUBSET1 = Choices.Subset(VAL1)

        self.assertEqual("'Display 1'", str(ctx.exception))

        with self.assertRaises(TypeError) as ctx:  # invalid value type
            Choices(VAL=Choices.Value("Display", value=True))
        self.assertEqual("type 'bool' is not acceptable for choices class value 'Choices.VAL'", str(ctx.exception))

    def test_accessors(self):
        for _type in (ValueType, str):
            self.assertIsInstance(TestChoices.VAL1, _type)
            self.assertIsInstance(TestChoices.Nested.VAL10, _type)

        for _type in (ValueType, tuple):
            self.assertIsInstance(TestChoices.VAL6, _type)

        self.assertEqual("Display 1", TestChoices.VAL1.display)
        self.assertEqual("val2", TestChoices.VAL2)
        self.assertEqual("value-3", TestChoices.VAL3)
        self.assertEqual(7, TestChoices[7])
        self.assertEqual((1, 2, 3), TestChoices[1, 2, 3])
        self.assertEqual("Display 7", TestChoices[7].display)
        self.assertEqual("Param 4.1", TestChoices.VAL4.param1)
        self.assertEqual("val20", TestChoices.Nested.VAL20)
        self.assertEqual("val4", getattr(TestChoices, "VAL4"))

        self.assertTrue("xal4", TestChoices.VAL4.replace("v", "x"))
        self.assertEqual("Custom", TestChoices.VAL5.strip)

        with self.assertRaises(AttributeError) as ctx:  # invalid key
            _ = TestChoices.VAL0
        self.assertEqual("type object 'TestChoices' has no attribute 'VAL0'", str(ctx.exception))

        with self.assertRaises(AttributeError) as ctx:  # invalid value parameter
            _ = TestChoices.VAL5.param3
        self.assertEqual("'TestChoices_VAL5' object has no attribute 'param3'", str(ctx.exception))

    def test_search(self):
        self.assertIn("val1", TestChoices)
        self.assertIn("value-3", TestChoices)
        self.assertIn((1, 2, 3), TestChoices)
        self.assertNotIn("val3", TestChoices)
        self.assertNotIn((1, 2, 3, 4), TestChoices)
        self.assertIn(TestChoices.VAL1, TestChoices)

        self.assertIsInstance(TestChoices.get("val2"), ValueType)
        self.assertEqual("val2", TestChoices.get(TestChoices.VAL2))
        self.assertEqual("Display 2", TestChoices.get("val2").display)
        self.assertEqual("VAL2", TestChoices.get_key("val2"))
        self.assertIs(TestChoices.get("val2"), TestChoices["val2"])

        self.assertIsNone(TestChoices.get("val0"))
        self.assertEqual(123.45, TestChoices.get("val0", 123.45))
        self.assertIsNone(TestChoices.get_key("val0"))
        self.assertEqual(123.45, TestChoices.get_key("val0", 123.45))

        with self.assertRaises(ValueError) as ctx:
            _ = TestChoices["val0"]
        self.assertEqual("value 'val0' is not found in choices class 'TestChoices'", str(ctx.exception))

        self.assertIn("val2", TestChoices.SUBSET1)
        self.assertNotIn("val4", TestChoices.SUBSET1)
        self.assertIn(TestChoices.VAL1, TestChoices.SUBSET1)

    def test_iteration(self):
        self.assertEqual(("VAL1", "VAL2", "VAL3", "VAL4", "VAL5", "VAL6", "VAL7"), TestChoices.keys())
        self.assertEqual(("val1", "val2", "value-3", "val4", "val5", (1, 2, 3), 7), TestChoices.values())
        self.assertEqual(tuple(zip(TestChoices.keys(), TestChoices.values())), TestChoices.items())

        self.assertEqual(
            ("Display 1", "Display 2", "Display 3", "Display 4", "Display 5", "Display 6", "Display 7"),
            TestChoices.displays(),
        )

        self.assertIsInstance(TestChoices, Iterable)
        self.assertEqual(
            (
                ("val1", "Display 1"),
                ("val2", "Display 2"),
                ("value-3", "Display 3"),
                ("val4", "Display 4"),
                ("val5", "Display 5"),
                ((1, 2, 3), "Display 6"),
                (7, "Display 7"),
            ),
            tuple(TestChoices),
        )
        self.assertTrue(callable(TestChoices))
        self.assertEqual(tuple(TestChoices), TestChoices())

        self.assertEqual(
            (
                ("val1", "Display 1"),
                ("val2", "Display 2"),
                ("value-3", "Display 3"),
            ),
            tuple(TestChoices.SUBSET1),
        )
        self.assertTrue(callable(TestChoices.SUBSET1))
        self.assertEqual(tuple(TestChoices.SUBSET1), TestChoices.SUBSET1())

        self.assertEqual(("VAL1", "VAL2", "VAL3"), TestChoices.SUBSET1.keys())
        self.assertEqual(("val1", "val2", "value-3"), TestChoices.SUBSET1.values())
        self.assertEqual(
            tuple(zip(TestChoices.SUBSET1.keys(), TestChoices.SUBSET1.values())),
            TestChoices.SUBSET1.items(),
        )
        self.assertEqual(("Display 1", "Display 2", "Display 3"), TestChoices.SUBSET1.displays())

        self.assertEqual(
            (
                ("val4", "Display 4"),
                ("val5", "Display 5"),
            ),
            TestChoices(strip="Custom"),
        )
        self.assertEqual(("VAL4", "VAL5"), TestChoices.keys(strip="Custom"))
        self.assertEqual(("val4", "val5"), TestChoices.values(strip="Custom"))
        self.assertEqual(
            tuple(zip(TestChoices.keys(strip="Custom"), TestChoices.values(strip="Custom"))),
            TestChoices.items(strip="Custom"),
        )
        self.assertEqual(("Display 4", "Display 5"), TestChoices.displays(strip="Custom"))

        self.assertEqual((), TestChoices.values(strip="Custom", param0="Unknown"))
        self.assertEqual(("val5",), TestChoices.values(strip="Custom", param2="Param 5.2"))

    def test_extract(self):
        choices_extract = TestChoices.extract("VAL2", "VAL5")
        self.assertEqual("TestChoices.Subset", choices_extract.__name__)
        self.assertEqual(("val2", "val5"), choices_extract.values())

        subset_extract = TestChoices.SUBSET1.extract("VAL1", "VAL3", name="EXTRACTED")
        self.assertEqual("TestChoices.SUBSET1.EXTRACTED", subset_extract.__name__)
        self.assertEqual(("val1", "value-3"), subset_extract.values())

    def test_exclude(self):
        choices_exclude = TestChoices.exclude("VAL2", "VAL5")
        self.assertEqual("TestChoices.Subset", choices_exclude.__name__)
        self.assertEqual(("val1", "value-3", "val4", (1, 2, 3), 7), choices_exclude.values())

        subset_exclude = TestChoices.SUBSET1.exclude("VAL1", "VAL3", name="EXCLUDED")
        self.assertEqual("TestChoices.SUBSET1.EXCLUDED", subset_exclude.__name__)
        self.assertEqual(("val2",), subset_exclude.values())

    def test_operations(self):
        union = TestChoices.SUBSET1 | TestChoices.SUBSET2
        self.assertEqual("TestChoices.SUBSET1|TestChoices.SUBSET2", union.__name__)
        self.assertEqual(("VAL1", "VAL2", "VAL3", "VAL5"), union.keys())
        self.assertEqual((TestChoices.VAL1, TestChoices.VAL2, TestChoices.VAL3, TestChoices.VAL5), union.values())

        intersection = TestChoices.SUBSET1 & TestChoices.SUBSET2
        self.assertEqual("TestChoices.SUBSET1&TestChoices.SUBSET2", intersection.__name__)
        self.assertEqual(("VAL3",), intersection.keys())
        self.assertEqual((TestChoices.VAL3,), intersection.values())

        difference = TestChoices.SUBSET1 - TestChoices.SUBSET2
        self.assertEqual("TestChoices.SUBSET1-TestChoices.SUBSET2", difference.__name__)
        self.assertEqual(("VAL1", "VAL2"), difference.keys())
        self.assertEqual((TestChoices.VAL1, TestChoices.VAL2), difference.values())

        symmetric_difference = TestChoices.SUBSET1 ^ TestChoices.SUBSET2
        self.assertEqual("TestChoices.SUBSET1^TestChoices.SUBSET2", symmetric_difference.__name__)
        self.assertEqual(("VAL1", "VAL2", "VAL5"), symmetric_difference.keys())
        self.assertEqual((TestChoices.VAL1, TestChoices.VAL2, TestChoices.VAL5), symmetric_difference.values())

    def test_custom_methods(self):
        self.assertEqual(
            ("DISPLAY 1", "DISPLAY 2", "DISPLAY 3", "DISPLAY 4", "DISPLAY 5", "DISPLAY 6", "DISPLAY 7"),
            TestChoices.get_upper_displays(),
        )
        self.assertEqual(("DISPLAY 3", "DISPLAY 5"), TestChoices.SUBSET2.get_upper_displays())
        self.assertEqual(("DISPLAY 1", "DISPLAY 7"), TestChoices.extract("VAL1", "VAL7").get_upper_displays())

    def test_inheritance(self):
        class TestNextChoices(TestChoices):
            VAL3 = Choices.Value("Display 3", value="val3")
            VAL8 = "Display 8"

        class TestFinalChoices(TestNextChoices):
            VAL9 = "Display 9"
            SUBSET3 = Choices.Subset("VAL2", "VAL8", "VAL9")

        self.assertEqual("Display 1", TestFinalChoices.VAL1.display)
        self.assertEqual("val3", TestFinalChoices.VAL3)
        self.assertEqual("val9", TestFinalChoices.VAL9)
        self.assertEqual(
            ("val1", "val2", "val3", "val4", "val5", (1, 2, 3), 7, "val8", "val9"),
            TestFinalChoices.values(),
        )
        self.assertEqual(("DISPLAY 2", "DISPLAY 8", "DISPLAY 9"), TestFinalChoices.SUBSET3.get_upper_displays())

    def test_copy(self):
        self.assertEqual("val1", copy.copy(TestChoices.VAL1))
        self.assertEqual("value-3", copy.copy(TestChoices.VAL3))
        self.assertEqual("val2", copy.deepcopy(TestChoices.VAL2))
        self.assertEqual((1, 2, 3), copy.deepcopy(TestChoices.VAL6))
        self.assertEqual("Param 6.1", copy.deepcopy(TestChoices.VAL6).param3)

        self.assertIsNot(TestChoices.VAL4, copy.copy(TestChoices.VAL4))
        self.assertIsNot(TestChoices.VAL7, copy.deepcopy(TestChoices.VAL7))

    def test_pickle(self):
        def factory1():
            class Local(Choices):
                VAL = "Display F1"
            return Local

        def factory2():
            class Local(Choices):
                VAL = Choices.Value("Display F2", param=123)
            return Local

        choices1 = factory1()
        val1 = pickle.loads(pickle.dumps(choices1.VAL))
        self.assertEqual("Display F1", val1.display)
        self.assertEqual("TestCase_test_pickle_<locals>_factory1_<locals>_Local_VAL", type(choices1.VAL).__name__)

        choices2 = factory2()
        val2 = pickle.loads(pickle.dumps(choices2.VAL))
        self.assertEqual(123, val2.param)
        self.assertEqual("TestCase_test_pickle_<locals>_factory2_<locals>_Local_VAL", type(choices2.VAL).__name__)

        self.assertIs(type(val1), type(choices1.extract("VAL").VAL))
        self.assertEqual("Display F1", pickle.loads(pickle.dumps(choices1.VAL)).display)

        self.assertEqual([*TestChoices], pickle.loads(pickle.dumps([*TestChoices])))

    def test_json(self):
        self.assertEqual('"value-3"', json.dumps(TestChoices.VAL3))
        self.assertEqual(
            '[["val1", "Display 1"], ["val2", "Display 2"], ["value-3", "Display 3"], '
            '["val4", "Display 4"], ["val5", "Display 5"], [[1, 2, 3], "Display 6"], [7, "Display 7"]]',
            json.dumps([*TestChoices]),
        )


if __name__ == "__main__":
    unittest.main()
