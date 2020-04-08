# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""host_summary - handles reading noebooklets modules."""
from typing import Any, Optional, Iterable, List, Tuple

import attr
import pandas as pd
from msticpy.nbtools import nbwidgets, nbdisplay
from msticpy.nbtools import entities
from msticpy.sectools import GeoLiteLookup
from msticpy.common.utility import md
from azure.common.exceptions import CloudError

from ...common import (
    Notebooklet,
    NotebookletResult,
    TimeSpan,
    NotebookletException,
    NBMetaData,
)

# __all__ = [HostSummary]


@attr.s(auto_attribs=True)
class HostResult(NotebookletResult):
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
    """HostSummary Notebooklet class."""

    metadata = NBMetaData(
        name=__name__,
        description="Host summary",
        options=["heartbeat", "azure_net", "alerts", "bookmarks"],
        keywords=["host", "computer", "heartbeat", "windows", "linux", "azure"],
        entity_types=["host"],
    )

    def run(
        self,
        value: Any = None,
        data: Optional[pd.DataFrame] = None,
        timespan: Optional[TimeSpan] = None,
        options: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> HostResult:
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
        HostResult
            Result object with attributes for each result type.

        Raises
        ------
        NotebookletException
            If required parameters are missing

        """
        del data

        related_alerts = None
        related_bookmarks = None

        if not value:
            raise NotebookletException("parameter 'value' is required.")
        if not timespan:
            raise NotebookletException("parameter 'timespan' is required.")
        if options:
            self.options = list(options)
        host_name, verified = _verify_host_name(self.query_provider, timespan, value)
        if not verified:
            md(f"Could not verify host name {value}. Results may not be reliable.")

        host_entity = None
        if "heartbeat" in self.options:
            host_entity = _get_heartbeat(self.query_provider, host_name)
        if "azure_net" in self.options:
            host_entity = host_entity or entities.Host(HostName=host_name)
            _get_aznet_topology(
                self.query_provider, host_entity=host_entity, host_name=host_name
            )
        if "alerts" in self.options:
            related_alerts = _get_related_alerts(
                self.query_provider, timespan, host_name
            )
        # If azure_details flag is set, ann encrichment provider is given, and the resource is an Azure host get resource details from Azure API
        if (
            "azure_api" in self.options
            and "azure_data" in self.enrichment_providers
            and host_entity.Environment == "Azure"
        ):
            azure_data = _azure_api_details(
                self.enrichment_providers["azure_data"], host_entity
            )
            if azure_data:
                host_entity.AzureDetails["ResourceDetails"] = azure_data[
                    "resoure_details"
                ]
                host_entity.AzureDetails["SubscriptionDetails"] = azure_data[
                    "sub_details"
                ]

        if "bookmarks" in self.options:
            related_bookmarks = _get_related_bookmarks(
                self.query_provider, timespan, host_name
            )

        return HostResult(
            description="Host Summary",
            host_entity=host_entity,
            related_alerts=related_alerts,
            related_bookmarks=related_bookmarks,
        )


# Get Azure Resource details from API
def _azure_api_details(az, host_record):
    try:
        # Get subscription details
        sub_details = az.get_subscription_info(
            host_record.AzureDetails["SubscriptionId"]
        )
        # Get resource details
        resource_details = az.get_resource_details(
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
        azure_data = {"resoure_details": resource_details, "sub_details": sub_details}
        return azure_data
    except CloudError:
        return None


# %%
# Get heartbeat
def _verify_host_name(qry_prov, timespan, host_name) -> Tuple[str, bool]:

    host_names: List[str] = []
    # Get single event - try process creation
    if "SecurityEvent" in qry_prov.schema_tables:
        sec_event_host = f"""
            SecurityEvent
            | where TimeGenerated between (datetime({timespan.start})..datetime({timespan.end}))
            | where Computer has "{host_name}"
            | distinct Computer
             """
        win_hosts_df = qry_prov.exec_query(sec_event_host)
        if win_hosts_df is not None and not win_hosts_df.empty:
            host_names.extend(win_hosts_df["Computer"].to_list())
    if "Syslog" in qry_prov.schema_tables:
        syslog_host = f"""
            Syslog
            | where TimeGenerated between (datetime({timespan.start})..datetime({timespan.end}))
            | where Computer has "{host_name}"
            | distinct Computer
            """
        lx_hosts_df = qry_prov.exec_query(syslog_host)
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
        print(f"Host not found: {host_name}")
        return host_name, False

    print(f"Unique host found: {host_names[0]}")
    return host_names[0], True


# %%
# Get IP Information
def _get_heartbeat(qry_prov, host_name):
    host_entity = entities.Host(HostName=host_name)
    if "Heartbeat" in qry_prov.schema_tables:
        print(f"Looking for {host_name} in OMS Heartbeat data...")
        host_hb_df = qry_prov.Network.get_heartbeat_for_host(host_name=host_name)
        if not host_hb_df.empty:
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
            host_entity.Environment = host_hb["ComputerEnvironment"]
            if host_entity.Environment == "Azure":
                host_entity.AzureDetails = {
                    "SubscriptionId": host_hb["SubscriptionId"],
                    "ResourceProvider": host_hb["ResourceProvider"],
                    "ResourceType": host_hb["ResourceType"],
                    "ResourceGroup": host_hb["ResourceGroup"],
                    "ResourceId": host_hb["ResourceId"],
                    "Solutions": host_hb["Solutions"],
                }
            ip_entity = entities.IpAddress()
            ip_entity.Address = host_hb["ComputerIP"]
            geoloc_entity = entities.GeoLocation()
            geoloc_entity.CountryName = host_hb["RemoteIPCountry"]
            geoloc_entity.Longitude = host_hb["RemoteIPLongitude"]
            geoloc_entity.Latitude = host_hb["RemoteIPLatitude"]
            ip_entity.Location = geoloc_entity
            host_entity.IPAddress = ip_entity

    return host_entity


def _to_ip_entities(ip_str):
    iplocation = GeoLiteLookup()
    ip_entities = []
    if ip_str:
        if "," in ip_str:
            addrs = ip_str.split(",")
        elif " " in ip_str:
            addrs = ip_str.split(" ")
        else:
            addrs = [ip_str]
        for addr in addrs:
            ip_entity = entities.IpAddress()
            ip_entity.Address = addr.strip()
            iplocation.lookup_ip(ip_entity=ip_entity)
            ip_entities.append(ip_entity)
    return ip_entities


def _get_aznet_topology(qry_prov, host_name, host_entity):
    if "AzureNetworkAnalytics_CL" in qry_prov.schema_tables:
        print(f"Looking for {host_name} IP addresses in network flows...")
        az_net_df = qry_prov.Network.get_ips_for_host(host_name=host_name)

        if not az_net_df.empty:
            host_entity.private_ips = _to_ip_entities(
                az_net_df["PrivateIPAddresses"].iloc[0]
            )
            host_entity.public_ips = _to_ip_entities(
                az_net_df["PublicIPAddresses"].iloc[0]
            )
        else:
            if "private_ips" not in host_entity:
                host_entity.private_ips = []
            if "public_ips" not in host_entity:
                host_entity.public_ips = []
    return host_entity


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
