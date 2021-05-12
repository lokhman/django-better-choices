import copy
import json
import pickle
import unittest

from collections.abc import Iterable

from django_better_choices import Choices, Value, choices


@choices
class TestChoices:
    # values
    VAL1 = "Display 1"
    VAL2 = choices.value("Display 2")
    VAL3 = choices.value("Display 3", value="value-3")
    VAL4 = choices.value("Display 4", param1="Param 4.1", strip="Custom")
    VAL5 = choices.value("Display 5", param1="Param 5.1", param2="Param 5.2", strip="Custom")
    VAL6 = choices.value("Display 6", value=(1, 2, 3), param3="Param 6.1")
    VAL7 = choices.value("Display 7", value=7)

    # subsets
    SUBSET1 = choices.subset("VAL1", "VAL2", "VAL3")
    SUBSET2 = choices.subset("VAL3", "VAL5")

    # arbitrary data
    DATA1 = 123.45
    data2 = [1, 2, 3]

    # nested choices
    @choices
    class Nested:
        VAL10 = "Display 10"
        VAL20 = "Display 20"

    def get_upper_displays(self):
        return tuple(map(str.upper, self.displays()))


class TestCase(unittest.TestCase):
    def test_init(self):
        local = choices.new(
            VAL1="Display 1",
            VAL2=choices.value("Display 2"),
            SUBSET=choices.subset("VAL1", "VAL2", "VAL1"),
        )

        self.assertEqual("TestChoices", TestChoices.__class__.__name__)
        self.assertEqual("CONST_NAME", choices.new("CONST_NAME").__class__.__name__)
        self.assertEqual("TestChoices.SUBSET1", TestChoices.SUBSET1.__class__.__name__)
        self.assertEqual("Choices", local.__class__.__name__)

        self.assertEqual("Choices(VAL1, VAL2)", str(local))
        self.assertEqual("Choices('Choices', VAL1='val1', VAL2='val2')", repr(local))
        self.assertEqual("Choices.SUBSET(VAL1, VAL2)", str(local.SUBSET))
        self.assertEqual("Choices('TEST')", repr(choices.new("TEST")))

        self.assertEqual("val1", local.VAL1)
        self.assertEqual("val2", str(local.VAL2))

        self.assertEqual(local.VAL1, str(local.VAL1))
        self.assertEqual(local.VAL1, TestChoices.VAL1)

        self.assertEqual(123.45, TestChoices.DATA1)
        self.assertEqual([1, 2, 3], TestChoices.data2)

        with self.assertRaises(ValueError) as ctx:  # duplicated value
            choices.new(VAL1="Display 1", VAL2=choices.value("Display 2", value="val1"))

        self.assertEqual(
            "choices class 'Choices' has a duplicated value 'val1' for attribute 'VAL2'",
            str(ctx.exception)
        )

        with self.assertRaises(AttributeError) as ctx:  # invalid subset key
            @choices
            class _:
                VAL1 = "Display 1"
                SUBSET1 = choices.subset(VAL1)

        self.assertEqual("'_' object has no attribute 'Display 1'", str(ctx.exception))

        with self.assertRaises(TypeError) as ctx:  # invalid value type
            choices.new(VAL=choices.value("Display", value=True))
        self.assertEqual("type 'bool' is not acceptable for choices class value 'Choices.VAL'", str(ctx.exception))

    def test_accessors(self):
        for type_ in (Value, str):
            self.assertIsInstance(TestChoices.VAL1, type_)
            self.assertIsInstance(TestChoices.Nested.VAL10, type_)

        for type_ in (Value, tuple):
            self.assertIsInstance(TestChoices.VAL6, type_)

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
        self.assertEqual("'TestChoices' object has no attribute 'VAL0'", str(ctx.exception))

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

        self.assertIsInstance(TestChoices.get("val2"), Value)
        self.assertEqual("val2", TestChoices.get(TestChoices.VAL2))
        self.assertEqual("Display 2", TestChoices.get("val2").display)
        self.assertIs(TestChoices.get("val2"), TestChoices["val2"])

        self.assertIsNone(TestChoices.get("val0"))
        self.assertEqual(123.45, TestChoices.get("val0", 123.45))

        with self.assertRaises(KeyError) as ctx:
            _ = TestChoices["val0"]
        self.assertEqual("'val0'", str(ctx.exception))

        self.assertIn("val2", TestChoices.SUBSET1)
        self.assertNotIn("val4", TestChoices.SUBSET1)
        self.assertIn(TestChoices.VAL1, TestChoices.SUBSET1)

    def test_iteration(self):
        self.assertEqual(("val1", "val2", "value-3", "val4", "val5", (1, 2, 3), 7), TestChoices.keys())
        self.assertEqual(("val1", "val2", "value-3", "val4", "val5", (1, 2, 3), 7), TestChoices.values())
        self.assertIsNot(TestChoices.keys(), TestChoices.values())
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
            TestChoices.choices(),
        )

        self.assertEqual(
            (
                ("val1", "Display 1"),
                ("val2", "Display 2"),
                ("value-3", "Display 3"),
            ),
            TestChoices.SUBSET1.choices(),
        )

        self.assertEqual(("val1", "val2", "value-3"), TestChoices.SUBSET1.keys())
        self.assertEqual(("val1", "val2", "value-3"), TestChoices.SUBSET1.values())
        self.assertEqual(
            tuple(zip(TestChoices.SUBSET1.keys(), TestChoices.SUBSET1.values())),
            TestChoices.SUBSET1.items(),
        )
        self.assertEqual(("Display 1", "Display 2", "Display 3"), TestChoices.SUBSET1.displays())

    def test_extract(self):
        choices_extract = TestChoices.extract("VAL2", "VAL5")
        self.assertEqual("TestChoices.Subset", choices_extract.__class__.__name__)
        self.assertEqual(("val2", "val5"), choices_extract.values())

        subset_extract = TestChoices.SUBSET1.extract("VAL1", "VAL3", name="EXTRACTED")
        self.assertEqual("TestChoices.SUBSET1.EXTRACTED", subset_extract.__class__.__name__)
        self.assertEqual(("val1", "value-3"), subset_extract.values())

    def test_exclude(self):
        choices_exclude = TestChoices.exclude("VAL2", "VAL5")
        self.assertEqual("TestChoices.Subset", choices_exclude.__class__.__name__)
        self.assertEqual(("val1", "value-3", "val4", (1, 2, 3), 7), choices_exclude.values())

        subset_exclude = TestChoices.SUBSET1.exclude("VAL1", "VAL3", name="EXCLUDED")
        self.assertEqual("TestChoices.SUBSET1.EXCLUDED", subset_exclude.__class__.__name__)
        self.assertEqual(("val2",), subset_exclude.values())

    def test_operations(self):
        union = TestChoices.SUBSET1 | TestChoices.SUBSET2
        self.assertEqual("<TestChoices.SUBSET1|TestChoices.SUBSET2>", union.__class__.__name__)
        self.assertEqual(("val1", "val2", "value-3", "val5"), union.keys())
        self.assertEqual((TestChoices.VAL1, TestChoices.VAL2, TestChoices.VAL3, TestChoices.VAL5), union.values())

        intersection = TestChoices.SUBSET1 & TestChoices.SUBSET2
        self.assertEqual("<TestChoices.SUBSET1&TestChoices.SUBSET2>", intersection.__class__.__name__)
        self.assertEqual(("value-3",), intersection.keys())
        self.assertEqual((TestChoices.VAL3,), intersection.values())

        difference = TestChoices.SUBSET1 - TestChoices.SUBSET2
        self.assertEqual("<TestChoices.SUBSET1-TestChoices.SUBSET2>", difference.__class__.__name__)
        self.assertEqual(("val1", "val2"), difference.keys())
        self.assertEqual((TestChoices.VAL1, TestChoices.VAL2), difference.values())

        symmetric_difference = TestChoices.SUBSET1 ^ TestChoices.SUBSET2
        self.assertEqual("<TestChoices.SUBSET1^TestChoices.SUBSET2>", symmetric_difference.__class__.__name__)
        self.assertEqual(("val1", "val2", "val5"), symmetric_difference.keys())
        self.assertEqual((TestChoices.VAL1, TestChoices.VAL2, TestChoices.VAL5), symmetric_difference.values())

    def test_custom_methods(self):
        self.assertEqual(
            ("DISPLAY 1", "DISPLAY 2", "DISPLAY 3", "DISPLAY 4", "DISPLAY 5", "DISPLAY 6", "DISPLAY 7"),
            TestChoices.get_upper_displays(),
        )
        self.assertEqual(("DISPLAY 3", "DISPLAY 5"), TestChoices.SUBSET2.get_upper_displays())
        self.assertEqual(("DISPLAY 1", "DISPLAY 7"), TestChoices.extract("VAL1", "VAL7").get_upper_displays())

    def test_inheritance(self):
        @choices
        class TestNextChoices(TestChoices):
            VAL3 = choices.value("Display 3", value="val3")
            VAL8 = "Display 8"

        @choices
        class TestFinalChoices(TestNextChoices):
            VAL9 = "Display 9"
            SUBSET3 = choices.subset("VAL2", "VAL8", "VAL9")

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
            @choices
            class Local:
                VAL = "Display F1"
            return Local

        def factory2():
            @choices
            class Local:
                VAL = choices.value("Display F2", param=123)
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
            json.dumps([*TestChoices.choices()]),
        )


if __name__ == "__main__":
    unittest.main()
