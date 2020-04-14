# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Common definitions and classes."""
from datetime import datetime, timedelta
from typing import Union, Optional, Iterable, Tuple, Any

import pandas as pd

from ._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


class TimeSpan:
    """Timespan parameter for notebook modules."""

    def __init__(
        self,
        start: Optional[Union[datetime, str]] = None,
        end: Optional[Union[datetime, str]] = None,
        period: Optional[Union[timedelta, str]] = None,
    ):
        """
        Initialize Timespan.

        Parameters
        ----------
        start : Optional[Union[datetime, str]], optional
            datetime of the start of the time period, by default None
        end : Optional[Union[datetime, str]], optional
            datetime of the end of the time period, by default utcnow
        period : Optional[Union[timedelta, str]], optional
            duration of the period, by default None

        Raises
        ------
        ValueError
            If neither `start` nor `period` are specified.

        """
        if not start and not period:
            raise ValueError("At least one of 'start' or 'period' must be specified.")

        self.period = None
        if period:
            if isinstance(period, str):
                # parse period string properly
                self.period = pd.TimeDelta(str).to_pytimedelta()
            elif isinstance(period, timedelta):
                self.period = timedelta
            else:
                raise NotebookletException(
                    "'period' must be a pandas-compatible time period string",
                    " or Python timedelta.",
                )

        if end is None:
            self.end = datetime.utcnow()
        elif isinstance(end, str):
            self.end = pd.to_datetime(end, infer_datetime_format=True)
        elif isinstance(end, datetime):
            self.end = end
        else:
            raise NotebookletException("'end' must be a datetime or a datetime string.")
        if start is None and self.period:
            self.start = self.end - self.period
        elif isinstance(start, str):
            self.start = pd.to_datetime(start, infer_datetime_format=True)
        elif isinstance(start, datetime):
            self.start = start
        else:
            raise NotebookletException(
                f"'start' must be a datetime or a datetime string."
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
        return "\n".join(self.__dict__.keys())

    def iter_classes(self) -> Iterable[Tuple[str, Any]]:
        """Iterate through all notebooklet classes."""
        for key, val in self.__dict__.items():
            if isinstance(val, NBContainer):
                yield from val.iter_classes()
            else:
                yield key, val


def find_type_in_globals(req_type: type, last=False):
    """Return first (or last) instance of a type if it exists in globals."""
    found = [inst for inst in globals() if isinstance(inst, req_type)]
    return found[0 if last else -1] if found else None


class NotebookletException(Exception):
    """Generic exception class for Notebooklets."""
