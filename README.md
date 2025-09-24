# Django Better Choices

[![PyPI](https://img.shields.io/pypi/v/django-better-choices)](https://pypi.org/project/django-better-choices)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-better-choices)
[![Build Status](https://img.shields.io/github/actions/workflow/status/lokhman/django-better-choices/ci.yml?branch=master)](https://github.com/lokhman/django-better-choices/actions?query=workflow%3ACI)
[![codecov](https://codecov.io/gh/lokhman/django-better-choices/branch/master/graph/badge.svg)](https://codecov.io/gh/lokhman/django-better-choices)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Better [choices](https://docs.djangoproject.com/en/3.0/ref/models/fields/#choices) library for Django web framework.

Define your choices once, get:

- **String values** (for DB compatibility) + **rich attributes** (for app logic).
- **Pretty display labels** (lazy-translatable).
- **Typed access** via enum members.
- **Subsets** (extract/exclude) for forms/admin or feature flags.
- **Django-friendly**: `ModelField(choices=..., default=...)`.

## Requirements
This library was written for Python 3.9+ and may not work in any earlier versions.

## Installation
```bash
pip install django-better-choices
# or with uv
uv add django-better-choices
```

## Quick start
```python
from django_better_choices import Choices

class Status(Choices):
    # simplest: display only — value is auto-generated as lowercase("name")
    DRAFT = "Draft"

    # explicit wrapper — value auto-generated later
    OPEN = Choices.Value("Open")

    # fully explicit
    CLOSED = Choices.Value("Closed", value="closed-hard", css="badge--red")

    # attach arbitrary params to a choice (become attributes)
    PENDING = Choices.Value("Pending review", level=2, css="badge--yellow")

    # subsets (reusable groups of members)
    PUBLIC = Choices.Subset("OPEN", "CLOSED")

# Use like enum + str
Status.OPEN.value              # "open"
Status.OPEN.display            # "Open"
Status.PENDING.level           # 2
str(Status.OPEN)               # "open"
Status("open") is Status.OPEN  # True
"open" in Status               # True

# For Django model fields:
# choices=Status.choices()  -> [("draft", "Draft"), ("open", "Open"), ...]
```

## Why this instead of plain Enum or Django tuples?
- **Single source of truth:** define once, get both the **DB value** (string/bool/int) and the **human label**.
- **Attributes per choice:** attach metadata (`css`, `level`, ...) right on the member.
- **Subsets:** build narrow groups (`PUBLIC`, `INTERNAL`, ...) or compose at runtime (`extract`, `exclude`).
- **Typed access:** members are enum-like and `str`-like, so they fit Django fields and your logic.


## Usage
### Defining values & parameters
#### 1) Implicit values (default)

If you pass a string, it’s treated as **display**. The stored **value** is the lower-cased member name.
```python
class Example(Choices):
    FOO = "Foo"
    BAR = "Bar"

Example.FOO.value    # "foo"
Example.FOO.display  # "Foo"
```

#### 2) Choices.Value(display, *, value=_auto, **params)
- `display`: what users see (may be lazy `_("Text")`).
- `value`: hashable value (string/bool/int). By default, auto-generated from the **member name**.
- `params`: any extra attributes you want to access later.

```python
class Example(Choices):
    A = Choices.Value("Alpha", slug="alpha", css="badge")
    B = Choices.Value("Beta", value=True, risk=5)
    C = Choices.Value("Gamma", value=7)

Example.A.slug   # "alpha"
Example.B.value  # True
Example.C.value  # 7
```

#### 3) Custom value factory (optional)
Override `_choices_value_factory_` to control auto values.
```python
class Example(Choices):
    _choices_value_factory_ = staticmethod(lambda name, **_: name.upper())

    ALPHA = "Alpha"

Example.ALPHA.value  # "ALPHA"
```

### Subsets

Create **named** subsets on the class:
```python
class Status(Choices):
    OPEN = "Open"
    CLOSED = "Closed"
    ARCHIVED = "Archived"

    ACTIVE = Choices.Subset("OPEN", "CLOSED")
```

Or **ad-hoc** at runtime:
```python
Status.extract("OPEN", "CLOSED")   # -> new Choices subclass "Status.Subset"
Status.exclude("ARCHIVED")         # -> everything but ARCHIVED
```

Subsets are full `Choices` classes themselves:
```python
subset = Status.ACTIVE
list(subset)            # [Status.OPEN, Status.CLOSED]
subset.choices()        # [("open", "Open"), ("closed", "Closed")]
repr(subset)            # "<choices 'Status.ACTIVE'>"
```

### Django integration
#### Model fields
```python
from django.db import models

class Ticket(models.Model):
    class Status(Choices):
        OPEN = "Open"
        CLOSED = Choices.Value("Closed", css="badge--red")

    status = models.CharField(
        max_length=20,
        choices=Status.choices(),
        default=Status.OPEN,   # can pass the member (stores its .value)
    )
```

#### Forms/admin
```python
from django import forms

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["status"]
        widgets = {
            "status": forms.Select(choices=Ticket.Status.ACTIVE.choices())
        }
```

#### i18n (optional)
```python
from django.utils.translation import gettext_lazy as _

class Color(Choices):
    RED = _("Red")
    GREEN = Choices.Value(_("Green"), css="green")
```
`display` accepts Django’s lazy `Promise`, so translation resolves at render time.

## Type hints
- The package ships with type annotations.
- Members are both Enum and `str` (subclass), so tools like mypy/pyright see them as string-like values with extra attributes.

## Testing
```bash
uv sync --dev
uv run pytest -q
```
With coverage 100% enforced:
```bash
uv run pytest --cov
```

## Contributing
- Issues and PRs welcome.
- Please run `ruff check . --fix` and keep tests green with 100% coverage.

## License
Library is available under the MIT license. The included LICENSE file describes this in detail.
