import datajoint as dj
from operator import mul
from functools import reduce
from .context import foreigns
from .utils import class_property, key_hash, user_choice, to_camel_case
from .errors import MissingError
from .logging import logger


def master_definition(name, comment, length):
    return """
    {name}_id                       : char({length})    # {comment}
    ---
    members                         : int unsigned      # number of members
    {name}_ts = CURRENT_TIMESTAMP   : timestamp         # automatic timestamp
    """.format(
        name=name,
        length=length,
        comment=comment,
    )


def part_definition(foriegn_keys):
    return """
    -> master
    {foriegn_keys}
    """.format(
        foriegn_keys="\n    ".join([f"-> {f}" for f in foriegn_keys]),
    )


note_definition = """
    -> master
    note                            : varchar(1024)     # note for set
    ---
    note_ts = CURRENT_TIMESTAMP     : timestamp         # automatic timestamp
    """


class Set:
    @class_property
    def key_source(cls):
        return reduce(mul, [key.proj() for key in cls.keys])

    @class_property
    def member_key(cls):
        return cls.key_source.primary_key

    @class_property
    def order(cls):
        return [f"{key} ASC" for key in cls.member_key]

    @property
    def members(self):
        """
        Returns
        -------
        Set.Part
            tuples that comprise the set
        """
        key, n = self.fetch1(dj.key, "members")
        members = getattr(self, self._part) & key

        if len(members) == n:
            return members
        else:
            raise MissingError("Members are missing.")

    @property
    def ordered_keys(self):
        """
        Returns
        -------
        list[dict]
            ordered tuples that comprise the set
        """
        return self.members.fetch(*self.member_key, as_dict=True, order_by=self.order)

    @classmethod
    def fill(cls, restriction, note=None, *, prompt=True, silent=False):
        """Creates a hash for the restricted tuples, and inserts into master, member, and note tables

        Parameters
        ----------
        restriction : datajoint restriction
            used to restrict key_source
        note : str | None
            note to attach to the tuple set

        Returns
        -------
        dict | None
            set key
        """
        Part = getattr(cls, cls._part)

        keys = cls.key_source.restrict(restriction)
        keys = keys.fetch(as_dict=True, order_by=cls.order)
        n = len(keys)

        key = dict([[i, key_hash(k)] for i, k in enumerate(keys)])
        key = {f"{cls.name}_id": key_hash(key)}

        if cls & key:
            assert (cls & key).fetch1("members") == len(Part & key)

            if not silent:
                logger.info(f"{key} already exists.")

        elif not prompt or user_choice(f"Insert set with {n} keys?") == "yes":

            cls.insert1(dict(key, members=n))
            Part.insert([dict(**key, **k) for k in keys])

            if not silent:
                logger.info(f"{key} inserted.")

        else:
            if not silent:
                logger.info(f"{key} not inserted.")

            return

        if note:
            if not silent:
                logger.info(f"Note for {key} inserted.")

            cls.Note.insert1(dict(key, note=note), skip_duplicates=True)

        return key

    @classmethod
    def get(cls, restriction):
        """
        Parameters
        ----------
        restriction : datajoint restriction
            used to restrict key_source

        Returns
        -------
        Set
            tuple that matches restriction
        """
        key = cls.key_source & restriction
        n = len(key)

        candidates = cls & f"members = {n}"
        members = getattr(cls, cls._part) & key
        key = candidates.aggr(members, n="count(*)") & f"n = {n}"

        if key:
            return cls & key.fetch1(dj.key)
        else:
            raise MissingError("Set does not exist.")


def setup_set(cls, schema):

    keys = tuple(cls.keys)
    name = str(cls.name)
    comment = str(cls.comment)
    part_name = str(cls.part_name)

    assert name != part_name

    length = int(getattr(cls, "length", 32))
    length = max(0, min(length, 32))

    foriegn_keys, context = foreigns(keys, schema)

    Note = type("Note", (dj.Part,), {"definition": note_definition})

    part = to_camel_case(part_name)
    Part = type(part, (dj.Part,), {"definition": part_definition(foriegn_keys)})

    attr = {
        "definition": master_definition(name, comment, length),
        "keys": keys,
        "name": name,
        "comment": comment,
        "part_name": part_name,
        "length": length,
        "Note": Note,
        "_part": part,
        part: Part,
    }
    cls = type(cls.__name__, (Set, cls, dj.Lookup), attr)
    cls = schema(cls, context=context)
    return cls
