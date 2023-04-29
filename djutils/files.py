import os
import datajoint as dj
from datajoint.hash import key_hash
from datajoint.utils import from_camel_case, user_choice
from shutil import rmtree
from .logging import logger


class Files:
    store = None

    @classmethod
    def table_dir(cls, *, root=None, create=False):
        """
        root : str | None
            root directory
        """
        if root is None:
            if cls.store is None:
                root = os.getcwd()
            else:
                root = dj.config["stores"][cls.store]["location"]

        table_dir = os.path.join(root, cls.database, from_camel_case(cls.__name__))

        if create and not os.path.exists(table_dir):
            os.makedirs(table_dir)

        return table_dir

    @classmethod
    def tuple_dir(cls, key, *, root=None, create=False):
        """
        key : dict
            dictionary primary key of table
        root : str | None
            root directory --- defaults to cls.store location if root is None
        """
        key = {k: key[k] for k in cls.primary_key}

        tuple_dir = os.path.join(cls.table_dir(root=root), key_hash(key))

        if create and not os.path.exists(tuple_dir):
            os.makedirs(tuple_dir)

        return tuple_dir

    @classmethod
    def prune(cls, *, root=None):
        table_dir = cls.table_dir(root=root)

        if not os.path.exists(table_dir):
            logger.info("Table directory does not exist. Nothing to prune.")
            return

        paths = set(os.listdir(table_dir)) - set(map(key_hash, cls.fetch(dj.key)))
        n = len(paths)

        if not n:
            logger.info("No untracked paths to remove")
            return

        if user_choice(f"Remove {n} paths in {table_dir}?") == "yes":

            for path in paths:
                full_path = os.path.join(table_dir, path)

                if os.path.isdir(full_path):
                    rmtree(full_path)

                else:
                    os.remove(full_path)

            logger.info(f"{n} paths removed.")

        else:
            logger.info(f"{n} paths not removed.")
