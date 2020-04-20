# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""host_network_summary notebooklet."""
from ipaddress import ip_address
from itertools import chain
from typing import Any, Optional, Iterable, Tuple

import attr
import bokeh
from IPython.display import display
import pandas as pd

from msticpy.nbtools import nbwidgets, nbdisplay
from msticpy.nbtools import entities, foliummap
from msticpy.sectools import GeoLiteLookup, TILookup
from msticpy.sectools.ip_utils import get_whois_df, get_whois_info, get_ip_type
from msticpy.sectools.tiproviders.ti_provider_base import TISeverity
from msticpy.common.utility import md, md_warn

from ...common import (
    TimeSpan,
    NotebookletException,
    find_type_in_globals,
    print_data_wait,
)
from ...data_providers import DataProviders
from ...notebooklet import Notebooklet, NotebookletResult, NBMetaData
from ..host.host_summary import get_heartbeat, get_aznet_topology

from ..._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"

# __all__ = [HostSummary]


@attr.s(auto_attribs=True)
class NetworkFlowResult(NotebookletResult):
    """
    Network Flow Details Results.

    Attributes
    ----------
    host_entity : msticpy.data.nbtools.entities.Host
    network_flows : pd.DataFrame
    related_bookmarks: pd.DataFrame

    """

    description: str = "Network flow results"
    host_entity: entities.Host = None
    network_flows: pd.DataFrame = None
    plot_flows_by_protocol: bokeh.plotting.figure = None
    plot_flows_by_direction: bokeh.plotting.figure = None
    plot_flow_values: bokeh.plotting.figure = None
    flow_index: pd.DataFrame = None
    flow_summary: pd.DataFrame = None
    ti_results: pd.DataFrame = None
    geo_map: foliummap.FoliumMap = None


class NetworkFlowSummary(Notebooklet):
    """
    Network Flow Summary Notebooklet class.

    Notes
    -----
    Queries network data and plots time lines for network
    traffic to/from a host or IP address.

    """

    metadata = NBMetaData(
        name=__name__,
        description="Network flow summary",
        options=[
            "plot_flows",
            "plot_flow_values",
            "flow_summary",
            "resolve_host",
            "geo_map",
        ],
        default_options=["plot_flows", "plot_flow_values", "flow_summary"],
        keywords=["host", "computer", "network", "flow"],
        entity_types=["host", "ip_address"],
        req_providers=["azure_sentinel"],
    )

    def __init__(
        self, data_providers: Optional[DataProviders] = None, **kwargs,
    ):
        """
        Intialize a new instance of the notebooklet class.

        Parameters
        ----------
        data_providers : DataProviders, Optional
            Optional DataProviders instance to query data.
            Most classes require this.

        """
        super().__init__(data_providers, **kwargs)

        self.asn_selector: Optional[nbwidgets.SelectSubset] = None
        self.ti_lookup = find_type_in_globals(TILookup, last=True) or TILookup()

    def run(
        self,
        value: Any = None,
        data: Optional[pd.DataFrame] = None,
        timespan: Optional[TimeSpan] = None,
        options: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> NetworkFlowResult:
        """
        Return host summary data.

        Parameters
        ----------
        value : str
            Host entity, hostname or host IP Address
        data : Optional[pd.DataFrame], optional
            Not used, by default None
        timespan : TimeSpan
            Timespan for queries
        options : Optional[Iterable[str]], optional
            List of options to use, by default None
            A value of None means use default options.

        Returns
        -------
        HostNetworkResult
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

        result = NetworkFlowResult()
        if isinstance(value, entities.Host):
            host_name = value.HostName
            result.host_entity = value
            host_ip = None
        else:
            host_ip, host_name = _ip_or_hostname(value)
            result.host_entity = _create_host_entity(
                host_name=host_name, host_ip=host_ip
            )

        result.description = (
            "Network flow summary for " + host_name or host_ip  # type: ignore
        )

        flow_df = _get_az_net_flows(self.query_provider, timespan, host_ip, host_name)
        result.network_flows = flow_df

        if "resolve_host" in self.options:
            print_data_wait("HostResolver")
            result.host_entity = _get_host_details(
                qry_prov=self.query_provider, host_entity=result.host_entity
            )
        if "plot_flows" in self.options:
            result.plot_flows_by_protocol = _plot_flows_by_protocol(flow_df)
            result.plot_flows_by_direction = _plot_flows_by_direction(flow_df)
        if "plot_flow_values" in self.options:
            result.plot_flow_values = _plot_flow_values(flow_df)
        if "flow_summary" in self.options:
            result.flow_index = _get_flow_index_display(_extract_flow_ips(flow_df))
            result.flow_summary = _get_flow_summary(result.flow_index)
        if "geo_map" in self.options:
            result.geo_map = _display_geo_map_all(flow_df, result.host_entity)

        self._last_result = result
        return self._last_result

    def select_asns(self):
        """Show selector to choose which ASNs to process."""
        if not self._last_result or not self._last_result.flow_summary:
            print(
                "Please use 'run' with 'flow_summary' option before using",
                "this method.",
            )
            return
        self.asn_selector = _select_asn_subset(
            flow_sum_df=self._last_result.flow_summary,
            host_entity=self._last_result.host_entity,
        )
        display(self.asn_selector)

    def lookup_ti_for_asn_ips(self):
        """Lookup IPs of selected ASN in TILookip."""
        if (
            not self._last_result
            or not self._last_result.flow_summary
            or not self.asn_selector
        ):
            print(
                "Please use 'run()' with 'flow_summary' option before using",
                "this method. Then call 'lookup_ti_for_asn_ips()'",
            )
            return

        selected_ips = _get_ips_from_selected_asn(
            flow_sum_df=self._last_result.flow_summary, select_asn=self.asn_selector,
        )
        ti_results = _lookup_ip_ti(
            flows_df=self._last_result,
            selected_ips=selected_ips,
            ti_lookup=self.ti_lookup,
        )
        self._last_result.ti_results = ti_results

    def show_selected_asn_map(self) -> foliummap.FoliumMap:
        """
        Display map of IP locations for selected ASNs.

        Returns
        -------
        FoliumMap
            msticpy Folium instance.

        """
        if (
            not self._last_result
            or not self._last_result.flow_summary
            or not self.asn_selector
        ):
            print(
                "Please use 'run()' with 'flow_summary' option before using",
                "this method. Then run 'select_asns()' (and optionally)",
                "'lookup_ti_for_asn_ips()'.",
                "\nThen call 'show_selected_asn_map()'",
            )
            return None
        return _display_geo_map(
            flow_df=self._last_result.flow_summary,
            host_entity=self._last_result.host_entity,
            ti_results=self._last_result.ti_results,
            select_asn=self.asn_selector,
        )


# %%
# Helper functions
def _ip_or_hostname(search_value) -> Tuple[Any, Any]:
    search_value = search_value.strip()
    try:
        ip_address(search_value)
        return search_value, None
    except ValueError:
        return None, search_value


def _create_host_entity(host_name=None, host_ip=None):
    host_entity = entities.Host()
    if host_name:
        host_entity.HostName = host_name
    if host_ip:
        ip_entity = entities.IpAddress(Address=host_ip)
        host_entity.IpAddress = ip_entity
    return host_entity


def _get_host_details(qry_prov, host_entity):
    host_ip = getattr(host_entity, "IpAddress", None)
    host_name = getattr(host_entity, "HostName", None)

    print_data_wait("Heartbeat")
    host_entity = get_heartbeat(qry_prov=qry_prov, host_ip=host_ip, host_name=host_name)
    print_data_wait("AzureNetworkAnalytics")
    get_aznet_topology(
        qry_prov=qry_prov, host_ip=host_ip, host_entity=host_entity, host_name=host_name
    )
    return host_entity


# %%
# Get network flows
def _get_az_net_flows(qry_prov, timespan, ip_addr, hostname):
    print_data_wait("AzureNetworkAnalytics")
    if ip_addr:
        flow_df = qry_prov.Network.list_azure_network_flows_by_ip(
            timespan, ip_address_list=ip_addr
        )
    else:
        flow_df = qry_prov.Network.list_azure_network_flows_by_host(
            timespan, host_name=hostname
        )

    flow_df["TotalAllowedFlows"] = (
        flow_df["AllowedOutFlows"] + flow_df["AllowedInFlows"]
    )
    return flow_df


# %%
# Plot flows
def _plot_flows_by_protocol(flow_df):
    return nbdisplay.display_timeline(
        data=flow_df,
        group_by="L7Protocol",
        title="Network Flows by Protocol",
        time_column="FlowStartTime",
        source_columns=["FlowType", "AllExtIPs", "L7Protocol", "FlowDirection"],
        height=300,
        legend="right",
        yaxis=True,
    )


def _plot_flows_by_direction(flow_df):
    return nbdisplay.display_timeline(
        data=flow_df,
        group_by="FlowDirection",
        title="Network Flows by Direction",
        time_column="FlowStartTime",
        source_columns=["FlowType", "AllExtIPs", "L7Protocol", "FlowDirection"],
        height=300,
        legend="right",
        yaxis=True,
    )


# %%
# Plot flow values
def _plot_flow_values(flow_df, related_alert=None):
    return nbdisplay.display_timeline_values(
        data=flow_df,
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
        ref_event=related_alert,
        legend="right",
        height=500,
        kind=["vbar", "circle"],
    )


# %%
# Extract source and dest IPs
def _extract_flow_ips(flow_df):
    cols = [
        "VMName",
        "VMIPAddress",
        "PublicIPs",
        "SrcIP",
        "DestIP",
        "L4Protocol",
        "L7Protocol",
        "DestPort",
        "FlowDirection",
        "AllExtIPs",
        "TotalAllowedFlows",
    ]
    flow_index = flow_df[cols].copy()

    def get_source_ip(row):
        if row.FlowDirection == "O":
            return row.VMIPAddress if row.VMIPAddress else row.SrcIP
        return row.AllExtIPs if row.AllExtIPs else row.DestIP

    def get_dest_ip(row):
        if row.FlowDirection == "O":
            return row.AllExtIPs if row.AllExtIPs else row.DestIP
        return row.VMIPAddress if row.VMIPAddress else row.SrcIP

    flow_index["source"] = flow_index.apply(get_source_ip, axis=1)
    flow_index["dest"] = flow_index.apply(get_dest_ip, axis=1)
    return flow_index


def _get_flow_index_display(flow_summary_df):
    return (
        flow_summary_df[
            ["source", "dest", "L7Protocol", "FlowDirection", "TotalAllowedFlows"]
        ]
        .groupby(["source", "dest", "L7Protocol", "FlowDirection"])
        .sum()
        .reset_index()
        .style.bar(subset=["TotalAllowedFlows"], color="#d65f5f")
    )


# %%
# Flow Summary and Whois lookup
def _get_flow_summary(flow_index):
    flows_df = (
        flow_index[
            ["source", "dest", "L7Protocol", "FlowDirection", "TotalAllowedFlows"]
        ]
        .groupby(["source", "dest", "L7Protocol", "FlowDirection"])
        .sum()
        .reset_index()
    )

    num_ips = len(flows_df["source"].unique()) + len(flows_df["dest"].unique())

    print_data_wait("Whois")
    flows_df = get_whois_df(flows_df, ip_column="dest", asn_col="DestASN")
    flows_df = get_whois_df(flows_df, ip_column="source", asn_col="SourceASN")

    # Split the tuple returned by get_whois_info into separate columns
    flows_df["DestASNFull"] = flows_df.apply(lambda x: x.DestASN[1], axis=1)
    flows_df["DestASN"] = flows_df.apply(lambda x: x.DestASN[0], axis=1)
    flows_df["SourceASNFull"] = flows_df.apply(lambda x: x.SourceASN[1], axis=1)
    flows_df["SourceASN"] = flows_df.apply(lambda x: x.SourceASN[0], axis=1)

    flow_sum_df = (
        flows_df.groupby(["DestASN", "SourceASN"])
        .agg(
            TotalAllowedFlows=pd.NamedAgg(column="TotalAllowedFlows", aggfunc="sum"),
            L7Protocols=pd.NamedAgg(
                column="L7Protocol", aggfunc=lambda x: x.unique().tolist()
            ),
            source_ips=pd.NamedAgg(
                column="source", aggfunc=lambda x: x.unique().tolist()
            ),
            dest_ips=pd.NamedAgg(column="dest", aggfunc=lambda x: x.unique().tolist()),
        )
        .reset_index()
    )
    return flow_sum_df


# %%
# ASN Selection
def _get_source_host_asns(host_entity):
    host_ips = getattr(host_entity, "public_ips", [])
    host_ips.append(getattr(host_entity, "IpAddress", None))
    host_asns = []
    for host_ip in host_ips:
        if get_ip_type(host_ip) == "Public":
            host_ip.ASNDescription, host_ip.ASNDetails = get_whois_info(host_ip)
            host_asns.append(host_ip.ASNDescription)
    return host_asns


def _select_asn_subset(flow_sum_df, host_entity):
    our_host_asns = _get_source_host_asns(host_entity)
    all_asns = list(flow_sum_df["DestASN"].unique()) + list(
        flow_sum_df["SourceASN"].unique()
    )
    all_asns = set(all_asns) - set(["private address"])

    # Select the ASNs in the 25th percentile (lowest number of flows)
    quant_25pc = flow_sum_df["TotalAllowedFlows"].quantile(q=[0.25]).iat[0]
    quant_25pc_df = flow_sum_df[flow_sum_df["TotalAllowedFlows"] <= quant_25pc]
    other_asns = list(quant_25pc_df["DestASN"].unique()) + list(
        quant_25pc_df["SourceASN"].unique()
    )
    other_asns = set(other_asns) - set(our_host_asns)
    md("Choose IPs from Selected ASNs to look up for Threat Intel.", "bold")
    sel_asn = nbwidgets.SelectSubset(source_items=all_asns, default_selected=other_asns)

    return sel_asn


# %%
# Lookup ASN IPs with TILookup
def _get_ips_from_selected_asn(flow_sum_df, select_asn):
    dest_ips = set(
        chain.from_iterable(
            flow_sum_df[flow_sum_df["DestASN"].isin(select_asn.selected_items)][
                "dest_ips"
            ]
        )
    )
    src_ips = set(
        chain.from_iterable(
            flow_sum_df[flow_sum_df["SourceASN"].isin(select_asn.selected_items)][
                "source_ips"
            ]
        )
    )
    selected_ips = dest_ips | src_ips
    md(f"{len(selected_ips)} unique IPs in selected ASNs")
    return selected_ips


def _lookup_ip_ti(flows_df, ti_lookup, selected_ips):
    def ti_check_ser_sev(severity, threshold):
        threshold = TISeverity.parse(threshold)
        return severity.apply(lambda x: TISeverity.parse(x) >= threshold)

    # Add the IoCType to save cost of inferring each item
    md("Looking up TI...")
    selected_ip_dict = {ip: "ipv4" for ip in selected_ips}
    ti_results = ti_lookup.lookup_iocs(data=selected_ip_dict)

    md(f"{len(ti_results)} results received.")

    ti_results_pos = ti_results[ti_check_ser_sev(ti_results["Severity"], 1)]
    print(f"{len(ti_results_pos)} positive results found.")

    if not ti_results_pos.empty:
        src_pos = flows_df.merge(ti_results_pos, left_on="source", right_on="Ioc")
        dest_pos = flows_df.merge(ti_results_pos, left_on="dest", right_on="Ioc")
        ti_ip_results = pd.concat([src_pos, dest_pos])
        md_warn("Positive Threat Intel Results found for the following flows")
        md(
            "Please examine these IP flows using the IP Explorer notebook.",
            "bold, large",
        )
        return ti_ip_results
    return None


# %%
# display GeoLocations of IPs
def _format_ip_entity(ip_loc, row, ip_col):
    ip_entity = entities.IpAddress(Address=row[ip_col])
    ip_loc.lookup_ip(ip_entity=ip_entity)
    ip_entity.AdditionalData["protocol"] = row.L7Protocol
    if "severity" in row:
        ip_entity.AdditionalData["threat severity"] = row["severity"]
    if "Details" in row:
        ip_entity.AdditionalData["threat details"] = row["Details"]
    return ip_entity


def _display_geo_map_all(flow_df, host_entity):
    ip_locator = GeoLiteLookup()
    # from msticpy.nbtools.foliummap import FoliumMap
    folium_map = foliummap.FoliumMap(zoom_start=4)
    if flow_df is None or flow_df.empty:
        print("No network flow data available.")
        return None

    # Get the flow records for all flows not in the TI results
    selected_out = flow_df

    if selected_out.empty:
        ips_out = []
    else:
        print_data_wait("IP Geolocation")
        ips_out = list(
            selected_out.apply(
                lambda x: _format_ip_entity(ip_locator, x, "dest"), axis=1
            )
        )

    selected_in = flow_df
    if selected_in.empty:
        ips_in = []
    else:
        print_data_wait("IP Geolocation")
        ips_in = list(
            selected_in.apply(
                lambda x: _format_ip_entity(ip_locator, x, "source"), axis=1
            )
        )

    md("External IP Addresses communicating with host", "large")
    md("Numbered circles indicate multiple items - click to expand")
    md("Location markers: <br>Blue = outbound, Purple = inbound, Green = Host")

    icon_props = {"color": "green"}
    for ips in host_entity.public_ips:
        ips.AdditionalData["host"] = host_entity.HostName
    folium_map.add_ip_cluster(ip_entities=host_entity.public_ips, **icon_props)
    icon_props = {"color": "blue"}
    folium_map.add_ip_cluster(ip_entities=ips_out, **icon_props)
    icon_props = {"color": "purple"}
    folium_map.add_ip_cluster(ip_entities=ips_in, **icon_props)
    folium_map.center_map()
    display(folium_map)
    return folium_map


def _display_geo_map(flow_df, host_entity, ti_results, select_asn):
    ip_locator = GeoLiteLookup()
    # from msticpy.nbtools.foliummap import FoliumMap
    folium_map = foliummap.FoliumMap(zoom_start=4)
    if flow_df is None or flow_df.empty:
        print("No network flow data available.")
        return None

    # Get the flow records for all flows not in the TI results
    selected_out = flow_df[flow_df["DestASN"].isin(select_asn.selected_items)]
    selected_in = flow_df[flow_df["SourceASN"].isin(select_asn.selected_items)]
    if ti_results is not None and not ti_results.empty:
        selected_out = selected_out[~selected_out["dest"].isin(ti_results["Ioc"])]
        selected_in = selected_in[~selected_in["source"].isin(ti_results["Ioc"])]

    if selected_out.empty:
        ips_out = []
    else:
        print_data_wait("IP Geolocation")
        ips_out = list(
            selected_out.apply(
                lambda x: _format_ip_entity(ip_locator, x, "dest"), axis=1
            )
        )

    if selected_in.empty:
        ips_in = []
    else:
        print_data_wait("IP Geolocation")
        ips_in = list(
            selected_in.apply(
                lambda x: _format_ip_entity(ip_locator, x, "source"), axis=1
            )
        )

    md("External IP Addresses communicating with host", "large")
    md("Numbered circles indicate multiple items - click to expand")
    md(
        "Location markers: <br>Blue = outbound, Purple = inbound, "
        + " Green = Host, Red = Threats"
    )

    icon_props = {"color": "green"}
    for ip_addr in host_entity.public_ips:
        ip_addr.AdditionalData["host"] = host_entity.HostName
    folium_map.add_ip_cluster(ip_entities=host_entity.public_ips, **icon_props)
    icon_props = {"color": "blue"}
    folium_map.add_ip_cluster(ip_entities=ips_out, **icon_props)
    icon_props = {"color": "purple"}
    folium_map.add_ip_cluster(ip_entities=ips_in, **icon_props)
    if ti_results is not None and not ti_results.empty:
        ips_threats = list(
            ti_results.apply(lambda x: _format_ip_entity(ip_locator, x, "Ioc"), axis=1)
        )
        icon_props = {"color": "red"}
        folium_map.add_ip_cluster(ip_entities=ips_threats, **icon_props)
    folium_map.center_map()
    display(folium_map)
    return folium_map
