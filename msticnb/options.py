# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Notebooklets global options.

Available options are:
[name, type (default value), description]

- `verbose`: bool (True) - Show progress messages.
- `debug`: bool (False) - Turn on debug output.
- `show_sample_results`: bool (True) - Display sample of results as they are produced.
- `silent`: bool (False) - Execute notebooklets with no output.

"""
from typing import Any, Dict

from ._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


_OPTION_DEFN = {
    "verbose": (True, "Show progress messages."),
    "debug": (False, "Turn on debug output."),
    "show_sample_results": (False, "Display sample of results as they are produced."),
    "silent": (False, "Execute notebooklets with no output"),
    "temp_silent": (False, "Execute notebooklets with no output"),
}


_OPT_DICT: Dict[str, Any] = {key: val[0] for key, val in _OPTION_DEFN.items()}


def show():
    """Show help for options."""
    print(
        "\n".join(
            [f"{key} (default={val[0]}): {val[1]}" for key, val in _OPTION_DEFN.items()]
        )
    )


def current():
    """Show current settings."""
    print("\n".join([f"{key}: {val}" for key, val in _OPT_DICT.items()]))


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
    if option in _OPT_DICT:
        if option == "silent":
            if _OPT_DICT.get("temp_silent") is not None:
                return _OPT_DICT.get("temp_silent")
            return _OPT_DICT.get("silent")
        return _OPT_DICT[option]
    raise KeyError(f"Unknown option {option}.")


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
    if option not in _OPT_DICT:
        raise KeyError(f"Unrecognized option {option}.")

    cur_opt = _OPT_DICT[option]
    # allow temp_silent to be None
    if option != "temp_silent" and not isinstance(value, type(cur_opt)):
        try:
            value = type(cur_opt)(value)
        except ValueError as err:
            raise TypeError(
                f"Option is of type {type(cur_opt)}.",
                "{value} cannot be converted to that type.",
            ) from err
    _OPT_DICT[option] = value
