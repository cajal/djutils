import datajoint as dj
from operator import mul
from functools import reduce
from .resolve import foreigns
from .utils import classproperty, key_hash, user_choice
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


def part_definition(name, foreign_keys):
    return """
    -> master
    {name}_index                    : int unsigned      # list index
    ---
    {foreign_keys}
    """.format(
        name=name,
        foreign_keys="\n    ".join([f"-> {f}" for f in foreign_keys]),
    )


note_definition = """
    -> master
    note                            : varchar(1024)     # note for list
    ---
    note_ts = CURRENT_TIMESTAMP     : timestamp         # automatic timestamp
    """


class List(dj.Lookup):
    @classproperty
    def key_source(cls):
        return reduce(mul, [key.proj() for key in cls.keys])

    @property
    def members(self):
        """
        Returns
        -------
        List.Member
            rows that make up the list
        """
        key, n = self.fetch1(dj.key, "members")
        members = self.Member & key

        if len(members) == n:
            return members
        else:
            raise MissingError("Members are missing.")

    @classmethod
    def fill(cls, restrictions, note=None, *, prompt=True, silent=False):
        """Creates a hash for the restriction list, and inserts into master, member, and note tables

        Parameters
        ----------
        restrictions : List[datajoint restriction]
            used to restrict key_source
        note : str | None
            note to attach to the tuple set

        Returns
        -------
        dict | None
            list key
        """
        keys = [cls.key_source.restrict(_).fetch1() for _ in restrictions]
        n = len(keys)

        key = {i: key_hash(k) for i, k in enumerate(keys)}
        key = {f"{cls.name}_id": key_hash(key)}

        if cls & key:
            assert (cls & key).fetch1("members") == len(cls.Member & key)

            if not silent:
                logger.info(f"{key} already exists.")

        elif not prompt or user_choice(f"Insert list with {n} keys?") == "yes":

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


def setup_list(cls, schema):
    length = int(getattr(cls, "length", 32))
    length = max(0, min(length, 32))

    foreign_keys, context = foreigns(cls.keys, schema)

    Member = type(
        "Member",
        (dj.Part,),
        {"definition": part_definition(cls.name, foreign_keys)},
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
    cls = type(cls.__name__, (cls, List), attr)
    cls = schema(cls, context=context)
    return cls
