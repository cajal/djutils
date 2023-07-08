# djutils

`djutils` provides helpful tools for creating `datajoint` pipelines.


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

    def make(self, key):
        ...
```

In addition, `djutils` provides table designs that are useful for creating composable and row-oriented pipelines that depend on abstractions, not concretions.

```python
@schema.link
class Abstract:
    links = [ConcreteTableA, ConcreteTableB, ...]
    name = "abstract"


@schema.set
class ExampleSet:
    keys = [TableA, TableB, ...]
    name = "exampleset"


@schema.list
class ExampleList:
    keys = [TableA, TableB, ...]
    name = "examplelist"
```

... and much more.
