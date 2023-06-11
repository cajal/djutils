import datajoint as dj
from operator import mul
from functools import reduce
from .resolve import foreigns
from .utils import classproperty, key_hash, user_choice, to_camel_case
from .rows import rowproperty
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


def part_definition(foriegn_keys, name):
    return """
    -> master
    {foriegn_keys}
    ---
    {name}_index                    : int unsigned      # set index
    """.format(
        foriegn_keys="\n    ".join([f"-> {f}" for f in foriegn_keys]),
        name=name,
    )


note_definition = """
    -> master
    note                            : varchar(1024)     # note for set
    ---
    note_ts = CURRENT_TIMESTAMP     : timestamp         # automatic timestamp
    """


class Set(dj.Lookup):
    @classproperty
    def key_source(cls):
        return reduce(mul, [key.proj() for key in cls.keys])

    @classproperty
    def member_key(cls):
        return cls.key_source.primary_key

    @classproperty
    def order(cls):
        return [f"{key} ASC" for key in cls.member_key]

    @rowproperty
    def members(self):
        """
        Returns
        -------
        Set.Member
            tuples that make up the set
        """
        key, n = self.fetch1(dj.key, "members")
        members = self.Member & key

        if len(members) == n:
            return members
        else:
            raise MissingError("Members are missing.")

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
        keys = cls.key_source.restrict(restriction)
        keys = keys.fetch(as_dict=True, order_by=cls.order)
        n = len(keys)

        key = {i: key_hash(k) for i, k in enumerate(keys)}
        key = {f"{cls.name}_id": key_hash(key)}

        if cls & key:
            assert (cls & key).fetch1("members") == len(cls.Member & key)

            if not silent:
                logger.info(f"{key} already exists.")

        elif not prompt or user_choice(f"Insert set with {n} keys?") == "yes":

            cls.insert1(
                dict(key, members=n),
                skip_duplicates=True,
            )

            index = f"{cls.name}_index"
            cls.Member.insert(
                [{index: i, **k, **key} for i, k in enumerate(keys)],
                skip_duplicates=True,
            )

            if not silent:
                logger.info(f"{key} inserted.")

        else:
            if not silent:
                logger.info(f"{key} not inserted.")

            return

        if note:
            if not silent:
                logger.info(f"Note for {key} inserted.")

            cls.Note.insert1(
                dict(key, note=note),
                skip_duplicates=True,
            )

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
        members = cls.Member & key
        key = candidates.aggr(members, n="count(*)") & f"n = {n}"

        if key:
            return cls & key.fetch1(dj.key)
        else:
            raise MissingError("Set does not exist.")


def setup_set(cls, schema):
    length = int(getattr(cls, "length", 32))
    length = max(0, min(length, 32))

    foriegn_keys, context = foreigns(cls.keys, schema)

    Member = type(
        "Member",
        (dj.Part,),
        {"definition": part_definition(foriegn_keys, cls.name)},
    )
    Note = type(
        "Note",
        (dj.Part,),
        {"definition": note_definition},
    )
    attr = {
        "definition": master_definition(cls.name, getattr(cls, "comment", cls.name), length),
        "length": length,
        "Member": Member,
        "Note": Note,
    }
    cls = type(cls.__name__, (cls, Set), attr)
    cls = schema(cls, context=context)
    return cls
