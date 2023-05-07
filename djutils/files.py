import os
from collections import deque
from .rows import rowmethod
from .utils import key_hash, classproperty, from_camel_case, user_choice


class Filepath:
    """File path handling"""

    @classproperty
    def _checksums(cls):
        if not hasattr(cls, "_checksums_"):
            cls._checksums_ = deque(maxlen=os.getenv("DJUTILS_FILEPATH_CACHE", 1024))
        return cls._checksums_

    @classproperty
    def _tablepath(cls):
        return os.path.join(cls.database, from_camel_case(cls.__name__))

    @classproperty
    def _filepaths(cls):
        return {k: v for k, v in cls.heading.attributes.items() if v.is_filepath}

    @classmethod
    def createpath(cls, key, attr, suffix=None):
        store = cls._filepaths[attr].store
        extern = cls().external[store]

        location = extern.spec["location"]
        assert location == extern.spec["stage"]

        tablepath = cls._tablepath
        keypath = key_hash({k: key[k] for k in cls.primary_key})

        folder = os.path.join(location, tablepath, keypath)
        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = attr if suffix is None else f"{attr}.{suffix}"
        filepath = os.path.join(folder, filename)

        return filepath

    @rowmethod
    def filepath(self, attr, checksum=True):
        """Fetches the filepath with optional checksum verification"""

        store = self._filepaths[attr].store
        extern = self.external[store]

        key = self.proj(hash=attr)
        filepath = (extern & key).fetch1("filepath")
        filepath = os.path.join(extern.spec["location"], filepath)

        if checksum and filepath not in self._checksums:
            _filepath = self.fetch1(attr)
            assert filepath == _filepath
            self._checksums.append(filepath)

        return filepath

    @classmethod
    def prune(cls):
        """Deletes the untracked filepaths and directories"""

        if user_choice(f"Are you sure you want to prune {cls.__name__}?") != "yes":
            return

        tablepath = cls._tablepath
        stores = {v.store for v in cls._filepaths.values()}
        extern = cls().external
        key = f'filepath like "{tablepath}%"'

        for store in stores:

            (extern[store] & key).delete(delete_external_files=True)

            root = os.path.join(extern[store].spec["location"], tablepath)
            deleted = set()

            for dirpath, dirnames, filenames in os.walk(root, topdown=False):

                dirs = (os.path.join(dirpath, _) for _ in dirnames)
                dirs = filter(lambda x: x not in deleted, dirs)
                dirs = list(dirs)

                if not filenames and not dirs:
                    os.rmdir(dirpath)
                    deleted.add(dirpath)
