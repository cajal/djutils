import io
import pickle
import numpy as np


def pickle_save(obj, protocol=None):
    """
    Parameters
    ----------
    obj : object
        object to save
    protocol : int | None
        pickle protocol

    Returns
    -------
    1D array (np.uint8)
        byte array
    """
    f = io.BytesIO()

    pickle.dump(obj, f, protocol=protocol)
    array = np.frombuffer(f.getvalue(), dtype=np.uint8)

    f.close()
    return array


def pickle_load(array):
    """
    Parameters
    ----------
    array : 1D array (np.uint8)
        byte array to load from

    Returns
    -------
    object
        loaded object
    """
    f = io.BytesIO(array.tobytes())
    obj = pickle.load(f)

    f.close()
    return obj
