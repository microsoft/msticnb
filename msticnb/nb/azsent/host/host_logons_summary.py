# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""logons_summary - provides overview of host logon events."""
from typing import Any, Optional, Iterable, Dict
import re
from math import pi

import attr
import pandas as pd
from bokeh.plotting import figure, show
from bokeh.io import output_notebook
from bokeh.palettes import viridis  # pylint: disable=no-name-in-module
from bokeh.transform import cumsum
from IPython.display import display
from msticpy.nbtools.foliummap import FoliumMap, get_center_ip_entities
from msticpy.sectools.ip_utils import convert_to_ip_entities
from msticpy.nbtools import timeline

from ....common import (
    TimeSpan,
    nb_print,
    MsticnbDataProviderError,
    MsticnbMissingParameterError,
    nb_data_wait,
    set_text,
)
from ....notebooklet import Notebooklet, NotebookletResult, NBMetaData

from ....nblib.azsent.host import verify_host_name

from ...._version import VERSION

pd.options.mode.chained_assignment = None

__version__ = VERSION
__author__ = "Pete Bryan"


@attr.s(auto_attribs=True)  # pylint: disable=too-few-public-methods
class HostLogonsSummaryResults(NotebookletResult):
    """
    Host Logons Summary Results.

    Attributes
    ----------
    logon_sessions: pd.DataFrame
        A Dataframe summarizing all sucessfull and failed logon attempts observed during the
        specified time period.

    logon_map: FoliumMap
        A map showing remote logon attempt source locations. Red points represent failed logons,
        green successful.

    plots: Dict
        A collection of Bokeh plot figures showing various aspects of observed logons.
        Keys are a descriptive name of the plot and values are the plot figures.

    """

    logon_sessions: pd.DataFrame = None
    logon_matrix: pd.DataFrame = None
    logon_map: FoliumMap = None
    timeline: figure = None
    failed_success: pd.DataFrame = None
    plots: Dict = None


class HostLogonsSummary(Notebooklet):  # pylint: disable=too-few-public-methods
    """
    Host Logons Summary Notebooket class.

    Queries and displays information about logons to a host including:

    - Summary of sucessfull logons
    - Visualizations of logon event times
    - Geolocation of remote logon sources
    - Visualizations of various logon elements depending on host type
    - Data on users with failed and sucessful logons

    Default Options
    ---------------
    - map: Display a map of logon attempt locations.
    - timeline: Display a timeline of logon atttempts
    - charts: Display a range of charts depicting different elements of logon events.
    - failed_success: Displays a DataFrame of all users with both successful and failed logons.

    """

    metadata = NBMetaData(
        name=__qualname__,  # type: ignore  # noqa
        mod_name=__name__,
        description="Host Logons summary",
        default_options=["map", "timeline", "charts", "failed_success"],
        keywords=["host", "computer", "logons", "windows", "linux"],
        entity_types=["host"],
        req_providers=["LogAnalytics|LocalData"],
    )

    @set_text(  # noqa:MC0001
        title="Host Logons Summary",
        hd_level=1,
        text="Data and plots are stored in the result class returned by this function",
    )
    # pylint: disable=too-many-locals, too-many-branches
    def run(
        self,
        value: Any = None,
        data: Optional[pd.DataFrame] = None,
        timespan: Optional[TimeSpan] = None,
        options: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> HostLogonsSummaryResults:
        """
        Return host summary data.

        Parameters
        ----------
        value : str
            Host name
        data : Optional[pd.DataFrame], optional
            Optionally pass raw data to use for analysis, by default None
        timespan : TimeSpan
            Timespan for queries
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
        if value is None and timespan is None and data is None:
            raise MsticnbMissingParameterError("data, or a hostname and timespan.")

        # If data is not provided use host_name and timespan to get data
        if data is None:
            nb_data_wait(f"{value}")
            host_name, host_names = verify_host_name(
                qry_prov=self.query_provider, timespan=timespan, host_name=value
            )
            if host_names:
                nb_print(f"Could not obtain unique host name from {value}. Aborting.")
                return self._last_result
            if not host_name:
                nb_print(
                    f"Could not find event records for host {value}. "
                    + "Results may be unreliable."
                )
                return self._last_result
            host_type = host_name[1] or None
            host_name = host_name[0] or value

            if host_type == "Windows":
                data = self.query_provider.WindowsSecurity.list_all_logons_by_host(
                    host_name=host_name, start=timespan.start, end=timespan.end
                )
            elif host_type == "Linux":
                data = self.query_provider.LinuxSyslog.list_logons_for_host(
                    host_name=host_name, start=timespan.start, end=timespan.end
                )
            # If no known data type try Windows
            else:
                data = self.query_provider.WindowsSecurity.list_all_logons_by_host(
                    host_name=host_name, start=timespan.start, end=timespan.end
                )
        else:
            # If data is provided do some required formatting
            data = _format_raw_data(data)

        # Add description to results for context
        self._last_result = HostLogonsSummaryResults(
            description=self.metadata.description
        )

        # Check we have data
        if not isinstance(data, pd.DataFrame) or data.empty:
            raise MsticnbDataProviderError("No valid data avaliable")

        # Conduct analysis and get visualizations
        nb_print(f"Performing analytics and generating visualizations")
        logon_sessions_df = data[data["LogonResult"] != "Unknown"]
        if "timeline" in self.options:
            tl_plot = _gen_timeline(data)
            self._last_result.timeline = tl_plot
        if "map" in self.options:
            logon_map = _map_logons(data)
            self._last_result.logon_map = logon_map
        logon_matrix = _logon_matrix(data)
        if "charts" in self.options:
            pie = _users_pie(data)
            stack_bar = _process_stack_bar(data)
            charts = {"User Pie Chart": pie, "Process Bar Chart": stack_bar}
            self._last_result.plots = charts
        if "failed_success" in self.options:
            failed_success_df = _failed_success_user(data)
            self._last_result.failed_success = failed_success_df

        self._last_result.logon_sessions = logon_sessions_df
        self._last_result.logon_matrix = logon_matrix

        return self._last_result
        # pylint: enable=too-many-locals, too-many-branches


@set_text(
    title="Timeline of logon events",
    text="""
A breakdown of logon attempts over time, split by the logon attempt result.
""",
)
def _gen_timeline(data: pd.DataFrame):
    time_line = timeline.display_timeline(
        data[data["LogonResult"] != "Unknown"],
        group_by="LogonResult",
        source_columns=[
            "Account",
            "LogonProcessName",
            "SourceIP",
            "LogonTypeName",
            "LogonResult",
        ],
    )
    return time_line


@set_text(
    title="Map of logon locations",
    text="""
Red markers show locations of failed signins, green shows sucessful logons.
""",
)
def _map_logons(data: pd.DataFrame) -> FoliumMap:
    """Produce a map of source IP logon locations."""
    # Seperate out failed and sucessful logons and clean the data
    remote_logons = data[data["LogonResult"] == "Success"]
    failed_logons = data[data["LogonResult"] == "Failure"]
    remote_logons.replace("", "NaN", inplace=True)
    failed_logons.replace("", "NaN", inplace=True)
    ip_list = [
        convert_to_ip_entities(ip)[0] for ip in remote_logons["SourceIP"] if ip != "NaN"
    ]
    ip_fail_list = [
        convert_to_ip_entities(ip)[0] for ip in failed_logons["SourceIP"] if ip != "NaN"
    ]
    # Get center point of logons and build map acount that
    location = get_center_ip_entities(ip_fail_list + ip_list)
    folium_map = FoliumMap(location=location, zoom_start=4)
    if len(ip_fail_list) > 0:
        icon_props = {"color": "red"}
        folium_map.add_ip_cluster(ip_entities=ip_fail_list, **icon_props)
    if len(ip_list) > 0:
        icon_props = {"color": "green"}
        folium_map.add_ip_cluster(ip_entities=ip_list, **icon_props)
    display(folium_map)
    return folium_map


@set_text(
    title="User name prevalence",
    text="""
Breakdown of logon attempts obsevered (failed and successful) by user name.
""",
)
def _users_pie(data: pd.DataFrame) -> figure:
    """Produce pie chart based on observence of user names in data."""
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
        plot_height=350,
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
    show(viz)

    return viz


@set_text(
    title="Logon sucess ratio by process",
    text="""
Ratio of failed to sucessful logons by process. Red is failure, green is successful.
""",
)
def _process_stack_bar(data: pd.DataFrame) -> figure:
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

    data = {"processes": procs, "Success": s_data, "Failure": f_data}

    viz = figure(
        x_range=processes,
        plot_height=350,
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
        source=data,
        legend_label=results,
    )

    viz.y_range.start = 0
    viz.x_range.range_padding = 0.1
    viz.xgrid.grid_line_color = None
    viz.axis.minor_tick_line_color = None
    viz.yaxis.axis_label = "% of logons"
    viz.xaxis.axis_label = "Process name"
    viz.outline_line_color = None
    viz.legend.location = "top_left"
    viz.legend.orientation = "horizontal"
    show(viz)

    return viz


@set_text(
    title="Logon Matrix",
    text="""
A breakdown of logons by account, logon type, and result.
""",
)
def _logon_matrix(data: pd.DataFrame) -> pd.DataFrame:
    """Produce DataFrame showing logons grouped by user and process."""
    logon_by_type = (
        data[(data["Account"] != "") & (data["LogonResult"] != "Unknown")][
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
    display(logon_by_type)
    return logon_by_type


@set_text(
    title="Accounts with failed and successful logons",
    text="""Accounts that have at least one successful and one failed logon within the
        timeframe of the notebooklet""",
)
def _failed_success_user(data: pd.DataFrame) -> pd.DataFrame:
    failed_logons = data[(data["LogonResult"] == "Failure") & (data["Account"] != "")]
    host_logons = data[(data["LogonResult"] == "Success") & (data["Account"] != "")]
    combined = host_logons[
        host_logons["Account"].isin(failed_logons["Account"].drop_duplicates())
    ]
    if not combined.empty:
        display(combined)
    else:
        nb_print("No accounts with both a successful and failed logon on.")
    return combined


def _win_remote_ip(row: pd.Series) -> str:
    """Return remote IP address from Windows log if logon type is remote."""
    if row["LogonType"] == 3:
        return row["IpAddress"]
    return "NaN"


def _format_raw_data(data: pd.DataFrame) -> pd.DataFrame:
    """Populate required fields in DataFrame if they aren not included."""
    if "SourceSystem" in data.columns and data["SourceSystem"].iloc[0] == "Linux":
        if "LogonResult" not in data.columns:
            data["LogonResult"] = data.apply(_get_logon_result_lx, axis=1)
            data["Account"] = data.apply(_parse_user_lx, axis=1)
            data["SourceIP"] = data.apply(_parse_ip_lx, axis=1)
        if "LogonProcessName" not in data.columns:
            data.rename(columns={"ProcessName", "LogonProcessName"})
    elif "EventID" and "SubjectUserSid" in data.columns:
        if "LogonResult" not in data.columns:
            data["LogonResult"] = data.apply(_event_id_to_result, axis=1)
            data["SourceIP"] = data.apply(_win_remote_ip, axis=1)
    return data


def _get_logon_result_lx(row: pd.Series) -> str:
    """Identify if a Linux syslog event is for a sucessful or failed logon."""
    failure_events = row.str.contains(
        "failure|failed|invalid|unable to negotiate|authentication failures|did not receive identification|bad protocol version identification|^Connection closed .* [preauth]",  # pylint: disable=line-too-long # noqa
        regex=True,
    )
    success_events = row.str.contains("Accepted|Successful", regex=True)
    if failure_events["SyslogMessage"] is True:
        return "Failure"
    if success_events["SyslogMessage"] is True:
        return "Success"
    return "Unknown"


def _parse_user_lx(row: pd.Series) -> str:
    """Extract a user name from Syslog message related to a logon."""
    if row.str.contains("publickey")["SyslogMessage"] is True:
        regex = re.compile("for ([^ ]*)")
        user = re.search(regex, row["SyslogMessage"])
        return user[1]

    regex = re.compile("user |user= ([^ ]*)")
    user = re.search(regex, row["SyslogMessage"])
    return user[1]


def _parse_ip_lx(row: pd.Series) -> str:
    """Extract an IP Address from an Syslog message."""
    regex = re.compile("((?:[0-9]{1,3}\\.){3}[0-9]{1,3})")
    ips = re.search(regex, row["SyslogMessage"])
    return ips[1]


def _event_id_to_result(row: pd.Series):
    """Transform Windows event id to string for logon results."""
    if row["EventID"] == 4624:
        return "Success"
    if row["EventID"] == 4625:
        return "Failure"
    return "Unknown"
