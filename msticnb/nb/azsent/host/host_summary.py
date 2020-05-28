# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklet for Host Summary."""
from functools import lru_cache
from typing import Any, Optional, Iterable, Union, Dict

import attr
import pandas as pd
from azure.common.exceptions import CloudError
from bokeh.models import LayoutDOM
from bokeh.plotting.figure import Figure
from msticpy.nbtools import nbdisplay
from msticpy.nbtools import entities
from msticpy.common.utility import md

from ....common import (
    TimeSpan,
    MsticnbMissingParameterError,
    nb_data_wait,
    set_text,
    nb_print,
    nb_markdown,
)
from ....notebooklet import Notebooklet, NotebookletResult, NBMetaData
from ....nblib.azsent.host import get_heartbeat, get_aznet_topology, verify_host_name
from ....nb_metadata import read_module_metadata
from ...._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


_CLS_METADATA: NBMetaData
_CELL_DOCS: Dict[str, Any]
_CLS_METADATA, _CELL_DOCS = read_module_metadata(__name__)


# pylint: disable=too-few-public-methods
@attr.s(auto_attribs=True)
class HostSummaryResult(NotebookletResult):
    """
    Host Details Results.

    Attributes
    ----------
    host_entity : msticpy.data.nbtools.entities.Host
        The host entity object contains data about the host
        such as name, environment, operating system version,
        IP addresses and Azure VM details. Depending on the
        type of host, not all of this data may be populated.
    related_alerts : pd.DataFrame
        Pandas DataFrame of any alerts recorded for the host
        within the query time span.
    alert_timeline:
        Bokeh time plot of alerts recorded for host.
    related_bookmarks: pd.DataFrame
        Pandas DataFrame of any investigation bookmarks
        relating to the host.

    """

    host_entity: entities.Host = None
    related_alerts: pd.DataFrame = None
    alert_timeline: Union[LayoutDOM, Figure] = None
    related_bookmarks: pd.DataFrame = None


# pylint: disable=too-few-public-methods
class HostSummary(Notebooklet):
    """
    HostSummary Notebooklet class.

    Queries and displays information about a host including:

    - IP address assignment
    - Related alerts
    - Related hunting/investigation bookmarks
    - Azure subscription/resource data.

    """

    metadata = _CLS_METADATA

    # pylint: disable=too-many-branches
    @set_text(docs=_CELL_DOCS, key="run")  # noqa MC0001
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
            Timespan over which operations such as queries will be
            performed, by default None.
            This can be a TimeStamp object or another object that
            has valid `start`, `end`, or `period` attributes.
        options : Optional[Iterable[str]], optional
            List of options to use, by default None
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

        # pylint: disable=attribute-defined-outside-init
        self._last_result = HostSummaryResult(description=self.metadata.description)

        host_name, host_names = verify_host_name(
            self.query_provider, self.timespan, value
        )
        if host_names:
            md(f"Could not obtain unique host name from {value}. Aborting.")
            return self._last_result
        if not host_name:
            nb_markdown(
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
            and "azuredata" in self.data_providers.providers
            and host_entity.Environment == "Azure"
        ):
            azure_api = _azure_api_details(
                self.data_providers["azuredata"], host_entity
            )
            if azure_api:
                host_entity.AzureDetails["ResourceDetails"] = azure_api[
                    "resoure_details"
                ]
                host_entity.AzureDetails["SubscriptionDetails"] = azure_api[
                    "sub_details"
                ]
        if not self.silent:
            _show_host_entity(host_entity)
        if "alerts" in self.options:
            related_alerts = _get_related_alerts(
                self.query_provider, self.timespan, host_name
            )
            if len(related_alerts) > 0:
                alert_timeline = _show_alert_timeline(related_alerts)
        if "bookmarks" in self.options:
            related_bookmarks = _get_related_bookmarks(
                self.query_provider, self.timespan, host_name
            )

        self._last_result.host_entity = host_entity
        self._last_result.related_alerts = related_alerts
        self._last_result.related_bookmarks = related_bookmarks
        self._last_result.alert_timeline = alert_timeline

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
@set_text(docs=_CELL_DOCS, key="show_host_entity")
def _show_host_entity(host_entity):
    nb_print(host_entity)


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
        nb_markdown(
            f"Found {len(related_alerts)} related alerts ({len(host_alert_items)}) types"
        )
    else:
        nb_markdown("No related alerts found.")
    return related_alerts


@set_text(docs=_CELL_DOCS, key="show_alert_timeline")
def _show_alert_timeline(related_alerts):
    if len(related_alerts) > 1:
        alert_plot = nbdisplay.display_timeline(
            data=related_alerts,
            title="Related Alerts",
            source_columns=["AlertName", "TimeGenerated"],
            height=200,
        )
        return alert_plot
    if len(related_alerts) == 1:
        nb_markdown("A single alert cannot be plotted on a timeline.")
    else:
        nb_markdown("No alerts available to be plotted.")
    return None


@lru_cache()
def _get_related_bookmarks(qry_prov, timespan, host_name):
    nb_data_wait("Bookmarks")
    host_bkmks = qry_prov.AzureSentinel.list_bookmarks_for_entity(
        timespan, entity_id=f"'{host_name}'"
    )

    if not host_bkmks.empty:
        nb_markdown(f"{len(host_bkmks)} investigation bookmarks found for this host.")
    else:
        nb_markdown("No bookmarks found.")
    return host_bkmks
