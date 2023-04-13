import datajoint as dj
from datajoint.hash import key_hash
from datajoint.utils import to_camel_case
import inspect
from .logging import logger


def master_definition(name, comment, length):
    return """
    {name}_id                       : varchar({length}) # {comment}
    ---
    {name}_type                     : varchar(128)      # {name} type
    {name}_ts = CURRENT_TIMESTAMP   : timestamp         # automatic timestamp
    """.format(
        name=name,
        length=length,
        comment=comment,
    )


def part_definition(database, table):
    return """
    -> master
    ---
    -> {database}.{table}
    """.format(
        database=database,
        table=table,
    )


class Master(dj.Lookup):
    @classmethod
    def fill(cls):
        """Inserts tuples into self and the part tables"""
        for table in cls.tables:
            getattr(cls, table).fill()

    @classmethod
    def clean(cls):
        """Deletes keys from self that are missing in links"""
        keys = []
        for table in cls.tables:
            keys += getattr(cls, table).fetch(dj.key)

        (cls - keys).delete()

    @property
    def part(self):
        """Returns the part table restricted by tuples

        IMPORTANT: tuples must be restricted to a single type
        """
        link_type = f"{self.name}_type"
        link_type = (dj.U(link_type) & self).fetch1(link_type)
        return getattr(self, link_type) & self

    @property
    def link(self):
        """Returns the linked table restricted by tuples

        IMPORTANT: tuples must be restricted to a single type
        """
        return self.part.link


class Part(dj.Part):
    @classmethod
    def fill(cls):
        """
        Inserts tuples into self and the master table
        """
        keys = (cls._link - cls).fetch(dj.key)

        if keys:
            logger.info(f"{cls.__name__} -- Inserting {len(keys)} keys")

            name = cls.master.name
            length = cls.master.length

            primary = f"{name}_id"
            secondary = {f"{name}_type": cls.__name__}

            primary_keys = [key_hash(dict(key, **secondary)) for key in keys]
            primary_keys = [{primary: key[:length]} for key in primary_keys]

            master_keys = [dict(**pk, **secondary) for pk in primary_keys]
            part_keys = [dict(**pk, **key) for pk, key in zip(primary_keys, keys)]

            cls.master.insert(master_keys, skip_duplicates=True)
            cls.insert(part_keys)

        else:
            logger.info(f"{cls.__name__} -- No new keys to insert")

    @property
    def link(self):
        """Returns the linked table restricted by tuples"""
        return self._link & self


def link(schema):

    if schema.context is None:
        context = inspect.currentframe().f_back.f_locals
    else:
        context = schema.context

    def decorate(cls):
        cls = setup(cls, dict(context))
        cls = schema(cls, context=context)
        return cls

    return decorate


def setup(cls, context):

    links = tuple(cls.links)
    databases = tuple(link.database for link in links)
    tables = tuple(link.__name__ for link in links)

    name = str(cls.name)
    comment = str(cls.comment)
    length = int(getattr(cls, "length", 32))
    length = max(0, min(length, 32))

    master_attr = dict(
        definition=master_definition(name, comment, length),
        links=links,
        databases=databases,
        tables=tables,
        name=name,
        comment=comment,
        length=length,
    )

    for link, database, table in zip(links, databases, tables):

        if database not in context:
            context[database] = dj.create_virtual_module(database, database)

        part_attr = dict(
            definition=part_definition(database, table),
            _link=link,
        )
        master_attr[table] = type(table, (Part,), part_attr)

    cls = type(cls.__name__, (Master,), master_attr)
    return cls
