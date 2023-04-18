import datajoint as dj
from datajoint.hash import key_hash
from datajoint.utils import user_choice
import inspect
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


def member_definition(foreigns):
    return """
    -> master
    {foreigns}
    """.format(
        foreigns="\n    ".join([f"-> {f}" for f in foreigns]),
    )


note_definition = """
    -> master
    note                            :varchar(1024)      # group note
    ---
    note_ts = CURRENT_TIMESTAMP     : timestamp         # automatic timestamp
    """


class Master(dj.Lookup):
    @property
    def key_source(self):
        if self._key_source is None:

            self._key_source = self.keys[0].proj()

            for key in self.keys[1:]:
                self._key_source *= key.proj()

        return self._key_source

    @classmethod
    def fill(cls, restriction, note=None, *, prompt=True):
        """Creates a hash for the restricted tuples, and inserts into master, member, and note tables

        Parameters
        ----------
        restriction : datajoint restriction
            used to restrict key_source
        """
        keys = cls.key_source.restrict(restriction)

        hashes = keys.fetch(as_dict=True, order_by=keys.primary_key)
        hashes = dict([[i, key_hash(k)] for i, k in enumerate(keys)])

        key = {f"{cls.name}_id": key_hash(hashes)}

        if cls & key:
            assert (cls & key).fetch1("members") == len(cls.Member & key)
            logger.info(f"{key} already exists.")

        elif not prompt or user_choice(f"Insert group with {len(keys)} keys?") == "yes":
            cls.insert1(dict(key, members=len(keys)))

            members = (cls & key).proj() * keys
            cls.Member.insert(members)

            logger.info(f"{key} inserted.")

        else:
            logger.info(f"{key} not inserted.")
            return

        if note:
            logger.info(f"Note for {key} inserted.")
            cls.Note.insert1(dict(key, note=note), skip_duplicates=True)

    @property
    def members(self):
        key, n = self.fetch1(dj.key, "members")
        members = self.Member & key

        if len(members) == n:
            return members
        else:
            raise MissingError("Members are missing.")


def group(schema):
    def decorate(cls):
        cls = setup(cls, schema)
        return cls

    return decorate


def setup(cls, schema):

    keys = tuple(cls.keys)
    tables = tuple(key.__name__ for key in keys)
    databases = tuple(key.database for key in keys)

    name = str(cls.name)
    comment = str(cls.comment)
    length = int(getattr(cls, "length", 32))
    length = max(0, min(length, 32))

    if schema.context is None:
        context = dict(inspect.currentframe().f_back.f_locals)
    else:
        context = dict(schema.context)

    foreigns = []
    for key, database, table in zip(keys, databases, tables):

        if database == schema.database:
            foreign = table
            if table not in context:
                context[table] = key
        else:
            foreign = f"{database}.{table}"
            if database not in context:
                context[database] = dj.create_virtual_module(database, database)

        foreigns.append(foreign)

    member_attr = dict(
        definition=member_definition(foreigns),
    )
    Member = type("Member", (dj.Part,), member_attr)

    note_attr = dict(
        definition=note_definition,
    )
    Note = type("Note", (dj.Part,), note_attr)

    master_attr = dict(
        definition=master_definition(name, comment, length),
        keys=keys,
        _key_source=None,
        _tables=tables,
        name=name,
        comment=comment,
        length=length,
        Member=Member,
        Note=Note,
    )
    cls = type(cls.__name__, (Master,), master_attr)
    cls = schema(cls, context=context)
    return cls
