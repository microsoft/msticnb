# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""logons_summary - provides overview of host logon events."""
from typing import Any, Optional, Iterable, Tuple, Dict
import re
from math import pi

import attr
import pandas as pd
from bokeh.plotting import figure
from bokeh.io import output_notebook
from bokeh.palettes import Category20c
from bokeh.transform import cumsum
from msticpy.data import QueryProvider
from msticpy.nbtools.foliummap import FoliumMap, get_center_ip_entities
from msticpy.sectools.ip_utils import convert_to_ip_entities
from msticpy.nbtools import timeline

from ...common import TimeSpan, NotebookletException
from ...notebooklet import Notebooklet, NotebookletResult, NBMetaData

from ..._version import VERSION

__version__ = VERSION
__author__ = "Pete Bryan"


@attr.s(auto_attribs=True)  # pylint: disable=too-few-public-methods
class HostLogonsSummaryResults(NotebookletResult):

    """
    Host Logons Summary Results.

    Attributes
    ----------
    logon_sessions: pd.DataFrame
    logon_map: FoliumMap
    plots: Dict

    """

    logon_sessions: pd.DataFrame = None
    logon_matrix: pd.DataFrame = None
    logon_map: FoliumMap = None
    timeline: figure = None
    plots: Dict = None


class HostLogonsSummary(Notebooklet):  # pylint: disable=too-few-public-methods

    """
    HostLogonsSummary Notebooklet class.

    Notes
    -----
    Queries and displays information about logons to a host including:
    - Summary of sucessfull logons
    - Visualizations of logon event times
    - Geolocation of remote logon sources
    - Visualizations of various logon elements depending on host type
    - Data on users with failed and sucessful logons

    """

    metadata = NBMetaData(
        name=__name__,
        description="Host Llgons summary",
        options=["map", "timeline", "charts"],
        default_options=["map", "timeline", "charts"],
        keywords=["host", "computer", "logons", "windows", "linux"],
        entity_types=["host"],
        req_providers=["azure_sentinel"],
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
        NotebookletException
            If required parameters are missing

        """
        super().run(
            value=value, data=data, timespan=timespan, options=options, **kwargs
        )

        # Check we have at either a dataset or a host_name and timespan
        if not value and not timespan and not data:
            raise NotebookletException(
                "Either data, or a hostname and timespan is required."
            )

        # Add description to results for context
        self._last_result = HostLogonsSummaryResults(
            description=self.metadata.description
        )

        # If data is not provided use host_name and timespan to get data
        if not data:
            if self.verbose is True:
                print(f"Collecting logon data from {value}")
            host_name_type, verified = _verify_host_name_type(
                self.query_provider, timespan, value
            )
            if not verified:
                print(
                    f"Could not verify unique host name {value}. Results may not be reliable."
                )
                return self._last_result

            host_name = next(iter(host_name_type))
            if list(host_name_type.values())[0] == "Windows":
                data = self.query_provider.WindowsSecurity.list_all_logons_by_host(
                    host_name=host_name, start=timespan.start, end=timespan.end
                )
            else:
                data = self.query_provider.LinuxSyslog.list_logons_for_host(
                    host_name=host_name, start=timespan.start, end=timespan.end
                )
        else:
            # If data is provided do some required formatting
            data = _format_raw_data(data)

        # Check we have data
        if not isinstance(data, pd.DataFrame) or data.empty:
            raise NotebookletException("No valid data avaliable")

        # Conduct analysis and get visualizations
        if self.verbose is True:
            print(f"Performing analytics and generating visualizations")
        logon_sessions_df = data[data["LogonResult"] != "Unknown"]
        logon_matrix = _logon_matrix(data)
        if "map" in self.options:
            logon_map = _map_logons(data)
            self._last_result.logon_map = logon_map
        if "timeline" in self.options:
            tl_plot = timeline.display_timeline(
                data[data["LogonResult"] != "Unknown"],
                group_by="LogonResult",
                source_columns=["Account", "LogonProcessName", "SourceIP"],
                hide=True,
            )
            self._last_result.timeline = tl_plot
        if "charts" in self.options:
            pie = _users_pie(data)
            stack_bar = _process_stack_bar(data)
            charts = {"User Pie Chart": pie, "Process Bar Chart": stack_bar}
            self._last_result.plots = charts

        self._last_result.logon_sessions = logon_sessions_df
        self._last_result.logon_matrix = logon_matrix

        return self._last_result
        # pylint: enable=too-many-locals, too-many-branches


def _verify_host_name_type(
    qry_prov: QueryProvider, timespan: TimeSpan, host_name: str
) -> Tuple[Any, bool]:
    """Verify a host name is valid and get the host type (Linux or Windows)."""
    host_names: Dict = {}
    # Check for Windows hosts matching host_name
    if "SecurityEvent" in qry_prov.schema_tables:
        sec_event_host = """
            SecurityEvent
            | where TimeGenerated between (datetime({start})..datetime({end})
            | where Computer has {host}
            | distinct Computer
             """
        win_hosts_df = qry_prov.exec_query(
            sec_event_host.format(
                start=timespan.start, end=timespan.end, host=host_name
            )
        )
        if win_hosts_df is not None and not win_hosts_df.empty:
            for host in win_hosts_df["Computer"].to_list():
                host_names.update({host: "Windows"})

    # Check for Linux hosts matching host_name
    if "Syslog" in qry_prov.schema_tables:
        syslog_host = """
            Syslog
            | where TimeGenerated between (datetime({start})..datetime({end})
            | where Computer has {host}
            | distinct Computer
            """
        lx_hosts_df = qry_prov.exec_query(
            syslog_host.format(start=timespan.start, end=timespan.end, host=host_name)
        )
        if lx_hosts_df is not None and not lx_hosts_df.empty:
            for host in lx_hosts_df["Computer"].to_list():
                host_names.update({host: "Linux"})

    # If we have more than one host let the user decide
    if len(host_names.keys()) > 1:
        print(
            f"Multiple matches for '{host_name}'.",
            "Please select a host and re-run.",
            "\n".join(host_names.keys()),
        )
        return ", ".join(host_names.keys()), False

    if host_names:
        unique_host = next(iter(host_names))
        print(f"Unique host found: {unique_host}")
        return {unique_host: host_names[unique_host]}, True

    print(f"Host not found: {host_name}")
    return host_name, False


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


def _map_logons(data: pd.DataFrame) -> FoliumMap:
    """Produces a map of source IP logon locations."""
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
    return folium_map


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
    user_logons["color"] = Category20c[len(user_logons)]

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

    return viz


def _process_stack_bar(data: pd.DataFrame) -> figure:
    """Produce stacked bar chart showing logon result by process."""
    proc_list = data["LogonProcessName"].unique()
    s_data = []
    f_data = []
    procs = []
    for process in proc_list:
        procs.append(process)
        proc_events = data[data["LogonProcessName"] == process][
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
            s_per = s_count / (f_count + s_count)
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
        title="Logon Result % by Process",
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

    return viz


def _event_id_to_result(row: pd.Series):
    """Transform Windows event id to string for logon results."""
    if row["EventID"] == 4624:
        return "Success"
    if row["EventID"] == 4625:
        return "Failure"
    return "Unknown"


def _logon_matrix(data: pd.DataFrame) -> pd.DataFrame:
    """Produce DataFrame showing logons grouped by user and process."""
    logon_by_type = (
        data[data["Account"] != ""][["Account", "LogonProcessName", "LogonResult"]]
        .groupby(["Account", "LogonProcessName"])
        .count()
        .unstack()
        .rename(columns={"EventID": "LogonCount"})
        .fillna(0)
        .style.background_gradient(cmap="viridis", low=0.5, high=0)
        .format("{0:0>3.0f}")
    )
    return logon_by_type


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
