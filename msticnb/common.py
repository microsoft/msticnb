# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Common definitions and classes."""
from datetime import datetime, timedelta
import functools
from typing import Union, Optional, Iterable, Tuple, Any, List, Dict

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
    ):
        """
        Initialize Timespan.

        Parameters
        ----------
        timespan : Union(TimeSpan, Tuple(Any, Any)), optional
            A TimeSpan object
            or a tuple of datetimes or datetime strings,
            or an object that has either `start` and `end` or `start` and
            `period` date_time-like attributes.
            By default None
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
        start, end, period = self._process_args(timespan, start, end, period)

        if not start and not period:
            raise MsticnbMissingParameterError(
                "start, period",
                "At least one of 'start' or 'period' must be specified.",
            )

        self._period = None
        if period:
            self._period = self._parse_timedelta(period)

        self._end = self._parse_time(end, "end")
        self._start = self._parse_time(start, "start")
        if self._start and self._period:
            self._end = self._start + self._period
        if self._end is None:
            self._end = datetime.utcnow()
        if self._start is None and self._period:
            self._start = self._end - self._period

    def __eq__(self, value):
        """Return True if the timespans are equal."""
        if not isinstance(value, TimeSpan):
            return False
        return self.start == value.start and self.end == value.end

    def __hash__(self):
        """Return the hash of the timespan."""
        return hash((self.start, self.end))

    @property
    def start(self) -> datetime:
        """
        Return the start of the timeperiod.

        Returns
        -------
        datetime
            Start datetime.

        """
        return self._start

    @property
    def end(self) -> datetime:
        """
        Return the end of the timeperiod.

        Returns
        -------
        datetime
            End datetime.

        """
        return self._end

    @property
    def period(self) -> timedelta:
        """
        Return the period of the timeperiod.

        Returns
        -------
        timedelta
            Period timedelta.

        """
        if not self._period:
            self._period = self.start - self.end
        return self._period

    @staticmethod
    def _process_args(timespan, start, end, period):
        if timespan:
            if isinstance(timespan, TimeSpan):
                start = timespan.start
                end = timespan.end
                period = timespan.period
            elif isinstance(timespan, tuple):
                start = timespan[0]
                end = timespan[1]
        if not start and hasattr(timespan, "start"):
            start = getattr(timespan, "start", None)
        if not end and hasattr(timespan, "end"):
            end = getattr(timespan, "end", None)
        if not period and hasattr(timespan, "period"):
            period = getattr(timespan, "period", None)
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


# pylint: disable=invalid-name, unused-argument
def set_text(  # noqa: MC0001
    title: Optional[str] = None,
    hd_level: int = 2,
    text: Optional[str] = None,
    md: bool = False,
    docs: Dict[str, Any] = None,
    key: str = None,
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
            if "silent" in kwargs:
                run_silent = kwargs.get("silent")
            else:
                run_silent = get_opt("silent")
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
