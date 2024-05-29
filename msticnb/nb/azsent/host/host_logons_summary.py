# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""logons_summary - provides overview of host logon events."""
import re
from math import pi
from typing import Any, Dict, Iterable, Optional, Union

import pandas as pd
from bokeh.io import output_notebook
from bokeh.palettes import viridis  # pylint: disable=no-name-in-module
from bokeh.plotting import figure, show
from bokeh.transform import cumsum
from IPython.display import display
from msticpy.common.timespan import TimeSpan
from msticpy.common.utility import md

try:
    from msticpy.vis import timeline
    from msticpy.vis.foliummap import FoliumMap
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.nbtools import timeline
    from msticpy.nbtools.foliummap import FoliumMap

from ...._version import VERSION
from ....common import MsticnbMissingParameterError, nb_data_wait, nb_print, set_text
from ....nb_metadata import read_mod_metadata
from ....nblib.azsent.host import verify_host_name
from ....notebooklet import NBMetadata, Notebooklet, NotebookletResult

pd.options.mode.chained_assignment = None

__version__ = VERSION
__author__ = "Pete Bryan"


_CLS_METADATA: NBMetadata
_CELL_DOCS: Dict[str, Any]
_CLS_METADATA, _CELL_DOCS = read_mod_metadata(__file__, __name__)


# pylint: disable=too-few-public-methods
class HostLogonsSummaryResult(NotebookletResult):
    """
    Host Logons Summary Results.

    Attributes
    ----------
    logon_sessions: pd.DataFrame
        A Dataframe summarizing all sucessfull and failed logon attempts
        observed during the specified time period.

    logon_map: FoliumMap
        A map showing remote logon attempt source locations. Red points
        represent failed logons, green successful.

    plots: Dict
        A collection of Bokeh plot figures showing various aspects of observed logons.
        Keys are a descriptive name of the plot and values are the plot figures.

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
        self.logon_sessions: Optional[pd.DataFrame] = None
        self.logon_matrix: Optional[pd.DataFrame] = None
        self.logon_map: Optional[FoliumMap] = None
        self.timeline: Optional[figure] = None
        self.failed_success: Optional[pd.DataFrame] = None
        self.plots: Optional[Dict[str, figure]] = None


class HostLogonsSummary(Notebooklet):  # pylint: disable=too-few-public-methods
    """
    Host Logons Summary Notebooket class.

    Queries and displays information about logons to a host including:

    - Summary of sucessfull logons
    - Visualizations of logon event times
    - Geolocation of remote logon sources
    - Visualizations of various logon elements depending on host type
    - Data on users with failed and sucessful logons

    """

    metadata = _CLS_METADATA

    @set_text(docs=_CELL_DOCS, key="run")  # noqa: MC0001, C901
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    def run(  # noqa:MC0001, C901
        self,
        value: Any = None,
        data: Optional[pd.DataFrame] = None,
        timespan: Optional[TimeSpan] = None,
        options: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> HostLogonsSummaryResult:
        """
        Return host summary data.

        Parameters
        ----------
        value : str
            Host name
        data : Optional[pd.DataFrame], optional
            Optionally pass raw data to use for analysis, by default None
        timespan : TimeSpan
            Timespan over which operations such as queries will be
            performed, by default None.
            This can be a TimeStamp object or another object that
            has valid `start`, `end`, or `period` attributes.
            Alternatively you can pass `start` and `end` datetime objects.
        options : Optional[Iterable[str]], optional
            List of options to use, by default None
            A value of None means use default options.

        Returns
        -------
        HostLogonsSummaryResults
            Result object with attributes for each result type.

        Raises
        ------
        MsticnbMissingParameterError
            If required parameters are missing

        MsticnbDataProviderError
            If data is not avaliable

        """
        super().run(
            value=value, data=data, timespan=timespan, options=options, **kwargs
        )

        # Check we have at either a dataset or a host_name and timespan
        if not (data is not None or (value is not None and timespan is not None)):
            raise MsticnbMissingParameterError("data, or a hostname and timespan.")

        # If data is not provided use host_name and timespan to get data
        if not isinstance(data, pd.DataFrame) or data.empty and timespan:
            nb_data_wait(f"{value}")
            host_verif = verify_host_name(
                qry_prov=self.query_provider, timespan=timespan, host_name=value
            )
            if host_verif.host_names:
                nb_print(f"Could not obtain unique host name from {value}. Aborting.")
                return self._last_result
            if not host_verif.host_name:
                nb_print(
                    f"Could not find event records for host {value}. "
                    + "Results may be unreliable."
                )
                # return self._last_result
            host_type = host_verif.host_type or None
            host_name = host_verif.host_name or value

            if host_type == "Windows" or not host_type == "Linux":
                # If no known data type try Windows
                data = self.query_provider.WindowsSecurity.list_all_logons_by_host(  # type: ignore
                    host_name=host_name, start=timespan.start, end=timespan.end  # type: ignore
                )
            else:
                data = self.query_provider.LinuxSyslog.list_logons_for_host(  # type: ignore
                    host_name=host_name, start=timespan.start, end=timespan.end  # type: ignore
                )
        else:
            # If data is provided do some required formatting
            data = _format_raw_data(data)

        # Add description to results for context
        self._last_result = HostLogonsSummaryResult(
            notebooklet=self, description=self.metadata.description, timespan=timespan
        )

        # Check we have data
        if not isinstance(data, pd.DataFrame) or data.empty:
            print("No valid data avaliable.")
            return self._last_result

        # Conduct analysis and get visualizations
        nb_print("Performing analytics and generating visualizations")
        logon_sessions_df = data[data["LogonResult"] != "Unknown"]

        if "timeline" in self.options:
            tl_plot = _gen_timeline(data, self.silent)
            self._last_result.timeline = tl_plot

        if "map" in self.options:
            logon_map = _map_logons(data, self.silent)
            self._last_result.logon_map = logon_map
        logon_matrix = _logon_matrix(data, self.silent)
        if "charts" in self.options:
            pie = _users_pie(data, self.silent)
            stack_bar = _process_stack_bar(data, self.silent)
            charts = {"User Pie Chart": pie, "Process Bar Chart": stack_bar}
            self._last_result.plots = charts
        if "failed_success" in self.options:
            failed_success_df = _failed_success_user(data, self.silent)
            self._last_result.failed_success = failed_success_df

        self._last_result.logon_sessions = logon_sessions_df
        self._last_result.logon_matrix = logon_matrix

        return self._last_result
        # pylint: enable=too-many-locals, too-many-branches


@set_text(docs=_CELL_DOCS, key="logons_timeline")
def _gen_timeline(data: pd.DataFrame, silent: bool):
    if silent:
        return timeline.display_timeline(
            data[data["LogonResult"] != "Unknown"],
            group_by="LogonResult",
            source_columns=[
                "Account",
                "LogonProcessName",
                "SourceIP",
                "LogonTypeName",
                "LogonResult",
            ],
            hide=True,
            title="Logon Events Over Time - Grouped by Result.",
        )

    return timeline.display_timeline(
        data[data["LogonResult"] != "Unknown"],
        group_by="LogonResult",
        source_columns=[
            "Account",
            "LogonProcessName",
            "SourceIP",
            "LogonTypeName",
            "LogonResult",
        ],
        title="Logon Events Over Time - Grouped by Result.",
    )


@set_text(docs=_CELL_DOCS, key="show_map")
def _map_logons(data: pd.DataFrame, silent: bool) -> FoliumMap:
    """Produce a map of source IP logon locations."""
    map_data = data[~(data["IpAddress"].isin(["-", "::1", "", "NaN"]))]
    if not isinstance(map_data, pd.DataFrame) or map_data.empty:
        if not silent:
            md("No plottable logins available")
        return None
    if not silent:
        display(
            map_data.mp_plot.folium_map(
                ip_column="IpAddress", layer_column="LogonResult"
            )
        )

    return map_data.mp_plot.folium_map(
        ip_column="IpAddress", layer_column="LogonResult"
    )


@set_text(docs=_CELL_DOCS, key="show_pie")
def _users_pie(data: pd.DataFrame, silent: bool) -> figure:
    """Produce pie chart based on observance of user names in data."""
    output_notebook()
    user_logons = (
        data["Account"]
        .value_counts()
        .head(20)
        .reset_index(name="value")
        .rename(columns={"index": "Account"})
    )
    # Exclude blank user names as Linux data can be skewed by this
    if "" in user_logons:
        user_logons.drop("", inplace=True)
    user_logons["angle"] = user_logons["value"] / user_logons["value"].sum() * 2 * pi
    user_logons["color"] = viridis(len(user_logons))

    viz = figure(
        height=350,
        title="20 most prevelent users",
        toolbar_location=None,
        tools="hover",
        tooltips="@Account: @value",
        x_range=(-0.5, 1.0),
    )

    viz.wedge(
        x=0,
        y=1,
        radius=0.4,
        start_angle=cumsum("angle", include_zero=True),
        end_angle=cumsum("angle"),
        line_color="white",
        fill_color="color",
        legend_field="Account",
        source=user_logons,
    )

    viz.axis.axis_label = None
    viz.axis.visible = False
    viz.grid.grid_line_color = None

    if not silent:
        show(viz)

    return viz


# pylint: disable=too-many-locals
@set_text(docs=_CELL_DOCS, key="show_process")
def _process_stack_bar(data: pd.DataFrame, silent: bool) -> figure:
    """Produce stacked bar chart showing logon result by process."""
    proc_list = data["LogonTypeName"].unique()
    s_data = []
    f_data = []
    procs = []
    for process in proc_list:
        procs.append(process)
        proc_events = data[data["LogonTypeName"] == process][
            "LogonResult"
        ].value_counts()
        try:
            s_count = proc_events["Success"]
        except KeyError:
            s_count = 0
        try:
            f_count = proc_events["Failure"]
        # Catch error caused if one type of logon result is missing
        except KeyError:
            f_count = 0
        # Convert counts to a percentage to get a more useful output
        if (s_count + f_count) > 0:
            s_per = (s_count / (f_count + s_count)) * 100
            f_per = 100 - s_per
            s_data.append(s_per)
            f_data.append(f_per)
        else:
            procs.remove(process)
    processes = procs
    results = ["Success", "Failure"]
    colors = ["#536d4c", "#832828"]

    graph_data = {"processes": procs, "Success": s_data, "Failure": f_data}

    viz = figure(
        x_range=processes,
        height=350,
        title="Logon Result % by Logon Type",
        toolbar_location=None,
        tools="hover",
        tooltips="@processes $name: @$name%",
    )

    viz.vbar_stack(
        results,
        x="processes",
        width=0.75,
        color=colors,
        source=graph_data,
        legend_label=results,
    )

    viz.y_range.start = 0  # type: ignore[attr-defined]
    viz.x_range.range_padding = 0.1  # type: ignore[attr-defined]
    viz.xgrid.grid_line_color = None  # type: ignore[attr-defined]
    viz.axis.minor_tick_line_color = None
    viz.yaxis.axis_label = "% of logons"
    viz.xaxis.axis_label = "Process name"  # type: ignore[assignment]
    viz.outline_line_color = None  # type: ignore[assignment]
    viz.legend.location = "top_left"
    viz.legend.orientation = "horizontal"

    if not silent:
        show(viz)

    return viz


# pylint: enable=too-many-locals


@set_text(docs=_CELL_DOCS, key="logon_matrix")
def _logon_matrix(data: pd.DataFrame, silent: bool) -> pd.DataFrame:
    """Produce DataFrame showing logons grouped by user and process."""
    print(data.columns)
    logon_by_type = (
        data[(data["Account"] != "") & (data["LogonResult"] != "Unknown")][  # type: ignore
            ["Account", "LogonTypeName", "LogonResult", "TimeGenerated"]
        ]
        .groupby(["Account", "LogonTypeName", "LogonResult"])
        .count()
        .unstack()
        .sort_values(by=[("TimeGenerated", "Success")])
        .rename(columns={"EventID": "LogonCount"})
        .fillna(0)
        .style.background_gradient(cmap="viridis", low=0.5, high=0)
        .format("{0:0>3.0f}")
    )
    if not silent:
        display(logon_by_type)
    return logon_by_type


@set_text(docs=_CELL_DOCS, key="show_df")
def _failed_success_user(data: pd.DataFrame, silent: bool) -> pd.DataFrame:
    failed_logons = data[(data["LogonResult"] == "Failure") & (data["Account"] != "")]
    host_logons = data[(data["LogonResult"] == "Success") & (data["Account"] != "")]
    combined = host_logons[
        host_logons["Account"].isin(failed_logons["Account"].drop_duplicates())
    ]

    if not silent:
        if combined.empty:
            nb_print("No accounts with both a successful and failed logon on.")
        else:
            display(combined)
    return combined


def _win_remote_ip(row: pd.Series) -> str:
    """Return remote IP address from Windows log if logon type is remote."""
    return row["IpAddress"] if row["LogonType"] == 3 else "NaN"


def _format_raw_data(data: pd.DataFrame) -> pd.DataFrame:
    """Populate required fields in DataFrame if they aren not included."""
    if "SourceSystem" in data.columns and data["SourceSystem"].iloc[0] == "Linux":
        if "LogonResult" not in data.columns:
            data["LogonResult"] = data.apply(_get_logon_result_lx, axis=1)
            data["Account"] = data.apply(_parse_user_lx, axis=1)
            data["SourceIP"] = data.apply(_parse_ip_lx, axis=1)
        if "LogonProcessName" not in data.columns:
            data.rename(columns={"ProcessName": "LogonProcessName"})
        if "LogonTypeName" not in data.columns:
            data["LogonTypeName"] = data["LogonProcessName"]
    elif "SubjectUserSid" in data.columns:
        if "LogonResult" not in data.columns:
            data["LogonResult"] = data.apply(_event_id_to_result, axis=1)
            data["SourceIP"] = data.apply(_win_remote_ip, axis=1)
    return data


def _get_logon_result_lx(row: pd.Series) -> str:
    """Identify if a Linux syslog event is for a sucessful or failed logon."""
    failure_events = row.str.contains(
        """failure|failed|invalid|unable to negotiate|authentication failures|did not receive identification|bad protocol version identification|^Connection closed .* [preauth]""",  # pylint: disable=line-too-long
        regex=True,
    )

    success_events = row.str.contains("Accepted|Successful", regex=True)
    if failure_events["SyslogMessage"] is True:
        return "Failure"
    return "Success" if success_events["SyslogMessage"] is True else "Unknown"


def _parse_user_lx(row: pd.Series) -> Union[str, Any, None]:
    """Extract a user name from Syslog message related to a logon."""
    if row.str.contains("publickey")["SyslogMessage"] is True:
        regex = re.compile("for ([^ ]*)")
        user = re.search(regex, row["SyslogMessage"])
        return user[1] if user else None

    regex = re.compile("user |user= ([^ ]*)")
    user = re.search(regex, row["SyslogMessage"])
    return user[1] if user else None


def _parse_ip_lx(row: pd.Series) -> Union[str, Any, None]:
    """Extract an IP Address from an Syslog message."""
    regex = re.compile("((?:[0-9]{1,3}\\.){3}[0-9]{1,3})")
    ips = re.search(regex, row["SyslogMessage"])
    return ips[1] if ips else None


def _event_id_to_result(row: pd.Series):
    """Transform Windows event id to string for logon results."""
    if row["EventID"] == 4624:
        return "Success"
    return "Failure" if row["EventID"] == 4625 else "Unknown"
