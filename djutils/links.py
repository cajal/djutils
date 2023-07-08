import datajoint as dj
from .resolve import foreigns
from .utils import key_hash
from .sets import setup_set
from .lists import setup_list
from .logging import logger
from .errors import MissingError


def master_definition(name, comment, length):
    return """
    {name}_id                       : char({length})    # {comment}
    ---
    {name}_type                     : varchar(128)      # {name} type
    {name}_ts = CURRENT_TIMESTAMP   : timestamp         # automatic timestamp
    """.format(
        name=name,
        length=length,
        comment=comment,
    )


def part_definition(foreign):
    return """
    -> master
    ---
    -> {foreign}
    """.format(
        foreign=foreign,
    )


class Link(dj.Lookup):
    @classmethod
    def fill(cls):
        """Inserts tuples into self and part tables"""
        for table in cls.tables:
            getattr(cls, table).fill()

    @classmethod
    def clean(cls):
        """Deletes tuples from self that are missing in links"""
        keys = []
        for table in cls.tables:
            keys += getattr(cls, table).fetch(dj.key)

        (cls - keys).delete()

    @property
    def link(self):
        """Restricted linked table

        IMPORTANT: must be restricted to a single row
        """
        link_type = self.fetch1(f"{self.name}_type")
        part = getattr(self, link_type) & self
        return part.link

    @classmethod
    def query(cls, link_type, link_key=None):
        """
        Parameters
        ----------
        link_type : str
            link type
        link_key : datajoint restriction | None
            link key, optional

        Returns
        -------
        dj.Lookup
            link table restricted by link type, and optionally restricted by link key
        """
        _link_type = f"{cls.name}_type"
        keys = cls & {_link_type: link_type}
        if not keys:
            raise MissingError("Link type does not exist.")

        part = getattr(cls, link_type)
        links = part * part._link if link_key is None else part * part._link & link_key
        if not links:
            raise MissingError("No links found.")

        return keys & links


class Part(dj.Part):
    @classmethod
    def fill(cls):
        """
        Inserts tuples into self and the master table
        """
        keys = (cls._link - cls).fetch(dj.key)

        if keys:
            logger.info(f"{cls.__name__} -- Inserting {len(keys)} keys")

            master = cls.master
            name = master.name
            length = master.length

            cls_type = {f"{name}_type": cls.__name__}
            hashes = [key_hash(dict(k, **cls_type)) for k in keys]
            hashes = [{f"{name}_id": p[:length]} for p in hashes]

            master.insert(
                [dict(**h, **cls_type) for h in hashes],
                skip_duplicates=True,
            )
            cls.insert(
                [dict(**h, **k) for h, k in zip(hashes, keys)],
                skip_duplicates=True,
            )

        else:
            logger.info(f"{cls.__name__} -- No new keys to insert")

    @property
    def link(self):
        """Returns the restricted linked table"""
        return self._link & self


def setup_link(cls, schema):

    length = int(getattr(cls, "length", 32))
    length = max(0, min(length, 32))

    master_attr = dict(
        definition=master_definition(cls.name, getattr(cls, "comment", cls.name), length),
        length=length,
    )

    keys, context = foreigns(cls.links, schema)

    tables = []
    parts = []

    for key, link in zip(keys, cls.links):

        tables.append(link.__name__)

        part = key.split(".")[-1]
        assert part not in parts

        part_attr = dict(
            definition=part_definition(key),
            _link=link,
        )
        master_attr[part] = type(part, (Part,), part_attr)

    master_attr["tables"] = tables

    cls = type(cls.__name__, (cls, Link), master_attr)
    cls = schema(cls, context=context)
    return cls


def setup_link_set(cls, schema):

    if not issubclass(cls.link, Link):
        raise TypeError("Provided link is not a subclass of Link.")

    cls.keys = [cls.link]

    return setup_set(cls, schema)


def setup_link_list(cls, schema):

    if not issubclass(cls.link, Link):
        raise TypeError("Provided link is not a subclass of Link.")

    cls.keys = [cls.link]

    return setup_list(cls, schema)
