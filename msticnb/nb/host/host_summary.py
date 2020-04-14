# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""host_summary - handles reading noebooklets modules."""
from typing import Any, Optional, Iterable, List, Tuple

import attr
import pandas as pd
from msticpy.data import QueryProvider
from msticpy.nbtools import nbwidgets, nbdisplay
from msticpy.nbtools import entities
from msticpy.sectools.ip_utils import convert_to_ip_entities, create_ip_record
from msticpy.common.utility import md

from ...common import TimeSpan, NotebookletException
from ...notebooklet import Notebooklet, NotebookletResult, NBMetaData

from ..._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


@attr.s(auto_attribs=True)
class HostSummaryResult(NotebookletResult):
    """
    Host Details Results.

    Attributes
    ----------
    host_entity : msticpy.data.nbtools.entities.Host
    related_alerts : pd.DataFrame
    related_bookmarks: pd.DataFrame

    """

    host_entity: entities.Host = None
    related_alerts: pd.DataFrame = None
    related_bookmarks: pd.DataFrame = None


class HostSummary(Notebooklet):
    """

    HostSummary Notebooklet class.

    Notes
    -----
    Queries and displays information about a host including:
    - IP address assignment
    - Related alerts
    - Related hunting/investigation bookmarks
    - Azure subscription/resource data.

    """

    metadata = NBMetaData(
        name=__name__,
        description="Host summary",
        options=["heartbeat", "azure_net", "alerts", "bookmarks", "azure_data"],
        default_options=["heartbeat", "azure_net", "alerts", "bookmarks", "azure_data"],
        keywords=["host", "computer", "heartbeat", "windows", "linux"],
        entity_types=["host"],
    )

    def run(
        self,
        value: Any = None,
        data: Optional[pd.DataFrame] = None,
        timespan: Optional[TimeSpan] = None,
        options: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> HostSummaryResult:
        """
        Return host summary data.

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

        host_name, verified = _verify_host_name(self.query_provider, timespan, value)
        if not verified:
            md(f"Could not verify host name {value}. Results may not be reliable.")

        host_entity = None
        if "heartbeat" in self.options:
            host_entity = get_heartbeat(self.query_provider, host_name)
        if "azure_net" in self.options:
            host_entity = host_entity or entities.Host(HostName=host_name)
            get_aznet_topology(
                self.query_provider, host_entity=host_entity, host_name=host_name
            )
        if "alerts" in self.options:
            related_alerts = _get_related_alerts(
                self.query_provider, timespan, host_name
            )

        if "bookmarks" in self.options:
            related_bookmarks = _get_related_bookmarks(
                self.query_provider, timespan, host_name
            )

        self._last_result = HostSummaryResult(
            description="Host Summary",
            host_entity=host_entity,
            related_alerts=related_alerts,
            related_bookmarks=related_bookmarks,
        )
        return self._last_result


# %%
# Get heartbeat
def _verify_host_name(qry_prov, timespan, host_name) -> Tuple[str, bool]:

    host_names: List[str] = []
    # Get single event - try process creation
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
            host_names.extend(win_hosts_df["Computer"].to_list())

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
            host_names.extend(lx_hosts_df["Computer"].to_list())

    if len(host_names) > 1:
        print(
            f"Multiple matches for '{host_name}'.",
            "Please select a host from the list.",
        )
        host_select = nbwidgets.SelectString(
            item_list=list(host_names),
            description="Select the host.",
            auto_display=True,
        )
        return host_select, True
    if not host_names:
        print(f"Unique host found: {host_names[0]}")
        return host_names[0], True

    print(f"Host not found: {host_name}")
    return host_name, False


# %%
# Get IP Information
def get_heartbeat(
    qry_prov: QueryProvider, host_name: str = None, host_ip: str = None
) -> entities.Host:
    """
    Get Heartbeat information for host or IP.

    Parameters
    ----------
    qry_prov : QueryProvider
        Query provider to use for queries
    host_name : str, optional
        Host name, by default None
    host_ip : str, optional
        Host IP Address, by default None

    Returns
    -------
    Host
        Host entity

    """
    host_entity = entities.Host(HostName=host_name)
    if "HeartBeat" in qry_prov.schema_tables:
        print(f"Looking for {host_name or host_ip} in OMS Heartbeat data...")
        host_hb_df = None
        if host_name:
            host_hb_df = qry_prov.Network.get_heartbeat_for_host(host_name=host_name)
        elif host_ip:
            host_hb_df = qry_prov.Network.get_heartbeat_for_ip(ip_address=host_ip)
        if host_hb_df is not None and not host_hb_df.empty:
            host_hb = host_hb_df.iloc[0]
            host_entity = entities.Host(host_hb)
            host_entity.SourceComputerId = host_hb["SourceComputerId"]
            host_entity.OSType = host_hb["OSType"]
            host_entity.OSMajorVersion = host_hb["OSMajorVersion"]
            host_entity.OSMinorVersion = host_hb["OSMinorVersion"]
            host_entity.ComputerEnvironment = host_hb["ComputerEnvironment"]
            host_entity.ResourceId = host_hb["ResourceId"]
            host_entity.OmsSolutions = [
                sol.strip() for sol in host_hb["Solutions"].split(",")
            ]
            host_entity.VMUUID = host_hb["VMUUID"]

            host_entity.IPAddress = create_ip_record(heartbeat_df=host_hb_df)

    return host_entity


def get_aznet_topology(
    qry_prov: QueryProvider,
    host_entity: entities.Host,
    host_name: str = None,
    host_ip: str = None,
):
    """
    Get Azure Network topology information for host or IP address.

    Parameters
    ----------
    qry_prov : QueryProvider
        Query provider to use for queries
    host_entity : Host
        Host entity to populate data with
    host_name : str, optional
        Host name, by default None
    host_ip : str, optional
        Host IP Address, by default None

    """
    if "AzureNetworkAnalytics_CL" in qry_prov.schema_tables:
        print(f"Looking for {host_name or host_ip} IP addresses in network flows...")
        if host_name:
            az_net_df = qry_prov.Network.get_ips_for_host(host_name=host_name)
        elif host_ip:
            az_net_df = qry_prov.Network.host_for_ip(ip_address=host_ip)

        if not az_net_df.empty:
            host_entity.private_ips = convert_to_ip_entities(
                az_net_df["PrivateIPAddresses"].iloc[0]
            )
            host_entity.public_ips = convert_to_ip_entities(
                az_net_df["PublicIPAddresses"].iloc[0]
            )
        else:
            if "private_ips" not in host_entity:
                host_entity.private_ips = []
            if "public_ips" not in host_entity:
                host_entity.public_ips = []


# %%
# Get related alerts
def _get_related_alerts(qry_prov, timespan, host_name):
    related_alerts = qry_prov.SecurityAlert.list_related_alerts(
        timespan, host_name=host_name
    )

    if not related_alerts.empty:
        host_alert_items = (
            related_alerts[["AlertName", "TimeGenerated"]]
            .groupby("AlertName")
            .TimeGenerated.agg("count")
            .to_dict()
        )
        md(f"Found {len(host_alert_items)} related alerts", "bold")
        for alert_name, count in host_alert_items:
            md(f"- {alert_name}, ({count} found)")

        if len(related_alerts) > 1:
            nbdisplay.display_timeline(
                data=related_alerts,
                title="Related Alerts",
                source_columns=["AlertName", ""],
                height=200,
            )
    else:
        md("No related alerts found.")
    return related_alerts


def _get_related_bookmarks(qry_prov, timespan, host_name):
    host_bkmks = qry_prov.AzureSentinel.list_bookmarks_for_entity(
        timespan, entity_id=f"'{host_name}'"
    )

    if not host_bkmks.empty:
        md(f"{len(host_bkmks)} investigation bookmarks found for this host.", "bold")
    return host_bkmks
