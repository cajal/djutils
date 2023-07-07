# djutils

`djutils` provides helpfus tools for creating `datajoint` pipelines.


## Install

```
pip3 install git+https://github.com/cajal/djutils.git
```

## Getting Started

Standard `lookup`, and `computed` datajoint tables can be created as follows:

```python
from djutils import Schema

schema = Schema(...)

@schema.lookup
class ExampleLookup:
    definition = """
    ...
    """

@schema.computed
class ExampleComputed:
    definition = """
    ...
    """
```

In addition, `djutils` provides table designs that are useful for creating composable and row-oriented pipelines that depend on abstractions, not concretions.

```python
@schema.link
class Abstract:
    links = [ConcreteTableA, ConcreteTableB, ...]
    name = "abstract"


@schema.set
class RowSet:
    keys = [TableA, TableB, ...]
    name = "rowset"


@schema.list
class RowSet:
    keys = [TableA, TableB, ...]
    name = "rowlist"
```

... and many more.
