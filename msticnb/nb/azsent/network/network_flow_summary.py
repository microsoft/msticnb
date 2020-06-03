# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklet for Network Flow Summary."""
from ipaddress import ip_address
from itertools import chain
from typing import Any, Optional, Iterable, Tuple, Dict

import attr
from bokeh.plotting.figure import Figure
from IPython.display import display
import pandas as pd

from msticpy.nbtools import nbwidgets, nbdisplay
from msticpy.nbtools import entities, foliummap
from msticpy.sectools.ip_utils import get_whois_df, get_whois_info, get_ip_type
from msticpy.sectools.tiproviders.ti_provider_base import TISeverity

from ....common import (
    TimeSpan,
    MsticnbMissingParameterError,
    nb_data_wait,
    set_text,
    nb_markdown,
    nb_warn,
)
from ....data_providers import DataProviders
from ....notebooklet import Notebooklet, NotebookletResult, NBMetaData
from ....nblib.azsent.host import get_heartbeat, get_aznet_topology
from ....nb_metadata import read_mod_metadata

from ...._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


_CLS_METADATA: NBMetaData
_CELL_DOCS: Dict[str, Any]
_CLS_METADATA, _CELL_DOCS = read_mod_metadata(__file__, __name__)


# pylint: disable=too-few-public-methods, too-many-instance-attributes
@attr.s(auto_attribs=True)
class NetworkFlowResult(NotebookletResult):
    """
    Network Flow Details Results.

    Attributes
    ----------
    host_entity : msticpy.data.nbtools.entities.Host
        The host entity object contains data about the host
        such as name, environment, operating system version,
        IP addresses and Azure VM details. Depending on the
        type of host, not all of this data may be populated.
    network_flows : pd.DataFrame
        The raw network flows recorded for this host.
    plot_flows_by_protocol : Figure
        Bokeh timeline plot of flow events by protocol.
    plot_flows_by_direction : Figure
        Bokeh timeline plot of flow events by direction (in/out).
    plot_flow_values : Figure
        Bokeh values plot of flow events by protocol.
    flow_index : pd.DataFrame
        Summarized DataFrame of flows
    flow_index_data : pd.DataFrame
        Raw summary data of flows.
    flow_summary : pd.DataFrame
        Summarized flows grouped by ASN
    ti_results : pd.DataFrame
        Threat Intelligence results for selected IP Addreses.
    geo_map : foliummap.FoliumMap
        Folium map showing locations of all IP Addresses.
    geo_map_selected : foliummap.FoliumMap
        Folium map showing locations of selected IP Addresses.

    """

    description: str = "Network flow results"
    host_entity: entities.Host = None
    network_flows: pd.DataFrame = None
    plot_flows_by_protocol: Figure = None
    plot_flows_by_direction: Figure = None
    plot_flow_values: Figure = None
    flow_index: pd.DataFrame = None
    flow_index_data: pd.DataFrame = None
    flow_summary: pd.DataFrame = None
    ti_results: pd.DataFrame = None
    geo_map: foliummap.FoliumMap = None


class NetworkFlowSummary(Notebooklet):
    """
    Network Flow Summary Notebooklet class.

    Queries network data and plots time lines for network
    traffic to/from a host or IP address.

    - Plot flows events by protocol and direction
    - Plot flow count by protocol
    - Display flow summary table
    - Display flow summary by ASN
    - Display results on map

    Methods
    -------
    - run: main method for notebooklet.
    - select_asns: Open an interactive dialog to choose which ASNs to
      investigate further.
    - lookup_ti_for_asn_ips: For selected ASNs, lookup Threat Intelligence
      data for the IPs belonging to those ASNs.
    - show_selected_asn_map: Show IP address locations for selected IP
      (including any threats highlighted)

    """

    # assign metadata from YAML to class variable
    metadata = _CLS_METADATA

    def __init__(self, data_providers: Optional[DataProviders] = None, **kwargs):
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
        self.flow_index_data = pd.DataFrame()

    # pylint: disable=too-many-branches
    @set_text(docs=_CELL_DOCS, key="run")  # noqa: MC0001
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
        HostNetworkResult
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

        flow_df = _get_az_net_flows(
            self.query_provider, self.timespan, host_ip, host_name
        )
        result.network_flows = flow_df

        if "resolve_host" in self.options:
            result.host_entity = _get_host_details(
                qry_prov=self.query_provider, host_entity=result.host_entity
            )
        if "plot_flows" in self.options:
            result.plot_flows_by_protocol = _plot_flows_by_protocol(flow_df)
            result.plot_flows_by_direction = _plot_flows_by_direction(flow_df)
        if "plot_flow_values" in self.options:
            result.plot_flow_values = _plot_flow_values(flow_df)
        if "flow_summary" in self.options:
            flow_index = _extract_flow_ips(flow_df)
            result.flow_index = _get_flow_index(flow_index)
            if not self.silent:
                display(result.flow_index)
            result.flow_summary = _get_flow_summary(flow_index)
            if not self.silent:
                display(result.flow_summary)
            result.flow_index_data = flow_index
        if "geo_map" in self.options:
            result.geo_map = _display_geo_map_all(
                flow_index=flow_index,
                ip_locator=self.data_providers["geolitelookup"],
                host_entity=result.host_entity,
            )
            if not self.silent:
                display(result.geo_map)

        nb_markdown("Select ASNs to examine using select_asns()")
        nb_markdown(
            "Lookup threat intel for IPs from selected ASNs using"
            + " lookup_ti_for_asn_ips()"
        )
        nb_markdown("Display Geolocation of threats with show_selected_asn_map()")
        nb_markdown("For usage type 'help(NetworkFlowSummary.function_name)'")

        # pylint: disable=attribute-defined-outside-init
        # (defined in parent class)
        self._last_result = result
        return self._last_result

    def select_asns(self):
        """Show interactive selector to choose which ASNs to process."""
        if not self._last_result or self._last_result.flow_summary is None:
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
        """Lookup Threat Intel data for IPs of selected ASNs."""
        if (
            not self._last_result
            or self._last_result.flow_summary is None
            or not self.asn_selector
        ):
            print(
                "Please use 'run()' with 'flow_summary' option before using",
                "this method.\n",
                "Then call 'select_asns()' to select the ASNs to lookup.\n",
                "Then call 'lookup_ti_for_asn_ips()'.",
            )
            return

        selected_ips = _get_ips_from_selected_asn(
            flow_sum_df=self._last_result.flow_summary, select_asn=self.asn_selector
        )
        ti_results = _lookup_ip_ti(
            flows_df=self._last_result,
            selected_ips=selected_ips,
            ti_lookup=self.data_providers["tilookup"],
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
            or self._last_result.flow_summary is None
            or not self.asn_selector
        ):
            print(
                "Please use 'run()' with 'flow_summary' option before using",
                "this method. Then run 'select_asns()' (and optionally)",
                "'lookup_ti_for_asn_ips()'.",
                "\nThen call 'show_selected_asn_map()'",
            )
            return None
        geo_map = _display_geo_map(
            flow_index=self._last_result.flow_index_data,
            ip_locator=self.data_providers["geolitelookup"],
            host_entity=self._last_result.host_entity,
            ti_results=self._last_result.ti_results,
            select_asn=self.asn_selector,
        )
        if self.silent:
            display(geo_map)
        return geo_map


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

    host_entity = get_heartbeat(qry_prov=qry_prov, host_ip=host_ip, host_name=host_name)
    get_aznet_topology(
        qry_prov=qry_prov, host_ip=host_ip, host_entity=host_entity, host_name=host_name
    )
    return host_entity


# %%
# Get network flows
def _get_az_net_flows(qry_prov, timespan, ip_addr, hostname):
    nb_data_wait("AzureNetworkAnalytics")
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
@set_text(docs=_CELL_DOCS, key="plot_flows_by_protocol")
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


@set_text(docs=_CELL_DOCS, key="plot_flows_by_direction")
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
@set_text(docs=_CELL_DOCS, key="plot_flow_values")
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


@set_text(docs=_CELL_DOCS, key="get_flow_index")
def _get_flow_index(flow_summary_df):
    flow_index_df = (
        flow_summary_df[
            ["source", "dest", "L7Protocol", "FlowDirection", "TotalAllowedFlows"]
        ]
        .groupby(["source", "dest", "L7Protocol", "FlowDirection"])
        .sum()
        .reset_index()
        .style.bar(subset=["TotalAllowedFlows"], color="#d65f5f")
    )
    return flow_index_df


# %%
# Flow Summary and Whois lookup
@set_text(docs=_CELL_DOCS, key="get_flow_summary")
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
    nb_markdown(f"Found {num_ips} unique IP Addresses.")

    nb_data_wait("Whois")
    flows_df = get_whois_df(
        flows_df,
        ip_column="dest",
        asn_col="DestASN",
        whois_col="DestASNFull",
        show_progress=True,
    )
    flows_df = get_whois_df(
        flows_df,
        ip_column="source",
        asn_col="SourceASN",
        whois_col="SourceASNFull",
        show_progress=True,
    )

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


@set_text(docs=_CELL_DOCS, key="select_asn_subset")
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
    nb_markdown(f"{len(selected_ips)} unique IPs in selected ASNs")
    return selected_ips


@set_text(docs=_CELL_DOCS, key="lookup_ip_ti")
def _lookup_ip_ti(flows_df, ti_lookup, selected_ips):
    def ti_check_ser_sev(severity, threshold):
        threshold = TISeverity.parse(threshold)
        return severity.apply(lambda x: TISeverity.parse(x) >= threshold)

    # Add the IoCType to save cost of inferring each item
    nb_data_wait("Threat Intelligence")
    selected_ip_dict = {ip: "ipv4" for ip in selected_ips}
    ti_results = ti_lookup.lookup_iocs(data=selected_ip_dict)

    nb_markdown(f"{len(ti_results)} TI results received.")

    ti_results_pos = ti_results[ti_check_ser_sev(ti_results["Severity"], 1)]
    nb_markdown(f"{len(ti_results_pos)} positive results found.")

    if not ti_results_pos.empty:
        src_pos = flows_df.merge(ti_results_pos, left_on="source", right_on="Ioc")
        dest_pos = flows_df.merge(ti_results_pos, left_on="dest", right_on="Ioc")
        ti_ip_results = pd.concat([src_pos, dest_pos])
        nb_warn("Positive Threat Intel Results found for the following flows")
        nb_markdown(
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


@set_text(docs=_CELL_DOCS, key="display_geo_map_all")
def _display_geo_map_all(flow_index, ip_locator, host_entity):
    folium_map = foliummap.FoliumMap(zoom_start=4)
    if flow_index is None or flow_index.empty:
        nb_markdown("No network flow data available.")
        return None

    # Get the flow records for all flows not in the TI results
    selected_out = flow_index

    if selected_out.empty:
        ips_out = []
    else:
        nb_data_wait("IP Geolocation")
        ips_out = list(
            selected_out.apply(
                lambda x: _format_ip_entity(ip_locator, x, "dest"), axis=1
            )
        )

    selected_in = flow_index
    if selected_in.empty:
        ips_in = []
    else:
        nb_data_wait("IP Geolocation")
        ips_in = list(
            selected_in.apply(
                lambda x: _format_ip_entity(ip_locator, x, "source"), axis=1
            )
        )

    icon_props = {"color": "green"}
    for ips in host_entity.public_ips:
        ips.AdditionalData["host"] = host_entity.HostName
    folium_map.add_ip_cluster(ip_entities=host_entity.public_ips, **icon_props)
    icon_props = {"color": "blue"}
    folium_map.add_ip_cluster(ip_entities=ips_out, **icon_props)
    icon_props = {"color": "purple"}
    folium_map.add_ip_cluster(ip_entities=ips_in, **icon_props)
    folium_map.center_map()
    return folium_map


# pylint: disable=too-many-branches
@set_text(docs=_CELL_DOCS, key="display_geo_map")
def _display_geo_map(flow_index, ip_locator, host_entity, ti_results, select_asn):
    folium_map = foliummap.FoliumMap(zoom_start=4)
    if flow_index is None or flow_index.empty:
        nb_markdown("No network flow data available.")
        return None

    # Get the flow records for all flows not in the TI results
    selected_out = flow_index[flow_index["DestASN"].isin(select_asn.selected_items)]
    selected_in = flow_index[flow_index["SourceASN"].isin(select_asn.selected_items)]
    if ti_results is not None and not ti_results.empty:
        selected_out = selected_out[~selected_out["dest"].isin(ti_results["Ioc"])]
        selected_in = selected_in[~selected_in["source"].isin(ti_results["Ioc"])]

    if selected_out.empty:
        ips_out = []
    else:
        nb_data_wait("IP Geolocation")
        ips_out = list(
            selected_out.apply(
                lambda x: _format_ip_entity(ip_locator, x, "dest"), axis=1
            )
        )

    if selected_in.empty:
        ips_in = []
    else:
        nb_data_wait("IP Geolocation")
        ips_in = list(
            selected_in.apply(
                lambda x: _format_ip_entity(ip_locator, x, "source"), axis=1
            )
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

    return folium_map
