import hashlib
import re
from datajoint import DataJointError


class class_property:
    """decorator that turns a class method into a property"""

    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


# ----- from https://github.com/datajoint/datajoint-python -----


def key_hash(mapping):
    """
    32-byte hash of the mapping's key values sorted by the key name.
    This is often used to convert a long primary key value into a shorter hash.
    For example, the JobTable in datajoint.jobs uses this function to hash the primary key of autopopulated tables.
    """
    hashed = hashlib.md5()
    for k, v in sorted(mapping.items()):
        hashed.update(str(v).encode())
    return hashed.hexdigest()


def user_choice(prompt, choices=("yes", "no"), default=None):
    """
    Prompts the user for confirmation.  The default value, if any, is capitalized.
    :param prompt: Information to display to the user.
    :param choices: an iterable of possible choices.
    :param default: default choice
    :return: the user's choice
    """
    assert default is None or default in choices
    choice_list = ", ".join((choice.title() if choice == default else choice for choice in choices))
    response = None
    while response not in choices:
        response = input(prompt + " [" + choice_list + "]: ")
        response = response.lower() if response else default
    return response


def from_camel_case(s):
    """
    Convert names in camel case into underscore (_) separated names
    :param s: string in CamelCase notation
    :returns: string in under_score notation
    Example:
    >>> from_camel_case("TableName") # yields "table_name"
    """

    def convert(match):
        return ("_" if match.groups()[0] else "") + match.group(0).lower()

    if not re.match(r"[A-Z][a-zA-Z0-9]*", s):
        raise DataJointError("ClassName must be alphanumeric in CamelCase, begin with a capital letter")
    return re.sub(r"(\B[A-Z])|(\b[A-Z])", convert, s)