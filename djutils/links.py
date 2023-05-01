import datajoint as dj
from datajoint.hash import key_hash
from .context import foreigns
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


class Master:
    @classmethod
    def fill(cls):
        """Inserts tuples into self and part tables"""
        for table in cls._tables:
            getattr(cls, table).fill()

    @classmethod
    def clean(cls):
        """Deletes tuples from self that are missing in links"""
        keys = []
        for table in cls._tables:
            keys += getattr(cls, table).fetch(dj.key)

        (cls - keys).delete()

    @property
    def links(self):
        """Restricted linked tables"""
        link_type = f"{self.name}_type"
        types = (dj.U(link_type) & self).fetch(link_type)
        parts = (getattr(self, t) & self for t in types)
        return tuple(part.link for part in parts)

    @property
    def link(self):
        """Restricted linked table

        IMPORTANT: tuples must be restricted to a single type
        """
        links = self.links

        if len(links) != 1:
            raise ValueError("Must restrict to exactly one link type.")

        return links[0]

    @classmethod
    def get(cls, link_type, link_key=None):
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

    def filter(self, restriction):
        """Filters tuples by link restriction

        Parameters
        ----------
        restriction : datajoint restriction
            used to restrict links

        Returns
        -------
        dj.Lookup
            restricted tuples
        """
        return self & [l.restrict(restriction) for l in self.links]


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
            )

        else:
            logger.info(f"{cls.__name__} -- No new keys to insert")

    @property
    def link(self):
        """Returns the linked table restricted by tuples"""
        return self._link & self


def setup_link(cls, schema):

    name = str(cls.name)
    comment = str(cls.comment)
    links = tuple(cls.links)
    tables = tuple(link.__name__ for link in links)
    length = int(getattr(cls, "length", 32))
    length = max(0, min(length, 32))

    master_attr = dict(
        definition=master_definition(name, comment, length),
        name=name,
        comment=comment,
        length=length,
        _links=links,
        _tables=tables,
    )

    keys, context = foreigns(links, schema)
    parts = []

    for key, _link in zip(keys, links):

        part = key.split(".")[-1]
        assert part not in parts

        part_attr = dict(
            definition=part_definition(key),
            _link=_link,
        )
        master_attr[part] = type(part, (Part,), part_attr)

    cls = type(cls.__name__, (Master, cls, dj.Lookup), master_attr)
    cls = schema(cls, context=context)
    return cls
