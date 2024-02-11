# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklet for Windows Security Events."""
import os
import pkgutil
from io import StringIO
from typing import Any, Dict, Iterable, Optional, Union

import numpy as np
import pandas as pd
from bokeh.models import LayoutDOM
from defusedxml import ElementTree
from defusedxml.ElementTree import ParseError
from IPython.display import display
from msticpy.common.timespan import TimeSpan

try:
    from msticpy.vis.timeline import display_timeline
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.nbtools.nbdisplay import display_timeline

from .... import nb_metadata
from ...._version import VERSION
from ....common import (
    MsticnbMissingParameterError,
    nb_data_wait,
    nb_markdown,
    nb_warn,
    set_text,
)
from ....notebooklet import NBMetadata, Notebooklet, NotebookletResult

__version__ = VERSION
__author__ = "Ian Hellen"


_CLS_METADATA: NBMetadata
_CELL_DOCS: Dict[str, Any]
_CLS_METADATA, _CELL_DOCS = nb_metadata.read_mod_metadata(__file__, __name__)


# pylint: disable=too-few-public-methods
class WinHostEventsResult(NotebookletResult):
    """
    Windows Host Security Events Results.

    Attributes
    ----------
    all_events : pd.DataFrame
        DataFrame of all raw events retrieved.
    event_pivot : pd.DataFrame
        DataFrame that is a pivot table of event ID
        vs. Account
    account_events : pd.DataFrame
        DataFrame containing a subset of account management
        events such as account and group modification.
    acct_pivot : pd.DataFrame
        DataFrame that is a pivot table of event ID
        vs. Account of account management events
    account_timeline : Optional[LayoutDOM]
        Bokeh plot figure or Layout showing the account events on an
        interactive timeline.
    expanded_events : pd.DataFrame
        If `expand_events` option is specified, this will contain
        the parsed/expanded EventData as individual columns.

    """

    def __init__(
        self,
        description: Optional[str] = None,
        timespan: Optional[TimeSpan] = None,
        notebooklet: Optional["Notebooklet"] = None,
    ):
        """
        Create new Notebooklet result instance.

        Parameters
        ----------
        description : Optional[str], optional
            Result description, by default None
        timespan : Optional[TimeSpan], optional
            TimeSpan for the results, by default None
        notebooklet : Optional[, optional
            Originating notebooklet, by default None

        """
        super().__init__(description, timespan, notebooklet)
        self.description: str = "Windows Host Security Events"
        self.all_events: Optional[pd.DataFrame] = None
        self.event_pivot: Optional[pd.DataFrame] = None
        self.account_events: Optional[pd.DataFrame] = None
        self.account_pivot: Optional[pd.DataFrame] = None
        self.account_timeline: Optional[LayoutDOM] = None
        self.expanded_events: Optional[pd.DataFrame] = None


class WinHostEvents(Notebooklet):
    """
    Windows host Security Events Notebooklet class.

    Queries and displays Windows Security Events including:

    - All security events summary
    - Extracting and displaying account management events
    - Account management event timeline
    - Optionally parsing packed event data into DataFrame columns

    Process (4688) and Account Logon (4624, 4625) are not included
    in the event types processed by this module.

    """

    metadata = _CLS_METADATA
    __doc__ = nb_metadata.update_class_doc(__doc__, metadata)
    _cell_docs = _CELL_DOCS

    @set_text(docs=_CELL_DOCS, key="run")
    def run(
        self,
        value: Any = None,
        data: Optional[pd.DataFrame] = None,
        timespan: Optional[TimeSpan] = None,
        options: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> WinHostEventsResult:
        """
        Return Windows Security Event summary.

        Parameters
        ----------
        value : str
            Host name
        data : Optional[pd.DataFrame], optional
            Not used, by default None
        timespan : TimeSpan
            Timespan over which operations such as queries will be
            performed, by default None.
            This can be a TimeStamp object or another object that
            has valid `start`, `end`, or `period` attributes.
        options : Optional[Iterable[str]], optional
            List of options to use, by default None.
            A value of None means use default options.
            Options prefixed with "+" will be added to the default options.
            To see the list of available options type `help(cls)` where
            "cls" is the notebooklet class or an instance of this class.

        Other Parameters
        ----------------
        start : Union[datetime, datelike-string]
            Alternative to specifying timespan parameter.
        end : Union[datetime, datelike-string]
            Alternative to specifying timespan parameter.

        Returns
        -------
        HostSummaryResult
            Result object with attributes for each result type.

        Raises
        ------
        MsticnbMissingParameterError
            If required parameters are missing

        """
        super().run(
            value=value, data=data, timespan=timespan, options=options, **kwargs
        )

        if not value:
            raise MsticnbMissingParameterError("value")
        if not timespan:
            raise MsticnbMissingParameterError("timespan.")

        result = WinHostEventsResult(
            notebooklet=self, description=self.metadata.description, timespan=timespan
        )

        all_events_df, event_pivot_df = _get_win_security_events(
            self.query_provider, host_name=value, timespan=self.timespan
        )
        result.all_events = all_events_df
        result.event_pivot = event_pivot_df

        if "event_pivot" in self.options:
            _display_event_pivot(event_pivot=event_pivot_df)

        if "acct_events" in self.options:
            result.account_events = _extract_acct_mgmt_events(event_data=all_events_df)
            result.account_pivot = _create_acct_event_pivot(
                account_event_data=result.account_events
            )
            if result.account_pivot is not None:
                _display_acct_event_pivot(event_pivot_df=result.account_pivot)
                result.account_timeline = _display_acct_mgmt_timeline(
                    acct_event_data=result.account_events
                )

        if "expand_events" in self.options:
            result.expanded_events = _parse_eventdata(all_events_df)

        nb_markdown("To unpack eventdata from selected events use expand_events()")
        self._last_result = result  # pylint: disable=attribute-defined-outside-init
        return self._last_result

    def expand_events(
        self, event_ids: Optional[Union[int, Iterable[int]]] = None
    ) -> Optional[pd.DataFrame]:
        """
        Expand `EventData` for `event_ids` into separate columns.

        Parameters
        ----------
        event_ids : Optional[Union[int, Iterable[int]]], optional
            Single or interable of event IDs (ints).
            If no event_ids are specified all events will be expanded.

        Returns
        -------
        pd.DataFrame
            Results with expanded columns.

        Notes
        -----
        For a specific event ID you can expand the EventProperties values
        into their own columns using this function.
        You can do this for the whole data set but it will time-consuming
        and result in a lot of sparse columns in the output data frame.

        """
        if (
            not self._last_result or self._last_result.all_events is None
        ):  # type: ignore
            print(
                "Please use 'run()' to fetch the data before using this method.",
                "\nThen call 'expand_events()'",
            )
            return None
        return _parse_eventdata(
            event_data=self._last_result.all_events,  # type: ignore
            event_ids=event_ids,
        )


# %%
# Get Windows Security Events
def _get_win_security_events(qry_prov, host_name, timespan):
    nb_data_wait("SecurityEvent")

    all_events_df = qry_prov.WindowsSecurity.list_host_events(
        timespan,
        host_name=host_name,
        add_query_items="| where EventID != 4688 and EventID != 4624",
    )

    # Create a pivot of Event vs. Account
    win_events_acc = all_events_df[["Account", "Activity", "TimeGenerated"]].copy()
    win_events_acc = win_events_acc.replace("-\\-", "No Account").replace(
        {"Account": ""}, value="No Account"
    )
    win_events_acc["Account"] = win_events_acc.apply(
        lambda x: x.Account.split("\\")[-1], axis=1
    )
    event_pivot_df = (
        pd.pivot_table(
            win_events_acc,
            values="TimeGenerated",
            index=["Activity"],
            columns=["Account"],
            aggfunc="count",
        )
        .fillna(0)
        .reset_index()
    )
    return all_events_df, event_pivot_df


@set_text(docs=_CELL_DOCS, key="display_event_pivot")
def _display_event_pivot(event_pivot):
    display(
        event_pivot.style.map(lambda x: "color: white" if x == 0 else "")
        .map(
            lambda x: "background-color: lightblue"
            if not isinstance(x, str) and x > 0
            else ""
        )
        .set_properties(subset=["Activity"], **{"width": "400px", "text-align": "left"})
        .highlight_max(axis=1)
        .hide(axis="index")
    )


# %%
# Extract event details from events
SCHEMA = "http://schemas.microsoft.com/win/2004/08/events/event"


def _parse_event_data_row(row):
    try:
        xdoc = ElementTree.fromstring(row.EventData)
        col_dict = {
            elem.attrib["Name"]: elem.text for elem in xdoc.findall(f"{{{SCHEMA}}}Data")
        }
        reassigned = set()
        for key, val in col_dict.items():
            if key in row and not row[key]:
                row[key] = val
                reassigned.add(key)
        if reassigned:
            for key in reassigned:
                col_dict.pop(key)
        return col_dict
    except (ParseError, TypeError):
        return None


def _expand_event_properties(input_df):
    # For a specific event ID you can explode the EventProperties values
    # into their own columns using this function. You can do this for
    # the whole data set but it will result
    # in a lot of sparse columns in the output data frame.
    exp_df = input_df.apply(lambda x: pd.Series(x.EventProperties), axis=1)
    return (
        exp_df.drop(set(input_df.columns).intersection(exp_df.columns), axis=1)
        .merge(
            input_df.drop("EventProperties", axis=1),
            how="inner",
            left_index=True,
            right_index=True,
        )
        .replace("", np.nan)  # these 3 lines get rid of blank columns
        .infer_objects(copy=False)
        .dropna(axis=1, how="all")
        .fillna("")
    )


@set_text(docs=_CELL_DOCS, key="parse_eventdata")
def _parse_eventdata(event_data, event_ids: Optional[Union[int, Iterable[int]]] = None):
    if event_ids:
        if isinstance(event_ids, int):
            event_ids = [event_ids]
        src_event_data = event_data[event_data["EventID"].isin(event_ids)].copy()
    else:
        src_event_data = event_data.copy()

    if src_event_data.empty:
        nb_warn(f"No events matching {event_ids}")
        return None
    # Parse event properties into a dictionary
    nb_markdown("Parsing event data...")
    src_event_data["EventProperties"] = src_event_data.apply(
        _parse_event_data_row, axis=1
    )
    return _expand_event_properties(src_event_data)


# %%
# Account management events
def _extract_acct_mgmt_events(event_data):
    # Get a full list of Windows Security Events

    w_evt = pkgutil.get_data("msticpy", f"resources{os.sep}WinSecurityEvent.json")

    win_event_df = pd.read_json(StringIO(w_evt.decode("utf-8")))

    # Create criteria for events that we're interested in
    acct_sel = win_event_df["subcategory"] == "User Account Management"
    group_sel = win_event_df["subcategory"] == "Security Group Management"
    schtask_sel = (win_event_df["subcategory"] == "Other Object Access Events") & (
        win_event_df["description"].str.contains("scheduled task")
    )

    event_list = win_event_df[acct_sel | group_sel | schtask_sel]["event_id"].to_list()
    # Add Service install event
    event_list.append(7045)
    return event_data[event_data["EventID"].isin(event_list)]


def _create_acct_event_pivot(account_event_data):
    # Create a pivot of Event vs. Account
    if account_event_data.empty:
        return None
    win_events_acc = account_event_data[["Account", "Activity", "TimeGenerated"]].copy()
    win_events_acc = win_events_acc.replace("-\\-", "No Account").replace(
        {"Account": ""}, value="No Account"
    )
    win_events_acc["Account"] = win_events_acc.apply(
        lambda x: x.Account.split("\\")[-1], axis=1
    )

    return (
        pd.pivot_table(
            win_events_acc,
            values="TimeGenerated",
            index=["Activity"],
            columns=["Account"],
            aggfunc="count",
        )
        .fillna(0)
        .reset_index()
    )


@set_text(docs=_CELL_DOCS, key="display_acct_event_pivot")
def _display_acct_event_pivot(event_pivot_df):
    display(
        event_pivot_df.style.map(lambda x: "color: white" if x == 0 else "")
        .map(
            lambda x: "background-color: lightblue"
            if not isinstance(x, str) and x > 0
            else ""
        )
        .set_properties(subset=["Activity"], **{"width": "400px", "text-align": "left"})
        .highlight_max(axis=1)
        .hide(axis="index")
    )


@set_text(docs=_CELL_DOCS, key="display_acct_mgmt_timeline")
def _display_acct_mgmt_timeline(acct_event_data):
    # Plot events on a timeline
    return display_timeline(
        data=acct_event_data,
        group_by="EventID",
        source_columns=["Activity", "Account"],
        legend="right",
    )
