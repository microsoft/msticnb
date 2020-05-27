# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Common definitions and classes."""
from datetime import datetime, timedelta
import functools
from typing import Union, Optional, Iterable, Tuple, Any, List

from dateutil.parser import ParserError  # type: ignore
from IPython.display import display, HTML
from markdown import markdown
import pandas as pd

from msticpy.common import utility as mp_utils

from .options import get_opt

from ._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


# pylint: disable=too-few-public-methods
class TimeSpan:
    """Timespan parameter for notebook modules."""

    # pylint: enable=too-many-branches
    def __init__(
        self,
        timespan: Optional[Union["TimeSpan", Tuple[Any, Any]]] = None,
        start: Optional[Union[datetime, str]] = None,
        end: Optional[Union[datetime, str]] = None,
        period: Optional[Union[timedelta, str]] = None,
        time_selector: Any = None,
    ):
        """
        Initialize Timespan.

        Parameters
        ----------
        timespan : Union(TimeSpan, Tuple(Any, Any)), optional
            Another TimeSpan object or a tuple of datetimes
            or datetime strings, by default None
        start : Optional[Union[datetime, str]], optional
            datetime of the start of the time period, by default None
        end : Optional[Union[datetime, str]], optional
            datetime of the end of the time period, by default utcnow
        period : Optional[Union[timedelta, str]], optional
            duration of the period, by default None
        time_selector : Any
            an object that has either `start` and `end` or `start` and
            `period` date_time-like attributes.

        Raises
        ------
        ValueError
            If neither `start` nor `period` are specified.

        """
        start, end, period = self._process_args(
            timespan, time_selector, start, end, period
        )

        if not start and not period:
            raise MsticnbMissingParameterError(
                "start, period",
                "At least one of 'start' or 'period' must be specified.",
            )

        self.period = None
        if period:
            self.period = self._parse_timedelta(period)

        self.end = self._parse_time(end, "end")
        self.start = self._parse_time(start, "start")
        if self.start and self.period:
            self.end = self.start + self.period
        if self.end is None:
            self.end = datetime.utcnow()
        if self.start is None and self.period:
            self.start = self.end - self.period

    def __eq__(self, value):
        """Return True if the timespans are equal."""
        if not isinstance(value, TimeSpan):
            return False
        return self.start == value.start and self.end == value.end

    @staticmethod
    def _process_args(timespan, time_selector, start, end, period):
        if timespan and isinstance(timespan, TimeSpan):
            start = timespan.start
            end = timespan.end
            period = timespan.period
        elif timespan and isinstance(timespan, tuple):
            start = timespan[0]
            end = timespan[1]
        if not start and hasattr(time_selector, "start"):
            start = getattr(time_selector, "start", None)
        if not end and hasattr(time_selector, "end"):
            end = getattr(time_selector, "end", None)
        if not period and hasattr(time_selector, "period"):
            period = getattr(time_selector, "period", None)
        return start, end, period

    @staticmethod
    def _parse_time(time_val, prop_name):
        if time_val is None:
            return None
        if isinstance(time_val, datetime):
            return time_val
        try:
            if isinstance(time_val, str):
                return pd.to_datetime(time_val, infer_datetime_format=True)
        except (ValueError, ParserError):
            pass
        raise ValueError(f"'{prop_name}' must be a datetime or a datetime string.")

    @staticmethod
    def _parse_timedelta(time_val):
        if time_val is None:
            return None
        if isinstance(time_val, timedelta):
            return time_val
        try:
            if isinstance(time_val, str):
                return pd.Timedelta(time_val).to_pytimedelta()
        except (ValueError, ParserError):
            pass
        raise ValueError(
            "'period' must be a pandas-compatible time period string",
            " or Python timedelta.",
        )


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
        """Print a string represenation of the object."""
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
        """Iterate through all notebooklet classes."""
        for key, val in self.__dict__.items():
            if isinstance(val, NBContainer):
                yield from val.iter_classes()
            else:
                yield key, val


def nb_print(mssg: Any):
    """
    Print a status message.

    Parameters
    ----------
    mssg : Any
        The item/message to show

    """
    if get_opt("verbose") and not get_opt("silent"):
        print(mssg)


def nb_data_wait(source: str):
    """
    Print Getting data message.

    Parameters
    ----------
    source : str
        The data source.

    """
    nb_print(f"Getting data from {source}...")


def nb_debug(*args):
    """Print debug args."""
    if get_opt("debug"):
        for arg in args:
            print(arg, end="--")
        print()


def nb_markdown(*args, **kwargs):
    """Display Markdown/HTML text."""
    if not get_opt("silent"):
        mp_utils.md(*args, **kwargs)


def nb_warn(*args, **kwargs):
    """Display Markdown/HTML warning text."""
    if not get_opt("silent"):
        mp_utils.md_warn(*args, **kwargs)


def nb_display(*args, **kwargs):
    """Ipython display function wrapper."""
    if not get_opt("silent"):
        display(*args, **kwargs)


# pylint: disable=invalid-name
def set_text(
    title: Optional[str] = None,
    hd_level: int = 2,
    text: Optional[str] = None,
    md: bool = False,
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

    Returns
    -------
    Callable[*args, **kwargs]
        Wrapped function

    """

    def text_wrapper(func):
        @functools.wraps(func)
        def print_text(*args, **kwargs):
            if not get_opt("silent"):
                if title:
                    h_level = max(min(hd_level, 4), 1)
                    display(HTML(f"<h{h_level}>{title}</h{h_level}>"))
                if text:
                    if md:
                        display(HTML(markdown(text=text)))
                    else:
                        fmt_text = text.replace("\n", "<br>")
                        display(HTML(f"{fmt_text}"))
            return func(*args, **kwargs)

        return print_text

    return text_wrapper


# pylint: disable=invalid-name


def add_result(result: Any, attr_name: Union[str, List[str]]):
    """
    Decorate func to add return value(s) to `result`.

    Parameters
    ----------
    result : Any
        Object that will have result attributes set.
    attr_name: str or List[str]
        Name of return attribute to set on `result`

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
