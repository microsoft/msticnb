# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Common definitions and classes."""
import functools
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import bokeh.io
import pandas as pd
from IPython import get_ipython
from IPython.display import HTML, display
from markdown import markdown
from msticpy import VERSION as MP_VERSION
from msticpy.common import utility as mp_utils
from pkg_resources import parse_version

from ._version import VERSION
from .options import get_opt

__version__ = VERSION
__author__ = "Ian Hellen"


_IP_AVAILABLE = get_ipython() is not None


class NBContainer:
    """Container for Notebooklet classes."""

    def __len__(self):
        """Return number of items in the attribute collection."""
        return len(self.__dict__)

    def __iter__(self):
        """Return iterator over the attributes."""
        return iter(self.__dict__.items())

    def __repr__(self):
        """Return list of attributes."""
        obj_list = []
        for key, val in self.__dict__.items():
            if isinstance(val, NBContainer):
                obj_list.append(f"{key} [{repr(val)}]")
            else:
                obj_list.append(repr(val))
        return ", ".join(obj_list)

    def __str__(self):
        """Print a string representation of the object."""
        obj_str = ""
        for key, val in self.__dict__.items():
            if isinstance(val, NBContainer):
                obj_str += f"{key}\n"
                for line in str(val).split("\n"):
                    if line.strip():
                        obj_str += f"  {line}\n"
            else:
                obj_str += val.__name__ + " (Notebooklet)\n"
        return obj_str

    def iter_classes(self) -> Iterable[Tuple[str, Any]]:
        """Return iterator through all notebooklet classes."""
        for key, val in self.__dict__.items():
            if isinstance(val, NBContainer):
                yield from val.iter_classes()
            else:
                yield key, val


def nb_print(*args, **kwargs):
    """
    Print output but suppress if "silent".

    Parameters
    ----------
    mssg : Any
        The item/message to show

    """
    if get_opt("verbose") and not get_opt("silent"):
        print(*args, **kwargs)


def nb_data_wait(source: str):
    """
    Print Getting data message.

    Parameters
    ----------
    source : str
        The data source.

    """
    nb_markdown(f"Getting data from {source}...")


def nb_debug(*args):
    """Print debug args."""
    if get_opt("debug"):
        for arg in args:
            print(arg, end="--")
        print()


def nb_markdown(*args, **kwargs):
    """Display Markdown/HTML text."""
    if not get_opt("silent"):
        if _IP_AVAILABLE:
            mp_utils.md(*args, **kwargs)
        else:
            nb_print(*args)


def nb_warn(*args, **kwargs):
    """Display Markdown/HTML warning text."""
    if not get_opt("silent"):
        if _IP_AVAILABLE:
            mp_utils.md_warn(*args, **kwargs)
        else:
            nb_print("WARNING:", *args)


def nb_display(*args, **kwargs):
    """Ipython display function wrapper."""
    if not get_opt("silent"):
        display(*args, **kwargs)


# pylint: disable=invalid-name, unused-argument
def set_text(  # noqa: MC0001
    title: Optional[str] = None,
    hd_level: int = 2,
    text: Optional[str] = None,
    md: bool = False,
    docs: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
):
    """
    Decorate function to print title/text before execution.

    Parameters
    ----------
    title : Optional[str], optional
        Title text to print, by default None
    hd_level : int
        Heading level (1-4), by default 2
    text : Optional[str], optional
        Text to print, by default None
    md : bool, optional
        Treat `text` as markdown, by default False
    docs : Dict[str, Any]
        Dictionary of cell documentation indexed by `key`
    key : str
        Item to use from `docs` dictionary.

    Returns
    -------
    Callable[*args, **kwargs]
        Wrapped function

    """

    def text_wrapper(func):
        @functools.wraps(func)
        def print_text(*args, **kwargs):
            # "silent" can be global option or in the func kwargs
            # The latter is only applicable for the NB run() method.
            run_silent = kwargs.get("silent") or get_opt("silent")

            if not run_silent:
                h_level = hd_level
                out_title = title
                out_text = text
                other_items = {}
                if docs and key:
                    out_title = docs.get(key, {}).get("title")
                    out_text = docs.get(key, {}).get("text")
                    h_level = docs.get(key, {}).get("hd_level", 2)
                    other_items = {
                        hdr: str(text)
                        for hdr, text in docs.get(key, {}).items()
                        if hdr not in ("title", "text", "doc", "hd_level", "md")
                    }
                if out_title:
                    h_level = max(min(h_level, 4), 1)
                    display(HTML(f"<h{h_level}>{out_title}</h{h_level}>"))
                if out_text:
                    if md:
                        display(HTML(markdown(text=out_text)))
                    else:
                        display(HTML(out_text.replace("\n", "<br>")))
                if other_items:
                    for sec_title, content in other_items.items():
                        display(HTML(f"<br><b>{sec_title}</b><br>"))
                        display(HTML(content.replace("\n", "<br>")))
            return func(*args, **kwargs)

        return print_text

    return text_wrapper


# pylint: enable=invalid-name, unused-argument


def add_result(result: Any, attr_name: Union[str, List[str]]):
    """
    Decorate func to add return value(s) to `result`.

    Parameters
    ----------
    result : Any
        Object that will have result attributes set.
    attr_name: str or List[str]
        Name of return attribute to set on `result`.

    Returns
    -------
    Callable[*args, **kwargs]
        Wrapped function

    """

    def result_wrapper(func):
        @functools.wraps(func)
        def add_results(*args, **kwargs):
            func_results = func(*args, **kwargs)
            if isinstance(attr_name, str):
                setattr(result, attr_name, func_results)
            elif isinstance(attr_name, list):
                for attr, ret_val in zip(attr_name, func_results):
                    setattr(result, attr, ret_val)
            return func_results

        return add_results

    return result_wrapper


def show_bokeh(plot):
    """Display bokeh plot, resetting output."""
    try:
        bokeh.io.reset_output()
        bokeh.io.output_notebook(hide_banner=True)
        bokeh.io.show(plot)
    except RuntimeError:
        bokeh.io.output_notebook(hide_banner=True)
        bokeh.io.show(plot)


def df_has_data(data) -> bool:
    """Return True if `data` DataFrame has data."""
    return data is not None and not data.empty


class MsticnbError(Exception):
    """Generic exception class for Notebooklets."""


class MsticnbMissingParameterError(MsticnbError):
    """Parameter Error."""

    def __init__(self, *args):
        """
        Exception for missing parameter.

        Parameters
        ----------
        args : str
            First arg is the name or names of the parameters.

        """
        if args:
            self.mssg = f"Required parameter(s) '{args[0]}' not supplied."
            args = (self.mssg, *args[1:])
        super().__init__(*args)


class MsticnbDataProviderError(MsticnbError):
    """DataProvider Error."""


def mp_version():
    """Return currently-loaded msticpy version."""
    return parse_version(MP_VERSION)


def check_mp_version(required_version: str) -> bool:
    """Return true if the installed version is >= `required_version`."""
    return mp_version().major >= parse_version(required_version).major


def check_current_result(
    result, attrib: Optional[str] = None, silent: bool = False
) -> bool:
    """
    Check that the result is valid and `attrib` contains data.

    Parameters
    ----------
    result: NotebookletResult
        The result data to check in.
    attrib : str
        Name of the attribute to check, if None this function
    silent : bool
        If True, suppress output.

    Returns
    -------
    bool
        Returns True if valid data is available, else False.

    """
    if not attrib:
        return True
    data_obj = getattr(result, attrib)
    if data_obj is None or isinstance(data_obj, pd.DataFrame) and data_obj.empty:
        if not silent:
            nb_markdown(f"No data is available for {attrib}.")
        return False
    return True
