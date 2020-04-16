# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""host_summary - handles reading noebooklets modules."""
import pkgutil
import os
from typing import Any, Optional, Iterable, Union
from defusedxml import ElementTree
from defusedxml.ElementTree import ParseError

import attr
import bokeh
from IPython.display import display
import numpy as np
import pandas as pd
from msticpy.nbtools import nbdisplay
from msticpy.common.utility import md

from ...common import TimeSpan, NotebookletException
from ...notebooklet import Notebooklet, NotebookletResult, NBMetaData

from ..._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


@attr.s(auto_attribs=True)
class WinHostEventsResult(NotebookletResult):
    """
    Windows Host Security Events Results.

    Attributes
    ----------
    all_events : pd.DataFrame
    event_pivot : pd.DataFrame
    account_events : pd.DataFrame
    account_timeline : bokeh.plotting.figure
    related_bookmarks: pd.DataFrame

    """

    all_events: pd.DataFrame = None
    event_pivot: pd.DataFrame = None
    account_events: pd.DataFrame = None
    account_timeline: bokeh.plotting.figure = None
    expanded_events: pd.DataFrame = None


class WinHostEvents(Notebooklet):
    """

    Windows host Security Events Notebooklet class.

    Notes
    -----
    Queries and displays Windows Security Events including:
    - All security events summary
    - Extracting and displaying account management events
    - Account management event timeline
    - Optionally parsing packed event data into DataFrame columns

    """

    metadata = NBMetaData(
        name=__name__,
        description="Window security events summary",
        options=["event_pivot", "expand_events", "acct_events"],
        default_options=["event_pivot", "acct_events"],
        keywords=["host", "computer", "events", "windows", "account"],
        entity_types=["host"],
        req_providers=["azure_sentinel"],
    )

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
            Timespan for queries
        options : Optional[Iterable[str]], optional
            List of options to use, by default None
            A value of None means use default options.

        Returns
        -------
        HostSummaryResult
            Result object with attributes for each result type.

        Raises
        ------
        NotebookletException
            If required parameters are missing

        """
        super().run(
            value=value, data=data, timespan=timespan, options=options, **kwargs
        )

        if not value:
            raise NotebookletException("parameter 'value' is required.")
        if not timespan:
            raise NotebookletException("parameter 'timespan' is required.")

        result = WinHostEventsResult()

        all_events_df, event_pivot_df = _get_win_security_events(
            self.query_provider, host_name=value, timespan=timespan
        )
        result.all_events = all_events_df
        result.event_pivot = event_pivot_df

        if "event_pivot" in self.options:
            _display_event_pivot(event_pivot=event_pivot_df)

        if "acct_events" in self.options:
            result.account_events = _extract_acct_mgmt_events(event_data=all_events_df)
            result.account_timeline = _display_acct_mgmt_timeline(
                acct_event_data=result.account_events
            )

        if "expand_events" in self.options:
            result.expanded_events = _parse_eventdata(all_events_df)

        self._last_result = result
        return self._last_result

    def expand_events(self, event_ids: Optional[Union[int, Iterable[int]]] = None):
        """
        Expand `eventdata` column into separate properties.

        Parameters
        ----------
        event_ids : Optional[Union[int, Iterable[int]]], optional
            Single or interable of eventid ints, by default None

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
        if not self._last_result or self._last_result.all_events is None:  # type: ignore
            print(
                "Please use 'run()' before using this method.",
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
    md(f"Collecting Windows Event Logs for {host_name}.")
    md("This may take a few minutes...")

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


def _display_event_pivot(event_pivot):
    md("Yellow highlights indicate account with highest event count")
    display(
        event_pivot.style.applymap(lambda x: "color: white" if x == 0 else "")
        .applymap(
            lambda x: "background-color: lightblue"
            if not isinstance(x, str) and x > 0
            else ""
        )
        .set_properties(subset=["Activity"], **{"width": "400px", "text-align": "left"})
        .highlight_max(axis=1)
        .hide_index()
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
        .dropna(axis=1, how="all")
        .fillna("")
    )


def _parse_eventdata(event_data, event_ids: Optional[Union[int, Iterable[int]]] = None):
    if event_ids:
        if isinstance(event_ids, int):
            event_ids = [event_ids]
        eventdata = event_data[event_data["EventID"].isin(event_ids)]

    # Parse event properties into a dictionary
    eventdata["EventProperties"] = eventdata.apply(_parse_event_data_row, axis=1)
    return _expand_event_properties(eventdata)


# %%
# Account management events
def _extract_acct_mgmt_events(event_data):
    # Get a full list of Windows Security Events

    w_evt = pkgutil.get_data("msticpy", f"resources{os.sep}WinSecurityEvent.json")
    win_event_df = pd.read_json(w_evt)

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


def _display_acct_mgmt_timeline(acct_event_data):
    # Plot events on a timeline
    return nbdisplay.display_timeline(
        data=acct_event_data,
        group_by="EventID",
        source_columns=["Activity", "Account"],
        legend="right",
    )
