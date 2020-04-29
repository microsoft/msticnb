# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""host_summary - handles reading noebooklets modules."""
from functools import lru_cache
from typing import Any, Optional, Iterable

import attr
import pandas as pd
from azure.common.exceptions import CloudError
from msticpy.nbtools import nbdisplay
from msticpy.nbtools import entities
from msticpy.common.utility import md

from ....common import (
    TimeSpan,
    NotebookletException,
    print_data_wait,
    print_status,
    set_text,
)
from ....notebooklet import Notebooklet, NotebookletResult, NBMetaData
from ....nblib.azsent.host import get_heartbeat, get_aznet_topology, verify_host_name

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
        name=__qualname__,
        mod_name=__name__,
        description="Host summary",
        options=["heartbeat", "azure_net", "alerts", "bookmarks", "azure_api"],
        default_options=["heartbeat", "azure_net", "alerts", "bookmarks", "azure_api"],
        keywords=["host", "computer", "heartbeat", "windows", "linux"],
        entity_types=["host"],
        req_providers=["azure_sentinel"],
    )

    @set_text(
        title="Host Entity Summary",
        hd_level=1,
        text="Data and plots are store in the result class returned by this function",
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

        self._last_result = HostSummaryResult(description=self.metadata.description)

        host_name, host_names = verify_host_name(self.query_provider, timespan, value)
        if host_names:
            md(f"Could not obtain unique host name from {value}. Aborting.")
            return self._last_result
        if not host_name:
            md(
                f"Could not find event records for host {value}. "
                + "Results may be unreliable.",
                "orange",
            )
        host_name = host_name or value

        host_entity = entities.Host(HostName=host_name)
        if "heartbeat" in self.options:
            host_entity = get_heartbeat(self.query_provider, host_name)
        if "azure_net" in self.options:
            host_entity = host_entity or entities.Host(HostName=host_name)
            get_aznet_topology(
                self.query_provider, host_entity=host_entity, host_name=host_name
            )
        # If azure_details flag is set, an encrichment provider is given,
        # and the resource is an Azure host get resource details from Azure API
        if (
            "azure_api" in self.options
            and "azure_api" in self.data_providers.providers
            and host_entity.Environment == "Azure"
        ):
            azure_api = _azure_api_details(
                self.data_providers.providers["azure_api"], host_entity
            )
            if azure_api:
                host_entity.AzureDetails["ResourceDetails"] = azure_api[
                    "resoure_details"
                ]
                host_entity.AzureDetails["SubscriptionDetails"] = azure_api[
                    "sub_details"
                ]
        _show_host_entity(host_entity)
        if "alerts" in self.options:
            related_alerts = _get_related_alerts(
                self.query_provider, timespan, host_name
            )
            _show_alert_timeline(related_alerts)
        if "bookmarks" in self.options:
            related_bookmarks = _get_related_bookmarks(
                self.query_provider, timespan, host_name
            )

        self._last_result.host_entity = host_entity
        self._last_result.related_alerts = related_alerts
        self._last_result.related_bookmarks = related_bookmarks

        return self._last_result


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
        azure_api = {"resoure_details": resource_details, "sub_details": sub_details}

        return azure_api
    except CloudError:
        return None


# %%
# Get IP Information from Heartbeat
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
