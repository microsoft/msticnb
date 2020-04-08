# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Common definitions and classes."""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Union, Any, Iterable, List, Set

import attr
from attr import Factory
import pandas as pd

from msticpy.data import QueryProvider


@attr.s(auto_attribs=True)
class NotebookletResult:
    """Base result class."""

    description: str


@attr.s(auto_attribs=True)
class NBMetaData:
    """Notebooklet metadata class."""

    name: str
    description: str
    options: List[str] = Factory(list)
    entity_types: List[str] = Factory(list)
    keywords: List[str] = Factory(list)

    @property
    def search_terms(self) -> Set[str]:
        """Return set of search terms for the object."""
        return set(
            [self.name]
            + [obj.casefold() for obj in self.entity_types]  # type: ignore
            + [key.casefold() for key in self.keywords]  # type: ignore
        )


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


class Notebooklet(ABC):
    """Base class for Notebooklets."""

    metadata: NBMetaData = NBMetaData(
        name="Notebooklet", description="Base class",
    )

    def __init__(
        self, query_provider: QueryProvider, enrichment_providers: dict = None, **kwargs
    ):
        """
        Intialize a new instance of the notebooklet class.

        Parameters
        ----------
        query_provider : QueryProvider
            Optional query_provider instance to query data.
            Most classes require this.
        

        """
        self.query_provider = query_provider
        self.enrichment_providers = enrichment_providers
        self._kwargs = kwargs
        self.result = None
        self.options = self.all_options

    @abstractmethod
    def run(
        self,
        value: Any = None,
        data: Optional[pd.DataFrame] = None,
        timespan: Optional[TimeSpan] = None,
        options: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> NotebookletResult:
        """
        Notebooklet abstract base class.

        Parameters
        ----------
        value : Any, optional
            value to process, by default None
        data : Optional[pd.DataFrame], optional
            Input data to process, by default None
        timespan : Optional[TimeSpan], optional
            Timespan over , by default None
        options :Optional[Iterable[str]], optional
            [description], by default None

        Returns
        -------
        NotebookletResult
            [description]
        """

    @property
    def name(self) -> str:
        """
        Return name of the Notebooklet.

        Returns
        -------
        str
            Name

        """
        return self.metadata.name

    @property
    def description(self) -> str:
        """
        Return description of the Notebooklet.

        Returns
        -------
        str
            Description

        """
        return self.metadata.description

    @property
    def all_options(self) -> List[str]:
        """
        Return supported options for Notebooklet run function.

        Returns
        -------
        List[str]
            Supported options.

        """
        return self.metadata.options

    @property
    def keywords(self) -> List[str]:
        """
        Return search keywords for Notebooklet.

        Returns
        -------
        List[str]
            Keywords

        """
        return self.metadata.keywords

    @property
    def entity_types(self) -> List[str]:
        """
        Entity types supported by the notebooklet.

        Returns
        -------
        List[str]
            Entity names

        """
        return self.metadata.entity_types


class NotebookletException(Exception):
    """Generic exception class for Notebooklets."""
