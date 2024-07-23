# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""IP Address Summary notebooklet."""
import json
from contextlib import suppress
from ipaddress import IPv4Address, IPv6Address, ip_address
from json import JSONDecodeError
from typing import Any, Dict, Iterable, List, Optional, Union

import numpy as np
import pandas as pd
from bokeh.models import LayoutDOM
from msticpy.common.exceptions import MsticpyException
from msticpy.common.timespan import TimeSpan
from msticpy.datamodel.entities import GeoLocation, Host, IpAddress

try:
    from msticpy import nbwidgets
    from msticpy.context.ip_utils import get_ip_type
    from msticpy.context.ip_utils import ip_whois as get_whois_info
    from msticpy.vis.timeline import display_timeline
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.nbtools import nbwidgets
    from msticpy.nbtools.timeline import display_timeline
    from msticpy.sectools.ip_utils import get_ip_type, get_whois_info

    # pylint: disable=unused-import
    from msticpy.vis import mp_pandas_plot  # noqa: F401

from .... import nb_metadata
from ...._version import VERSION
from ....common import (
    MsticnbMissingParameterError,
    df_has_data,
    nb_data_wait,
    nb_display,
    nb_markdown,
    set_text,
)
from ....nblib.azsent.alert import browse_alerts
from ....nblib.azsent.host import populate_host_entity
from ....nblib.iptools import convert_to_ip_entities
from ....notebooklet import NBMetadata, Notebooklet, NotebookletResult

__version__ = VERSION
__author__ = "Ian Hellen"


# Read module metadata from YAML
_CLS_METADATA: NBMetadata
_CELL_DOCS: Dict[str, Any]
_CLS_METADATA, _CELL_DOCS = nb_metadata.read_mod_metadata(__file__, __name__)


# pylint: disable=too-few-public-methods, too-many-instance-attributes, too-many-lines
# Rename this class
class IpSummaryResult(NotebookletResult):
    """
    IPSummary Results.

    Attributes
    ----------
    ip_str : str
        The input IP address as a string.
    ip_address : Optional[Union[IPv4Address, IPv6Address]]
        Ip Address Python object
    ip_entity : IpAddress
        IpAddress entity
    ip_origin : str
        "External" or "Internal"
    host_entities : Host
        Host entity or entities associated with IP Address
    ip_type : str
        IP address type - "Public", "Private", etc.
    geoip : Optional[Dict[str, Any]]
        Geo location information as a dictionary.
    location : Optional[GeoLocation]
        Location entity context object.
    whois : pd.DataFrame
        WhoIs information for IP Address
    whois_nets : pd.DataFrame
        List of networks definitions from WhoIs data
    heartbeat : pd.DataFrame
        Heartbeat record for IP Address or host
    az_network_if : pd.DataFrame
        Azure NSG analytics interface record, if available
    vmcomputer : pd.DataFrame
        VMComputer latest record
    az_network_flows : pd.DataFrame
        Azure NSG flows for IP, if available
    az_network_flows_timeline: LayoutDOM
        Azure NSG flows timeline, if data is available
    aad_signins : pd.DataFrame = None
        AAD signin activity
    azure_activity : pd.DataFrame = None
        Azure Activity log entries
    azure_activity_summary : pd.DataFrame = None
        Azure Activity (AAD and Az Activity) summarized view
    office_activity : pd.DataFrame = None
        Office 365 activity
    common_security : pd.DataFrame
        Common Security Log entries for source IP
    related_bookmarks : pd.DataFrame
        Bookmarks related to IP Address
    alert_timeline : LayoutDOM
        Timeline plot of alerts
    ti_results: pd.DataFrame
        Threat intel lookup results
    passive_dns: pd.DataFrame
        Passive DNS lookup results
    self.host_logons : pd.DataFrame
        Hosts with logons from this IP Address
    self.related_accounts : pd.DataFrame
        Accounts with activity related to this IP Address
    self.associated_hosts : pd.DataFrame
        Hosts using this IP Address
    self.device_info : pd.DataFrame
        Device info of hosts using this IP Address
    self.network_connections : pd.DataFrame = None
        Network connections to/from this IP on other devices

    """

    def __init__(
        self,
        description: Optional[str] = None,
        timespan: Optional[TimeSpan] = None,
        notebooklet: Optional["Notebooklet"] = None,
    ):
        """
        Create new IPSummaryResult result instance.

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
        self.description: str = "IP Address Summary"

        # Add attributes as needed here.
        # Make sure they are documented in the Attributes section
        # above.
        self.ip_str: str = ""
        self.ip_address: Optional[Union[IPv4Address, IPv6Address]] = None
        self.ip_entity: IpAddress = None
        self.ip_origin: str = "External"
        self.ip_type: str = "Public"
        self.host_entities: List[Host] = []
        self.geoip: Optional[Dict[str, Any]] = None
        self.location: Optional[GeoLocation] = None
        self.whois: Optional[pd.DataFrame] = None
        self.whois_nets: Optional[pd.DataFrame] = None
        self.heartbeat: Optional[pd.DataFrame] = None
        self.az_network_if: Optional[pd.DataFrame] = None
        self.vmcomputer: Optional[pd.DataFrame] = None
        self.az_network_flows: Optional[pd.DataFrame] = None
        self.az_network_flow_summary: Optional[pd.DataFrame] = None
        self.az_network_flows_timeline: Optional[LayoutDOM] = None
        self.aad_signins: Optional[pd.DataFrame] = None
        self.azure_activity: Optional[pd.DataFrame] = None
        self.azure_activity_summary: Optional[pd.DataFrame] = None
        self.office_activity: Optional[pd.DataFrame] = None
        self.common_security: Optional[pd.DataFrame] = None
        self.related_alerts: Optional[pd.DataFrame] = None
        self.related_bookmarks: Optional[pd.DataFrame] = None
        self.alert_timeline: Optional[LayoutDOM] = None
        self.ti_results: Optional[pd.DataFrame] = None
        self.passive_dns: Optional[pd.DataFrame] = None
        self.host_logons: Optional[pd.DataFrame] = None
        self.related_accounts: Optional[pd.DataFrame] = None
        self.associated_hosts: Optional[pd.DataFrame] = None
        self.device_info: Optional[pd.DataFrame] = None
        self.network_connections: Optional[pd.DataFrame] = None


# pylint: enable=too-few-public-methods, too-many-instance-attributes


class IpAddressSummary(Notebooklet):
    """
    IP Address Summary Notebooklet class.

    Queries and displays summary information about an IP address, including:

    - Basic IP address properties
    - IpAddress entity (and Host entity, if a host could be associated)
    - WhoIs and Geo-location
    - Azure activity and network data (optional)
    - Office activity summary (optional)
    - Threat intelligence reports
    - Related alerts and hunting bookmarks

    """

    # assign metadata from YAML to class variable
    metadata = _CLS_METADATA
    __doc__ = nb_metadata.update_class_doc(__doc__, metadata)
    _cell_docs = _CELL_DOCS

    # pylint: disable=too-many-branches, too-many-statements
    @set_text(docs=_CELL_DOCS, key="run")  # noqa: MC0001
    def run(  # noqa: MC0001,C901
        self,
        value: Any = None,
        data: Optional[pd.DataFrame] = None,
        timespan: Optional[TimeSpan] = None,
        options: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> IpSummaryResult:
        """
        Return IP Address activity summary.

        Parameters
        ----------
        value : str
            IP Address - The key for searches
        data : Optional[pd.DataFrame], optional
            Not supported for this notebooklet.
        timespan : TimeSpan
            Timespan for queries
        options : Optional[Iterable[str]], optional
            List of options to use, by default None.
            A value of None means use default options.
            Options prefixed with "+" will be added to the default options.
            To see the list of available options type `help(cls)` where
            "cls" is the notebooklet class or an instance of this class.

        Returns
        -------
        IpSummaryResult
            Result object with attributes for each result type.

        Raises
        ------
        MsticnbMissingParameterError
            If required parameters are missing

        """
        # This line use logic in the superclass to populate options
        # (including default options) into this class.
        super().run(
            value=value, data=data, timespan=timespan, options=options, **kwargs
        )

        if not value:
            raise MsticnbMissingParameterError("value")
        if not timespan:
            raise MsticnbMissingParameterError("timespan.")

        # Create a result class
        result = IpSummaryResult(
            notebooklet=self, description=self.metadata.description, timespan=timespan
        )

        result.ip_str = value
        result.ip_address = ip_address(value)
        result.ip_type = get_ip_type(value)
        result.ip_entity = IpAddress(Address=value)
        nb_markdown(f"{value}, ip address type: {result.ip_type}")

        geo_lookup = self.get_provider("geolitelookup") or self.get_provider(
            "ipstacklookup"
        )
        # Lookup basic host info
        if "device_info" in self.options and self.check_table_exists(
            "DeviceNetworkInfo"
        ):
            _get_device_info(
                qry_prov=self.query_provider,
                src_ip=value,
                result=result,
                geo_lookup=geo_lookup,
            )
        if not df_has_data(result.device_info):
            self.options.extend(["az_net_if", "heartbeat", "vmcomputer"])
            self.options = list(set(self.options))
        if "az_net_if" in self.options and self.check_table_exists(
            "AzureNetworkAnalytics_CL"
        ):
            _get_az_net_if(qry_prov=self.query_provider, src_ip=value, result=result)
        if "heartbeat" in self.options and self.check_table_exists("Heartbeat"):
            _get_heartbeat(qry_prov=self.query_provider, src_ip=value, result=result)
        if "vmcomputer" in self.options and self.check_table_exists("VMComputer"):
            _get_vmcomputer(qry_prov=self.query_provider, src_ip=value, result=result)
        _populate_host_entity(result, geo_lookup=geo_lookup)
        # Future: (ianhelle) - _normalize_host_entities(result)

        # Alerts and bookmarks
        if "alerts" in self.options:
            self._get_related_alerts(src_ip=value, result=result, timespan=timespan)
        if "bookmarks" in self.options:
            result = self._get_related_bookmarks(
                src_ip=value, result=result, timespan=timespan
            )
        # Azure NSG netflow
        if "az_netflow" in self.options:
            self._get_azure_netflow(src_ip=value, result=result, timespan=timespan)
            if df_has_data(result.az_network_flows):
                result.az_network_flow_summary = _summarize_netflows(
                    result.az_network_flows
                )
                nb_display()
        if "az_activity" in self.options or "related_accounts" in self.options:
            self._get_azure_activity(src_ip=value, result=result, timespan=timespan)
            _summarize_azure_activity(result)
        if "office_365" in self.options:
            self._get_office_activity(src_ip=value, result=result, timespan=timespan)
        if "common_security" in self.options:
            _get_common_security_log(
                qry_prov=self.query_provider,
                src_ip=value,
                result=result,
                timespan=timespan,
            )

        if "host_logons" in self.options:
            _get_host_logons(
                qry_prov=self.query_provider,
                src_ip=value,
                result=result,
                timespan=timespan,
            )
        if "related_accounts" in self.options:
            _get_related_accounts(result=result)

        if "device_network" in self.options and self.check_table_exists(
            "DeviceNetworkEvents"
        ):
            _get_device_net_connections(
                qry_prov=self.query_provider, src_ip=value, result=result
            )

        result.ip_origin = _determine_ip_origin(result)

        if result.ip_type == "Public":
            self._get_public_ip_data(src_ip=value, result=result)

        # Assign the result to the _last_result attribute
        # so that you can get to it without having to re-run the operation
        self._last_result = result  # pylint: disable=attribute-defined-outside-init

        nb_markdown("<h3>View the returned results object for more details.</h3>")
        nb_markdown(
            f"Additional methods for this class:<br>{'<br>'.join(self.list_methods())}"
        )
        return self._last_result

    # pylint: disable=too-many-branches, too-many-statements

    def browse_alerts(self) -> nbwidgets.SelectAlert:
        """Return alert browser/viewer."""
        if self.check_valid_result_data("related_alerts"):
            return browse_alerts(self._last_result, "related_alerts")
        return None

    def display_alert_timeline(self):
        """Display the alert timeline."""
        if self.check_valid_result_data("related_alerts"):
            return display_timeline(
                data=self._last_result.related_alerts,
                title="Alerts",
                source_columns=["AlertName"],
                height=300,
                hide=True,
            )
        return None

    def browse_ti_results(self):
        """Display Threat intel results."""
        if self.check_valid_result_data("ti_results"):
            ti_lookup = self.get_provider("tilookup")
            return ti_lookup.browse_results(self._last_result.ti_results)
        return None

    def netflow_by_protocol(
        self,
    ) -> Optional[LayoutDOM]:
        """Display netflows grouped by protocol."""
        if not self.check_valid_result_data("az_network_flows"):
            return None
        return _plot_netflow_by_protocol(self._last_result)

    def netflow_total_by_protocol(
        self,
    ) -> Optional[LayoutDOM]:
        """Display netflows grouped by protocol."""
        if not self.check_valid_result_data("az_network_flows"):
            return None
        return _plot_netflow_values_by_protocol(self._last_result)

    def netflow_by_direction(
        self,
    ) -> Optional[LayoutDOM]:
        """Display netflows grouped by direction."""
        if not self.check_valid_result_data("az_network_flows"):
            return None
        return _plot_netflow_by_direction(self._last_result)

    @set_text(docs=_CELL_DOCS, key="get_public_ip_data")
    def _get_public_ip_data(self, src_ip, result):
        """Retrieve data for public IP."""
        _get_whois(src_ip, result)
        nb_markdown("WhoIs data")
        nb_display(pd.DataFrame(result.whois.iloc[0]).T)

        # GeoIP
        if "geoip" in self.options:
            geo_lookup = self.get_provider("geolitelookup") or self.get_provider(
                "ipstacklookup"
            )
            if geo_lookup:
                _get_geoip_data(geo_lookup, src_ip, result)

        # TI Lookup
        if result.ip_origin == "External" or "ti" in self.options:
            _get_ti_data(self.get_provider("tilookup"), src_ip, result)

        # Passive DNS
        if (
            result.ip_origin == "External" or "passive_dns" in self.options
        ) and isinstance(result.ip_address, IPv4Address):
            _get_passv_dns(self.get_provider("tilookup"), src_ip, result)

    @set_text(docs=_CELL_DOCS, key="get_az_netflow")
    def _get_azure_netflow(self, src_ip, result, timespan):
        """Retrieve Azure netflow and activity events."""
        if self.check_table_exists("AzureNetworkAnalytics_CL"):
            _get_az_netflows(self.query_provider, src_ip, result, timespan)
            _display_df_summary(result.az_network_flows, "Azure NSG network flows")

    @set_text(docs=_CELL_DOCS, key="get_az_activity")
    def _get_azure_activity(self, src_ip, result, timespan):
        """Retrieve Azure netflow and activity events."""
        if self.check_table_exists("SigninLogs"):
            nb_data_wait("SigninLogs")
            result.aad_signins = self.query_provider.Azure.list_aad_signins_for_ip(
                timespan, ip_address_list=src_ip
            )
            _display_df_summary(result.aad_signins, "AAD signins")

        if self.check_table_exists("AzureActivity"):
            nb_data_wait("AzureActivity")
            result.azure_activity = (
                self.query_provider.Azure.list_azure_activity_for_ip(
                    timespan, ip_address_list=src_ip
                )
            )
            _display_df_summary(result.azure_activity, "Azure Activity")

    @set_text(docs=_CELL_DOCS, key="get_office_activity")
    def _get_office_activity(self, src_ip, result, timespan):
        """Retrieve Office activity data."""
        if self.check_table_exists("OfficeActivity"):
            nb_data_wait("OfficeActivity")
            office_activity = self.query_provider.Office365.list_activity_for_ip(
                timespan, ip_address_list=src_ip
            )
            if df_has_data(office_activity):
                result.office_activity = (
                    office_activity.rename(columns={"UserId": "Account"})
                    .groupby(["Account", "OfficeWorkload", "Operation"])
                    .agg(
                        OperationCount=pd.NamedAgg(column="Type", aggfunc="count"),
                        OperationTypes=pd.NamedAgg(
                            column="Operation", aggfunc=lambda x: x.unique().tolist()
                        ),
                        FirstOperation=pd.NamedAgg(
                            column="TimeGenerated", aggfunc="min"
                        ),
                        LastOperation=pd.NamedAgg(
                            column="TimeGenerated", aggfunc="max"
                        ),
                    )
                )
            _display_df_summary(result.office_activity, "Office 365 operations")
            if df_has_data(result.office_activity):
                nb_display(result.office_activity)

    @set_text(docs=_CELL_DOCS, key="get_related_alerts")
    def _get_related_alerts(self, src_ip, result, timespan):
        """Get any related alerts for `src_ip`."""
        nb_data_wait("RelatedAlerts")
        result.related_alerts = self.query_provider.SecurityAlert.list_alerts_for_ip(
            timespan, source_ip_list=src_ip
        )
        _display_df_summary(result.related_alerts, "related alerts")
        if df_has_data(result.related_alerts):
            nb_markdown(
                "Use `browse_alerts` and `display_alert_timeline` to view these."
            )

    @set_text(docs=_CELL_DOCS, key="get_related_alerts")
    def _get_related_bookmarks(
        self, src_ip, result, timespan: TimeSpan
    ) -> pd.DataFrame:
        nb_data_wait("Bookmarks")
        result.related_bookmarks = (
            self.query_provider.AzureSentinel.list_bookmarks_for_entity(  # type: ignore
                timespan, entity_id=src_ip
            )
        )
        _display_df_summary(result.related_bookmarks, "related bookmarks")
        return result


# %%
# Helper functions
def _display_df_summary(data, description):
    if df_has_data(data):
        nb_markdown(f"{len(data)} {description}.")
    else:
        nb_markdown(f"No events from {description} found.")


def _determine_ip_origin(result):
    return (
        "Internal"
        if (
            result.ip_type == "Private"
            or df_has_data(result.heartbeat)
            or df_has_data(result.az_network_if)
            or df_has_data(result.vmcomputer)
            or df_has_data(result.associated_hosts)
        )
        else "External"
    )


# %%
# Get Azure network flows
def _get_az_netflows(qry_prov, src_ip, result, timespan):
    nb_data_wait("Azure NSG flows")
    result.az_network_flows = qry_prov.Network.list_azure_network_flows_by_ip(
        timespan, ip_address_list=src_ip
    )
    if df_has_data(result.az_network_flows):
        result.az_network_flows["TotalAllowedFlows"] = (
            result.az_network_flows["AllowedOutFlows"]
            + result.az_network_flows["AllowedInFlows"]
        )
        result.az_network_flows_timeline = _plot_netflow_by_protocol(result)


def _plot_netflow_by_protocol(result):
    return result.az_network_flows.mp_plot.timeline(
        group_by="L7Protocol",
        title="Network Flows by Protocol",
        time_column="FlowStartTime",
        source_columns=["FlowType", "AllExtIPs", "L7Protocol", "FlowDirection"],
        height=300,
        legend="right",
        yaxis=True,
    )


def _plot_netflow_values_by_protocol(result):
    return result.az_network_flows.mp_plot.timeline_values(
        group_by="L7Protocol",
        source_columns=[
            "FlowType",
            "AllExtIPs",
            "L7Protocol",
            "FlowDirection",
            "TotalAllowedFlows",
        ],
        time_column="FlowStartTime",
        title="Network flows by Layer 7 Protocol",
        y="TotalAllowedFlows",
        legend="right",
        height=500,
        kind=["vbar", "circle"],
    )


def _plot_netflow_by_direction(result):
    return result.az_network_flows.mp_plot.timeline(
        group_by="FlowDirection",
        title="Network Flows by Direction",
        time_column="FlowStartTime",
        source_columns=["FlowType", "AllExtIPs", "L7Protocol", "FlowDirection"],
        height=300,
        legend="right",
        yaxis=True,
    )


@set_text(docs=_CELL_DOCS, key="netflow_summary")
def _summarize_netflows(data):
    # pylint: disable=unnecessary-lambda
    return (
        data[
            [
                "AllExtIPs",
                "L7Protocol",
                "FlowDirection",
                "TotalAllowedFlows",
                "FlowStartTime",
            ]
        ]
        .groupby(["L7Protocol", "FlowDirection"])
        .agg(
            ExtIPs=pd.NamedAgg(column="AllExtIPs", aggfunc=lambda x: ", ".join(x)),
            ExtIPCount=pd.NamedAgg(column="AllExtIPs", aggfunc="count"),
            FirstFlow=pd.NamedAgg(column="FlowStartTime", aggfunc="min"),
            LastFlow=pd.NamedAgg(column="FlowStartTime", aggfunc="max"),
        )
    )
    # pylint: enable=unnecessary-lambda


# %%
# Azure activity
def _summarize_azure_activity(result):
    az_dfs = []
    if df_has_data(result.aad_signins):
        az_dfs.append(
            result.aad_signins.assign(
                UserPrincipalName=lambda x: x.UserPrincipalName.str.lower(),
                Status=result.aad_signins["ResultDescription"],
            )
            .replace({"Status": ""}, "Success")  # fill in blank (ResultType==0) status
            .rename(
                columns={
                    "OperationName": "Operation",
                    "AppDisplayName": "AppResourceProvider",
                }
            )
        )

    if df_has_data(result.azure_activity):
        az_dfs.append(
            result.azure_activity.assign(
                UserPrincipalName=lambda x: x.Caller.str.lower()
            ).rename(
                columns={
                    "CallerIpAddress": "IPAddress",
                    "OperationName": "Operation",
                    "ResourceProvider": "AppResourceProvider",
                    "Category": "UserType",
                    "ActivityStatusValue": "Status",
                }
            )
        )

    if not az_dfs:
        return

    az_all_data = pd.concat(az_dfs)
    result.azure_activity_summary = az_all_data.groupby(
        [
            "UserPrincipalName",
            "Type",
            "IPAddress",
            "AppResourceProvider",
            "UserType",
            "Status",
        ]
    ).agg(
        OperationCount=pd.NamedAgg(column="Type", aggfunc="count"),
        OperationTypes=pd.NamedAgg(
            column="Operation", aggfunc=lambda x: x.unique().tolist()
        ),
        Resources=pd.NamedAgg(column="ResourceId", aggfunc="nunique"),
        FirstOperation=pd.NamedAgg(column="TimeGenerated", aggfunc="min"),
        LastOperation=pd.NamedAgg(column="TimeGenerated", aggfunc="max"),
    )
    nb_markdown("Summary of Azure activity", "large")
    nb_display(result.azure_activity_summary)


# %%
# Azure heartbeat, interface and VMComputer data
@set_text(docs=_CELL_DOCS, key="get_az_net_if")
def _get_az_net_if(qry_prov, src_ip, result):
    """Get the AzureNetwork topology record for `src_ip`."""
    nb_data_wait("Azure NSG topology")
    # Try to find the interface topology log entry
    result.az_network_if = qry_prov.Network.get_host_for_ip(  # type:ignore
        ip_address=src_ip
    )
    if not df_has_data(result.az_network_if):
        nb_markdown("Could not get Azure NSG network interface record.")


@set_text(docs=_CELL_DOCS, key="get_heartbeat")
def _get_heartbeat(qry_prov, src_ip, result):
    """Get the Heartbeat record for `src_ip`."""
    nb_data_wait("Heartbeat")
    if result.ip_type == "Public":
        result.heartbeat = qry_prov.Network.get_heartbeat_for_ip(ip_address=src_ip)
    elif (
        result.host_entity
        and result.host_entity.HostName
        and result.host_entity.HostName != "unknown"
    ):
        result.heartbeat = qry_prov.Network.get_heartbeat_for_host(
            host_name=result.host_entity.HostName
        )
    if not df_has_data(result.heartbeat):
        nb_markdown("Could not get Azure Heartbeat record.")


@set_text(docs=_CELL_DOCS, key="get_common_security_log")
def _get_common_security_log(qry_prov, src_ip, result, timespan):
    """Get the CommonSecurityLog records for `src_ip`."""
    nb_data_wait("Common Security Log")
    query = """
    CommonSecurityLog
    | where TimeGenerated between (datetime({start}) .. datetime({end}))
    | where SourceIP == '{ip_address}' or DestinationIP == '{ip_address}'
    """
    result_df = qry_prov.exec_query(
        query.format(
            start=timespan.start,
            end=timespan.end,
            ip_address=src_ip,
        )
    )

    if df_has_data(result_df):
        # Log has lots of sparse columns - trim these down as much as
        # possible.
        result.common_security = result_df.replace("", np.nan).dropna(
            how="all", axis="columns"
        )
    else:
        nb_markdown("No CommonSecurityLog records found.")


@set_text(docs=_CELL_DOCS, key="get_vmcomputer")
def _get_vmcomputer(qry_prov, src_ip, result):
    """Get the VMComputer record for `src_ip`."""
    nb_data_wait("VMComputer")
    result.vmcomputer = qry_prov.Azure.get_vmcomputer_for_ip(  # type:ignore
        ip_address=src_ip
    )
    if not df_has_data(result.vmcomputer):
        nb_markdown("Could not get VMComputer record")


_MDE_DEVICE_NET_INFO = """
DeviceNetworkInfo
| where IPAddresses has "{src_ip}"
| mv-expand IPAddresses
| extend IPAddress = tostring(IPAddresses.IPAddress)
| summarize arg_max(TimeGenerated, *) by IPAddress, DeviceName, DeviceId
"""

_MDE_DEVICE_INFO = """
DeviceInfo
| where DeviceId == "{device_id}"
| summarize arg_max(TimeGenerated, *)
"""


@set_text(docs=_CELL_DOCS, key="get_device_info")
def _get_device_info(qry_prov, src_ip, result, geo_lookup):
    nb_data_wait("DeviceInfo")
    result.associated_hosts = qry_prov.exec_query(
        _MDE_DEVICE_NET_INFO.format(src_ip=src_ip)
    )
    if df_has_data(result.associated_hosts):
        device_ids = result.associated_hosts.DeviceId.unique()
        result.device_info = pd.concat(
            [
                qry_prov.exec_query(_MDE_DEVICE_INFO.format(device_id=device_id))
                for device_id in device_ids
            ],
            ignore_index=True,
        )
        result.host_entities = _host_entity_from_dev_info(result, geo_lookup=geo_lookup)
        _display_df_summary(result.associated_hosts, "Defender hosts with matching IP")
        nb_display(result.associated_hosts[["DeviceName"]].drop_duplicates())
        _display_df_summary(result.device_info, "Defender hosts device info")
    nb_markdown("No events from Defender Device info")


def _host_entity_from_dev_info(result, geo_lookup):
    device_info = result.device_info
    host_dict: Dict[str, Host] = {}
    for row in device_info.itertuples():
        host_entity = host_dict.get(row.DeviceName)
        # if we don't already have a host of that name, create one
        if not host_entity:
            if "." in row.DeviceName:
                host, domain = row.DeviceName.split(".", maxsplit=1)
            else:
                host = row.DeviceName
                domain = None
            host_entity = Host(
                HostName=host,
                DnsDomain=domain,
                IsDomainJoined=row.IsAzureADJoined,
            )
            host_entity.DeviceIds = []
            host_entity.IpAddresses = []
            host_dict[row.DeviceName] = host_entity
        # add device ID
        if row.DeviceId not in host_entity.DeviceIds:
            host_entity.DeviceIds.append(row.DeviceId)
        # Add IP Addresses from dev info record
        ip_set = {row.PublicIP}
        # and from the devicenetworkinfo results for this device
        ip_set.update(
            result.associated_hosts[
                result.associated_hosts.DeviceId == row.DeviceId
            ].IPAddress
        )
        ip_entities = convert_to_ip_entities(list(ip_set), geo_lookup=geo_lookup)
        host_ips = {ip.Address for ip in host_entity.IpAddresses}
        host_entity.IpAddresses.extend(
            [
                ip_entity
                for ip_entity in ip_entities
                if ip_entity.Address not in host_ips
            ]
        )
    return list(host_dict.values())


_MDE_DEV_NETWORK_EVT = """
DeviceNetworkEvents
| where RemoteIP == "{src_ip}"
| extend Computer = DeviceName
| summarize Count=count(), FirstOperation=min(TimeGenerated),
LastOperation=max(TimeGenerated) by Computer, LocalIP, RemoteIP,
ActionType, InitiatingProcessAccountName, InitiatingProcessFolderPath,
InitiatingProcessSHA256
"""


@set_text(docs=_CELL_DOCS, key="get_device_network")
def _get_device_net_connections(qry_prov, src_ip, result):
    nb_data_wait("DeviceNetworkEvents")
    result.network_connections = qry_prov.exec_query(
        _MDE_DEV_NETWORK_EVT.format(src_ip=src_ip)
    )
    if df_has_data(result.network_connections):
        _display_df_summary(result.network_connections, "Defender network connections")
        nb_display(
            result.network_connections[["Computer", "LocalIP"]].drop_duplicates()
        )
    else:
        nb_markdown("No events from Device network connections")


_WIN_HOSTS_LOGONS = """
SecurityEvent
| where TimeGenerated >= datetime({start}) and TimeGenerated <= datetime({end})
| where EventID in (4624, 4625)
| where IpAddress == \'{ip_address}\'
| project-rename LogonTypeCode=LogonType
| project-rename LogonType=LogonTypeName
| summarize Count=count(), FirstOperation=min(TimeGenerated),
LastOperation=max(TimeGenerated) by Computer, Account, LogonType
"""
_LX_HOST_LOGONS_ADD = """
| project-rename Account=User
| summarize Count=count(), FirstOperation=min(TimeGenerated),
LastOperation=max(TimeGenerated) by Computer, Account, LogonType
"""


@set_text(docs=_CELL_DOCS, key="get_host_logons")
def _get_host_logons(qry_prov, src_ip, result, timespan):
    """Get the hosts with logons for `src_ip`."""
    nb_data_wait("Related hosts")
    win_hosts_df = qry_prov.exec_query(
        _WIN_HOSTS_LOGONS.format(
            start=timespan.start,
            end=timespan.end,
            ip_address=src_ip,
        )
    )
    lx_hosts_df = qry_prov.LinuxSyslog.list_logons_for_source_ip(
        start=timespan.start,
        end=timespan.end,
        ip_address=src_ip,
        add_query_items=_LX_HOST_LOGONS_ADD,
    )
    combined_results = []
    if df_has_data(win_hosts_df):
        combined_results.append(win_hosts_df.assign(Type="Windows"))
    if df_has_data(lx_hosts_df):
        combined_results.append(lx_hosts_df.assign(Type="Linux"))
    if combined_results:
        result.host_logons = pd.concat(combined_results, ignore_index=True)[
            [
                "Computer",
                "Account",
                "Type",
                "LogonType",
                "Count",
                "FirstOperation",
                "LastOperation",
            ]
        ]
        nb_display(
            result.host_logons[
                ["Computer", "Type", "LogonType", "Count"]
            ].drop_duplicates()
        )
        return
    nb_markdown("No results for host logons")


@set_text(docs=_CELL_DOCS, key="get_related_accounts")
def _get_related_accounts(result):
    """Get the related accounts for `src_ip`."""
    nb_data_wait("Related accounts")
    combined_results = []
    if df_has_data(result.host_logons):
        combined_results.append(result.host_logons)
    if df_has_data(result.azure_activity_summary):
        combined_results.append(
            result.azure_activity_summary.reset_index().rename(
                columns={"UserPrincipalName": "Account", "OperationCount": "Count"}
            )[["Account", "Type", "Status", "Count", "FirstOperation", "LastOperation"]]
        )
    if df_has_data(result.office_activity):
        combined_results.append(
            result.office_activity.reset_index().rename(
                columns={
                    "OfficeWorkload": "Type",
                    "OperationCount": "Count",
                }
            )[["Account", "Type", "Count", "FirstOperation", "LastOperation"]]
        )

    if combined_results:
        result.related_accounts = pd.concat(combined_results, ignore_index=True)
        nb_display(
            result.related_accounts[["Account", "Type", "Count"]].drop_duplicates()
        )
        return
    nb_markdown("No results for related accounts")


def _populate_host_entity(result, geo_lookup=None):
    """Populate host entity and IP address details."""
    result.host_entities.append(
        populate_host_entity(
            heartbeat_df=result.heartbeat,
            az_net_df=result.az_network_if,
            vmcomputer_df=result.vmcomputer,
            geo_lookup=geo_lookup,
            host_entity=result.host_entities[0] if result.host_entities else None,
        )
    )


# %%
# Public IP functions
def _get_whois(src_ip, result):
    """Get WhoIs data and split out networks."""
    _, whois_dict = get_whois_info(src_ip)
    result.whois = pd.DataFrame(whois_dict)
    result.whois_nets = pd.DataFrame(whois_dict.get("nets", []))
    if df_has_data(result.whois):
        nb_markdown("Whois data retrieved")


def _get_geoip_data(geo_lookup, src_ip, result):
    if result.ip_entity:
        geo_list, ip_list = geo_lookup.lookup_ip(ip_entity=result.ip_entity)
    else:
        geo_list, ip_list = geo_lookup.lookup_ip(src_ip)
    result.geoip = geo_list[0] if geo_list else None
    if isinstance(result.geoip, str):
        try:
            result.geoip = json.loads(result.geoip)
        except JSONDecodeError:
            pass
    result.ip_entity = ip_list[0] if ip_list else None
    if result.ip_entity and hasattr(result.ip_entity, "Location"):
        result.location = result.ip_entity.Location
        nb_markdown("GeoLocation data retrieved")
        nb_display(result.ip_entity.Location)


def _get_ti_data(ti_lookup, src_ip, result):
    nb_data_wait("Threat Intel")
    if not ti_lookup:
        return
    ti_results = ti_lookup.lookup_ioc(src_ip)
    result.ti_results = ti_lookup.result_to_df(ti_results)
    warn_ti_res = len(result.ti_results.query("Severity != 'information'"))
    if warn_ti_res:
        nb_markdown(f"{warn_ti_res} TI result(s) of severity 'warning' or above found.")
        nb_display(result.ti_results)
        nb_markdown("Use `browse_ti_results()` to view details.")


def _get_passv_dns(ti_lookup, src_ip, result):
    nb_data_wait("Passive DNS")
    if not ti_lookup:
        return
    try:
        ip_class = ip_address(src_ip)
    except ValueError:
        ip_class = None
    if not hasattr(ti_lookup, "available_query_types"):
        return
    if (
        isinstance(ip_class, IPv6Address)
        and "ipv6-passivedns" not in ti_lookup.available_query_types
    ):
        return
    if (
        isinstance(ip_class, IPv4Address)
        and "ipv4-passivedns" not in ti_lookup.available_query_types
    ):
        return
    with suppress(MsticpyException):
        passv_dns = ti_lookup.lookup_ioc(
            src_ip,
            ioc_type="ipv4" if isinstance(ip_class, IPv4Address) else "ipv6",
            ioc_query_type="passivedns",
        )
        result.passive_dns = ti_lookup.result_to_df(passv_dns)
    if result.passive_dns is not None and not result.passive_dns.empty:
        nb_markdown(f"{len(result.passive_dns)} Passive DNS results found.")
