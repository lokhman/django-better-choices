import pytest

from django_better_choices import Choices


class TestChoices(Choices):
    __test__ = False

    VAL1 = "Display 1"
    VAL2 = Choices.Value("Display 2")
    VAL3 = Choices.Value("Display 3", value="value-3")
    VAL4 = Choices.Value("Display 4", param1="Param 4.1", strip="Custom")
    VAL5 = Choices.Value("Display 5", param1="Param 5.1", param2="Param 5.2", strip="Custom")
    VAL6 = Choices.Value("Display 6", value=True, param1="Param 6.1")
    VAL7 = Choices.Value("Display 7", value=7)

    SUBSET1 = Choices.Subset("VAL1", "VAL2", "VAL3")
    SUBSET2 = Choices.Subset("VAL3", "VAL5")
    SUBSET3 = Choices.Subset(*SUBSET1, *SUBSET2)

    @classmethod
    def displays(cls):
        return [choice.display for choice in cls]

    def display_upper(self):
        return self.display.upper()


@pytest.mark.parametrize(
    ("name", "value", "display", "kwargs"),
    [
        ("VAL1", "val1", "Display 1", {}),
        ("VAL2", "val2", "Display 2", {}),
        ("VAL3", "value-3", "Display 3", {}),
        ("VAL4", "val4", "Display 4", {"param1": "Param 4.1", "strip": "Custom"}),
        ("VAL5", "val5", "Display 5", {"param1": "Param 5.1", "param2": "Param 5.2", "strip": "Custom"}),
        ("VAL6", True, "Display 6", {"param1": "Param 6.1"}),
        ("VAL7", 7, "Display 7", {}),
    ],
)
def test_values(name, value, display, kwargs):
    choice = getattr(TestChoices, name)
    assert choice.value == value
    assert choice.display == display
    assert type(value)(choice) == value
    for k, v in kwargs.items():
        assert getattr(choice, k) == v
    assert TestChoices(value) is choice
    assert choice in TestChoices
    assert value in TestChoices


@pytest.mark.parametrize(
    ("name", "values"),
    [
        ("SUBSET1", ["VAL1", "VAL2", "VAL3"]),
        ("SUBSET2", ["VAL3", "VAL5"]),
        ("SUBSET3", ["VAL1", "VAL2", "VAL3", "VAL5"]),
    ],
)
def test_subsets(name, values):
    choice = getattr(TestChoices, name)
    assert list(choice) == [getattr(TestChoices, name) for name in values]


def test_choices():
    assert TestChoices.choices() == [
        ("val1", "Display 1"),
        ("val2", "Display 2"),
        ("value-3", "Display 3"),
        ("val4", "Display 4"),
        ("val5", "Display 5"),
        (True, "Display 6"),
        (7, "Display 7"),
    ]
    assert TestChoices.SUBSET1.choices() == [
        ("val1", "Display 1"),
        ("val2", "Display 2"),
        ("value-3", "Display 3"),
    ]
    assert TestChoices.extract("VAL1", "VAL2").choices() == [
        ("val1", "Display 1"),
        ("val2", "Display 2"),
    ]


def test_extraction():
    extracted1 = TestChoices.extract("VAL1", "VAL2", "VAL6", class_name="ExtractedSubset")
    assert list(extracted1) == [TestChoices.VAL1, TestChoices.VAL2, TestChoices.VAL6]
    assert repr(extracted1) == "<choices 'ExtractedSubset'>"
    assert extracted1.VAL6.value is True
    assert extracted1.VAL6.display == "Display 6"
    assert extracted1.VAL6.param1 == "Param 6.1"

    excluded1 = TestChoices.exclude("VAL3", "VAL4", "VAL5", "VAL7", class_name="ExcludedSubset")
    assert list(excluded1) == list(extracted1)
    assert repr(excluded1) == "<choices 'ExcludedSubset'>"

    extracted2 = TestChoices.SUBSET2.extract("VAL5")
    assert list(extracted2) == [TestChoices.VAL5]
    assert repr(extracted2) == "<choices 'TestChoices.SUBSET2.Subset'>"
    assert extracted2.VAL5.value == "val5"
    assert extracted2.VAL5.display == "Display 5"
    assert extracted2.VAL5.param1 == "Param 5.1"

    excluded2 = TestChoices.SUBSET2.exclude("VAL3")
    assert list(excluded2) == list(extracted2)
    assert repr(excluded2) == "<choices 'TestChoices.SUBSET2.Subset'>"

    extracted3 = extracted1.extract("VAL6")
    assert list(extracted3) == [TestChoices.VAL6]
    assert repr(extracted3) == "<choices 'ExtractedSubset.Subset'>"
    assert extracted3.VAL6.value is True
    assert extracted3.VAL6.display == "Display 6"
    assert extracted3.VAL6.param1 == "Param 6.1"

    excluded3 = excluded1.exclude("VAL1", "VAL2")
    assert list(excluded3) == list(extracted3)
    assert repr(excluded3) == "<choices 'ExcludedSubset.Subset'>"

    extracted4 = TestChoices.extract(TestChoices.VAL4, TestChoices.SUBSET2, "VAL6")
    assert list(extracted4) == [TestChoices.VAL4, TestChoices.VAL3, TestChoices.VAL5, TestChoices.VAL6]

    excluded4 = extracted4.exclude(TestChoices.VAL4, TestChoices.SUBSET2)
    assert list(excluded4) == [TestChoices.VAL6]


def test_extras():
    assert TestChoices.displays() == [
        "Display 1",
        "Display 2",
        "Display 3",
        "Display 4",
        "Display 5",
        "Display 6",
        "Display 7",
    ]
    assert TestChoices.SUBSET1.displays() == [
        "Display 1",
        "Display 2",
        "Display 3",
    ]
    assert TestChoices.extract("VAL1").displays() == [
        "Display 1",
    ]
    assert TestChoices.exclude("VAL1", "VAL2", "VAL3", "VAL4", "VAL5", "VAL6").displays() == [
        "Display 7",
    ]

    assert TestChoices.VAL1.display_upper() == "DISPLAY 1"
    assert TestChoices.SUBSET1.VAL2.display_upper() == "DISPLAY 2"
    assert TestChoices.extract("VAL3").VAL3.display_upper() == "DISPLAY 3"
    assert TestChoices.exclude("VAL3").VAL4.display_upper() == "DISPLAY 4"


def test_errors():
    with pytest.raises(TypeError, match=r"Unexpected type 'int' for choices: BadChoices.VAL"):
        _ = Choices("BadChoices", {"VAL": 1})

    with pytest.raises(AttributeError, match=r"'TestChoices.VAL1' object has no attribute 'unknown'"):
        _ = TestChoices.VAL1.unknown
