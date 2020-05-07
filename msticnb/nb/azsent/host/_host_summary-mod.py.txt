# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""host_summary - experimental module."""
from functools import lru_cache
from typing import Any, Optional, Iterable, List, Tuple, Union

import attr
import pandas as pd
from azure.common.exceptions import CloudError
from msticpy.data import QueryProvider
from msticpy.nbtools import nbdisplay
from msticpy.nbtools import entities
from msticpy.sectools.ip_utils import convert_to_ip_entities, populate_host_entity
from msticpy.common.utility import md

from ....common import (
    TimeSpan,
    NotebookletException,
    print_data_wait,
    print_status,
    set_text,
)
from ....notebooklet import NotebookletResult, NBMetaData
from ....data_providers import DataProviders

from ...._version import VERSION

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


# Problem!
data_prov = DataProviders()
qry_prov = data_prov.providers["azure_sentinel"]
ti_lookup = data_prov.providers["ti_lookup"]
geoip = data_prov.providers["geolite_lookup"]
azure_api = data_prov.providers.get("azure_api", None)

metadata = NBMetaData(
    name=__name__,
    description="Host summary",
    options=["heartbeat", "azure_net", "alerts", "bookmarks", "azure_api"],
    default_options=["heartbeat", "azure_net", "alerts", "bookmarks", "azure_api"],
    keywords=["host", "computer", "heartbeat", "windows", "linux"],
    entity_types=["host"],
    req_providers=["azure_sentinel"],
)


def run(
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
    del data
    if not value:
        raise NotebookletException("parameter 'value' is required.")
    if not timespan:
        raise NotebookletException("parameter 'timespan' is required.")

    if not options:
        options = metadata.default_options

    result = HostSummaryResult(description="Host Summary")

    host_name, verified = _verify_host_name(qry_prov, timespan, value)
    if not verified:
        if isinstance(host_name, list):
            md(f"Could not obtain unique host name from {value}. Aborting.")
            return result
        md(
            f"Could not find event records for host {value}. "
            + "Results may be unreliable.",
            "orange",
        )
    host_name = host_name or value

    host_entity = entities.Host(HostName=host_name)
    if "heartbeat" in options:
        host_entity = get_heartbeat(qry_prov, host_name)
    if "azure_net" in options:
        host_entity = host_entity or entities.Host(HostName=host_name)
        get_aznet_topology(
            qry_prov, host_entity=host_entity, host_name=host_name
        )
    # If azure_details flag is set, an encrichment provider is given,
    # and the resource is an Azure host get resource details from Azure API
    if (
        "azure_api" in options
        and "azure_api" in globals()
        and host_entity.Environment == "Azure"
    ):
        azure_details = _azure_api_details(
            azure_api, host_entity
        )
        if azure_details:
            host_entity.AzureDetails["ResourceDetails"] = azure_details[
                "resoure_details"
            ]
            host_entity.AzureDetails["SubscriptionDetails"] = azure_details[
                "sub_details"
            ]
    _show_host_entity(host_entity)
    if "alerts" in options:
        related_alerts = _get_related_alerts(
            qry_prov, timespan, host_name
        )
        _show_alert_timeline(related_alerts)
    if "bookmarks" in options:
        related_bookmarks = _get_related_bookmarks(
            qry_prov, timespan, host_name
        )

    result.host_entity = host_entity
    result.related_alerts = related_alerts
    result.related_bookmarks = related_bookmarks

    return result


# Get Azure Resource details from API
@lru_cache()
def _azure_api_details(az_cli, host_record):
    try:
        # Get subscription details
        sub_details = az_cli.get_subscription_info(
            host_record.AzureDetails["SubscriptionId"]
        )
        # Get resource details
        resource_details = az_cli.get_resource_details(
            resource_id=host_record.AzureDetails["ResourceId"],
            sub_id=host_record.AzureDetails["SubscriptionId"],
        )
        # Get details of attached disks and network interfaces
        disks = [
            disk["name"]
            for disk in resource_details["properties"]["storageProfile"]["dataDisks"]
        ]
        network_ints = [
            net["id"]
            for net in resource_details["properties"]["networkProfile"][
                "networkInterfaces"
            ]
        ]
        image = (
            str(
                resource_details["properties"]["storageProfile"]["imageReference"][
                    "offer"
                ]
            )
            + " "
            + str(
                resource_details["properties"]["storageProfile"]["imageReference"][
                    "sku"
                ]
            )
        )
        # Extract key details and add host_entity
        resource_details = {
            "Azure Location": resource_details["location"],
            "VM Size": resource_details["properties"]["hardwareProfile"]["vmSize"],
            "Image": image,
            "Disks": disks,
            "Admin User": resource_details["properties"]["osProfile"]["adminUsername"],
            "Network Interfaces": network_ints,
            "Tags": str(resource_details["tags"]),
        }
        azure_result = {"resoure_details": resource_details, "sub_details": sub_details}

        return azure_result
    except CloudError:
        return None


# %%
# Get heartbeat
@lru_cache()
def _verify_host_name(
    qry_prov, timespan, host_name
) -> Tuple[Union[str, List[str]], bool]:

    host_names: List[str] = []
    # Get single event - try process creation
    if "SecurityEvent" in qry_prov.schema_tables:
        sec_event_host = """
            SecurityEvent
            | where TimeGenerated between (datetime({start})..datetime({end}))
            | where Computer contains "{host}"
            | distinct Computer
             """
        print_data_wait("SecurityEvent")
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
            | where TimeGenerated between (datetime({start})..datetime({end}))
            | where Computer contains "{host}"
            | distinct Computer
            """
        print_data_wait("Syslog")
        lx_hosts_df = qry_prov.exec_query(
            syslog_host.format(start=timespan.start, end=timespan.end, host=host_name)
        )
        if lx_hosts_df is not None and not lx_hosts_df.empty:
            host_names.extend(lx_hosts_df["Computer"].to_list())

    if len(host_names) > 1:
        print(
            f"Multiple matches for '{host_name}'.",
            "Please select a specific host and re-run.",
            "\n".join(host_names),
        )
        return ", ".join(host_names), False
    if host_names:
        print(f"Unique host found: {host_names[0]}")
        return host_names[0], True

    print(f"Host not found: {host_name}")
    return host_name, False


# %%
# Get IP Information from Heartbeat
@lru_cache()
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
    if "Heartbeat" in qry_prov.schema_tables:
        print_data_wait("Heartbeat")
        host_hb_df = None
        if host_name:
            host_hb_df = qry_prov.Network.get_heartbeat_for_host(host_name=host_name)
        elif host_ip:
            host_hb_df = qry_prov.Network.get_heartbeat_for_ip(ip_address=host_ip)
        if host_hb_df is not None and not host_hb_df.empty:
            host_entity = populate_host_entity(heartbeat_df=host_hb_df)

    return host_entity


# %%
# Get IP Information from Azure Network Topology
@lru_cache()
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
        print_data_wait("AzureNetworkAnalytics")
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


@set_text(
    title="Host Entity details",
    text="""
These are the host entity details gathered from Heartbeat
and, if applicable, AzureNetworkAnalytics and Azure management
API.

The data shows OS information, IP Addresses assigned the
host and any Azure VM information available.
""",
    md=True,
)
def _show_host_entity(host_entity):
    print(host_entity)


# %%
# Get related alerts
@lru_cache()
def _get_related_alerts(qry_prov, timespan, host_name):
    related_alerts = qry_prov.SecurityAlert.list_related_alerts(
        timespan, host_name=host_name
    )

    if not related_alerts.empty:
        host_alert_items = (
            related_alerts[["AlertName", "TimeGenerated"]]
            .groupby("AlertName")
            .TimeGenerated.agg("count")
        )
        print_status(
            f"Found {len(related_alerts)} related alerts ({len(host_alert_items)}) types"
        )
    else:
        print_status("No related alerts found.")
    return related_alerts


@set_text(
    title="Timeline of related alerts",
    text="""
Each marker on the timeline indicates one or more alerts related to the host
"""
)
def _show_alert_timeline(related_alerts):
    if len(related_alerts) > 1:
        nbdisplay.display_timeline(
            data=related_alerts,
            title="Related Alerts",
            source_columns=["AlertName", "TimeGenerated"],
            height=200,
        )


@lru_cache()
def _get_related_bookmarks(qry_prov, timespan, host_name):
    print_data_wait("Bookmarks")
    host_bkmks = qry_prov.AzureSentinel.list_bookmarks_for_entity(
        timespan, entity_id=f"'{host_name}'"
    )

    if not host_bkmks.empty:
        print_status(f"{len(host_bkmks)} investigation bookmarks found for this host.")
    else:
        print_status("No bookmarks found.")
    return host_bkmks
