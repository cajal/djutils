import os
import datajoint as dj
from shutil import rmtree
from .rows import row_property
from .utils import key_hash, class_property, from_camel_case, user_choice
from .logging import logger


class Filepath:
    """File path handling"""

    @class_property
    def external_table(cls):
        return cls().external[cls.store] & f"filepath like '{cls.table_dir(relative=True)}%'"

    @classmethod
    def table_dir(cls, create=False, relative=False):
        """
        Parameters
        ----------
        create : bool
            create the directory

        Returns
        -------
        str
            table directory
        """
        root = dj.config["stores"][cls.store]["location"]

        rel_dir = os.path.join(cls.database, from_camel_case(cls.__name__))
        abs_dir = os.path.join(root, rel_dir)

        if create and not os.path.exists(abs_dir):
            os.makedirs(abs_dir)

        if relative:
            return rel_dir
        else:
            return abs_dir

    @classmethod
    def tuple_dir(cls, key, create=False):
        """
        Parameters
        ----------
        key : dict
            primary key of the table
        create : bool
            create the directory

        Returns
        -------
        str
            tuple directory
        """
        key = {k: key[k] for k in cls.primary_key}
        tuple_dir = os.path.join(cls.table_dir(), key_hash(key))

        if create and not os.path.exists(tuple_dir):
            os.makedirs(tuple_dir)

        return tuple_dir

    @row_property
    def dir(self):
        """
        Returns
        -------
        str
            tuple directory
        """
        return self.tuple_dir(self.fetch1(dj.key))

    @classmethod
    def prune(cls):
        """Prunes the untracked files in the table_dir"""

        table_dir = cls.table_dir()

        if not os.path.exists(table_dir):
            logger.info("Table directory does not exist. Nothing to prune.")
            return

        paths = set(os.listdir(table_dir)) - set(map(key_hash, cls.fetch(dj.key)))
        n = len(paths)

        if not n:
            logger.info("No untracked paths to remove")
            return

        if user_choice(f"Remove {n} paths in {table_dir}?") == "yes":

            cls.external_table.delete(delete_external_files=False)

            for path in paths:
                full_path = os.path.join(table_dir, path)

                if os.path.isdir(full_path):
                    rmtree(full_path)

                else:
                    os.remove(full_path)

            logger.info(f"{n} paths removed.")

        else:
            logger.info(f"{n} paths not removed.")
