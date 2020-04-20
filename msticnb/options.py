# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklets options."""
from typing import Any

from ._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


_OPTIONS = {
    "verbose": True,
    "debug": False,
}


def get_opt(option: str) -> Any:
    """
    Get the named option.

    Parameters
    ----------
    option : str
        Option name.

    Returns
    -------
    Any
        Option value

    Raises
    ------
    KeyError
        An invalid option name was supplied.

    """
    if option in _OPTIONS:
        return _OPTIONS[option]
    raise KeyError(f"Unrecognized option {option}.")


def set_opt(option: str, value: Any):
    """
    Set the named option.

    Parameters
    ----------
    option : str
        Option name.

    value : Any
        Option value.

    Raises
    ------
    KeyError
        An invalid option name was supplied.
    TypeError
        Option value was not the correct type.

    """
    cur_opt = _OPTIONS.get(option)
    if cur_opt is None:
        raise KeyError(f"Unrecognized option {option}.")
    if not isinstance(value, type(cur_opt)):
        if value.casefold() == "true":
            value = True
        elif value.casefold() == "false":
            value = False
        else:
            try:
                value = type(cur_opt)(value)
            except ValueError:
                raise TypeError(
                    f"Option is of type {type(cur_opt)}.",
                    "{value} cannot be converted to that type.")
    _OPTIONS[option] = value
