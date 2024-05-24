# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklet for Network Flow Summary."""
from ipaddress import ip_address
from itertools import chain
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd
from bokeh.models import LayoutDOM
from IPython.display import display
from msticpy.common.timespan import TimeSpan
from msticpy.datamodel import entities

try:
    from msticpy import nbwidgets
    from msticpy.context.ip_utils import get_ip_type, get_whois_df
    from msticpy.context.ip_utils import ip_whois as get_whois_info
    from msticpy.context.tiproviders.ti_provider_base import ResultSeverity
    from msticpy.vis import foliummap
    from msticpy.vis.timeline import display_timeline, display_timeline_values
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.nbtools import foliummap, nbwidgets
    from msticpy.nbtools.nbdisplay import display_timeline, display_timeline_values
    from msticpy.sectools.ip_utils import get_ip_type, get_whois_df, get_whois_info
    from msticpy.sectools.tiproviders.ti_provider_base import ResultSeverity

from .... import nb_metadata
from ...._version import VERSION
from ....common import (
    MsticnbMissingParameterError,
    nb_data_wait,
    nb_markdown,
    nb_warn,
    set_text,
)
from ....data_providers import DataProviders
from ....nblib.azsent.host import get_aznet_topology, get_heartbeat
from ....notebooklet import NBMetadata, Notebooklet, NotebookletResult

__version__ = VERSION
__author__ = "Ian Hellen"


_CLS_METADATA: NBMetadata
_CELL_DOCS: Dict[str, Any]
_CLS_METADATA, _CELL_DOCS = nb_metadata.read_mod_metadata(__file__, __name__)


# pylint: disable=too-few-public-methods, too-many-instance-attributes
class NetworkFlowResult(NotebookletResult):
    """
    Network Flow Details Results.

    Attributes
    ----------
    host_entity : msticpy.datamodel.entities.Host
        The host entity object contains data about the host
        such as name, environment, operating system version,
        IP addresses and Azure VM details. Depending on the
        type of host, not all of this data may be populated.
    network_flows : pd.DataFrame
        The raw network flows recorded for this host.
    plot_flows_by_protocol : LayoutDOM
        Bokeh timeline plot of flow events by protocol.
    plot_flows_by_direction : LayoutDOM
        Bokeh timeline plot of flow events by direction (in/out).
    plot_flow_values : LayoutDOM
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

    def __init__(
        self,
        description: Optional[str] = None,
        timespan: Optional[TimeSpan] = None,
        notebooklet: Optional["Notebooklet"] = None,
    ):
        """
        Create new Notebooklet result instance.

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
        self.description: str = "Network flow results"
        self.host_entity: entities.Host = None
        self.network_flows: Optional[pd.DataFrame] = None
        self.plot_flows_by_protocol: Optional[LayoutDOM] = None
        self.plot_flows_by_direction: Optional[LayoutDOM] = None
        self.plot_flow_values: Optional[LayoutDOM] = None
        self.flow_index: Optional[pd.DataFrame] = None
        self.flow_index_data: Optional[pd.DataFrame] = None
        self.flow_summary: Optional[pd.DataFrame] = None
        self.ti_results: Optional[pd.DataFrame] = None
        self.geo_map: foliummap.FoliumMap = None


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
    __doc__ = nb_metadata.update_class_doc(__doc__, metadata)
    _cell_docs = _CELL_DOCS

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
    def run(  # noqa: MC0001, C901
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

        result = NetworkFlowResult(
            notebooklet=self, description=self.metadata.description, timespan=timespan
        )

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
            f"Network flow summary for {host_name or host_ip or 'unknown'}"
        )  # type: ignore

        flow_df = _get_az_net_flows(
            self.query_provider, self.timespan, host_ip, host_name
        )
        result.network_flows = flow_df

        if "resolve_host" in self.options or not hasattr(
            result.host_entity, "IpAddress"
        ):
            result.host_entity = _get_host_details(
                qry_prov=self.query_provider, host_entity=result.host_entity
            )
        if "plot_flows" in self.options:
            result.plot_flows_by_protocol = _plot_flows_by_protocol(flow_df)
            result.plot_flows_by_direction = _plot_flows_by_direction(flow_df)
        if "plot_flow_values" in self.options:
            result.plot_flow_values = _plot_flow_values(flow_df)
        flow_index = None
        if "flow_summary" in self.options:
            flow_index = _extract_flow_ips(flow_df)
            result.flow_index = _get_flow_index(flow_index)
            if not self.silent:
                display(result.flow_index)
            result.flow_summary = _get_flow_summary(flow_index)
            if not self.silent:
                display(result.flow_summary)
            result.flow_index_data = flow_index
        if "geo_map" in self.options and flow_index is not None:
            geo_lookup = self.get_provider("geolitelookup") or self.get_provider(
                "ipstacklookup"
            )
            result.geo_map = _display_geo_map_all(
                flow_index=flow_index,
                ip_locator=geo_lookup,
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
        self._last_result.ti_results = _lookup_ip_ti(
            flows_df=self._last_result.flow_index_data,
            selected_ips=selected_ips,
            ti_lookup=self.data_providers["tilookup"],
        )

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
        geo_lookup = self.get_provider("geolitelookup") or self.get_provider(
            "ipstacklookup"
        )
        geo_map = _display_geo_map(
            flow_index=self._last_result.flow_summary,
            ip_locator=geo_lookup,
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
    return display_timeline(
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
    return display_timeline(
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
    return display_timeline_values(
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
            return row.VMIPAddress or row.SrcIP
        return row.AllExtIPs or row.DestIP

    def get_dest_ip(row):
        if row.FlowDirection == "O":
            return row.AllExtIPs or row.DestIP
        return row.VMIPAddress or row.SrcIP

    flow_index["source"] = flow_index.apply(get_source_ip, axis=1)
    flow_index["dest"] = flow_index.apply(get_dest_ip, axis=1)

    return flow_index


@set_text(docs=_CELL_DOCS, key="get_flow_index")
def _get_flow_index(flow_summary_df):
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
    asn_columns = []
    if flows_df["dest"].apply(get_ip_type).unique() != ["Private"]:
        flows_df = get_whois_df(
            flows_df,
            ip_column="dest",
            asn_col="DestASN",
            whois_col="DestASNFull",
            show_progress=True,
        )
        asn_columns.append("DestASN")
    if flows_df["source"].apply(get_ip_type).unique() != ["Private"]:
        flows_df = get_whois_df(
            flows_df,
            ip_column="source",
            asn_col="SourceASN",
            whois_col="SourceASNFull",
            show_progress=True,
        )
        asn_columns.append("SourceASN")

    if isinstance(flows_df, pd.DataFrame) and not flows_df.empty:
        return (
            flows_df.groupby(asn_columns)
            .agg(
                TotalAllowedFlows=pd.NamedAgg(
                    column="TotalAllowedFlows", aggfunc="sum"
                ),
                L7Protocols=pd.NamedAgg(
                    column="L7Protocol", aggfunc=lambda x: x.unique().tolist()
                ),
                source_ips=pd.NamedAgg(
                    column="source", aggfunc=lambda x: x.unique().tolist()
                ),
                dest_ips=pd.NamedAgg(
                    column="dest", aggfunc=lambda x: x.unique().tolist()
                ),
            )
            .reset_index()
        )

    return None


# %%
# ASN Selection
def _get_source_host_asns(host_entity):
    host_ips = getattr(host_entity, "PublicIpAddresses", [])
    host_ips.append(getattr(host_entity, "IpAddress", None))
    host_asns = []
    for ip_entity in host_ips:
        if get_ip_type(ip_entity.Address) == "Public":
            ip_entity.ASNDescription, ip_entity.ASNDetails = get_whois_info(
                ip_entity.Address
            )
            host_asns.append(ip_entity.ASNDescription)
    return host_asns


@set_text(docs=_CELL_DOCS, key="select_asn_subset")
def _select_asn_subset(flow_sum_df, host_entity):
    our_host_asns = _get_source_host_asns(host_entity)
    all_asns: List[str] = []
    other_asns: List[str] = []

    # Select the ASNs in the 25th percentile (lowest number of flows)
    quant_25pc = flow_sum_df["TotalAllowedFlows"].quantile(q=[0.25]).iat[0]
    quant_25pc_df = flow_sum_df[flow_sum_df["TotalAllowedFlows"] <= quant_25pc]

    if "DestASN" in flow_sum_df.columns:
        all_asns.extend(flow_sum_df["DestASN"].unique())
        other_asns.extend(quant_25pc_df["DestASN"].unique())
    if "SourceASN" in flow_sum_df.columns:
        all_asns.extend(flow_sum_df["SourceASN"].unique())
        other_asns.extend(quant_25pc_df["SourceASN"].unique())
    all_asns = set(all_asns) - {"private address"}
    other_asns = set(other_asns) - set(our_host_asns)
    return nbwidgets.SelectSubset(source_items=all_asns, default_selected=other_asns)


# %%
# Lookup ASN IPs with TILookup
def _get_ips_from_selected_asn(flow_sum_df, select_asn):
    dest_ips: Set[str] = set()
    src_ips: Set[str] = set()
    if "DestASN" in flow_sum_df.columns:
        dest_ips = set(
            chain.from_iterable(
                flow_sum_df[flow_sum_df["DestASN"].isin(select_asn.selected_items)][
                    "dest_ips"
                ]
            )
        )
    if "SourceASN" in flow_sum_df.columns:
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
        threshold = ResultSeverity.parse(threshold)
        return severity.apply(lambda x: ResultSeverity.parse(x) >= threshold)

    # Add the IoCType to save cost of inferring each item
    nb_data_wait("Threat Intelligence")
    selected_ip_dict = {ip: "ipv4" for ip in selected_ips}
    ti_results = ti_lookup.lookup_iocs(data=selected_ip_dict)

    nb_markdown(f"{len(ti_results)} TI results received.")
    if ti_results.empty:
        return pd.DataFrame(columns=["Ioc"])

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
    return pd.DataFrame(columns=["Ioc"])


# %%
# display GeoLocations of IPs
def _format_ip_entity(ip_loc, row, ip_col):
    ip_entity = entities.IpAddress(Address=row[ip_col])
    ip_loc.lookup_ip(ip_entity=ip_entity)
    if "L7Protocol" in row:
        ip_entity.AdditionalData["protocol"] = row.L7Protocol
    if "severity" in row:
        ip_entity.AdditionalData["threat severity"] = row["severity"]
    if "Details" in row:
        ip_entity.AdditionalData["threat details"] = row["Details"]
    return ip_entity


# pylint: disable=too-many-branches
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
    host_ips = getattr(host_entity, "PublicIpAddresses", [])
    host_ip = getattr(host_entity, "IpAddress", None)
    if host_ip:
        host_ips.append(host_ip)
    if host_ips:
        for ips in host_ips:
            ips.AdditionalData["host"] = host_entity.HostName or "unknown hostname"
        folium_map.add_ip_cluster(ip_entities=host_ips, **icon_props)
    icon_props = {"color": "blue"}
    folium_map.add_ip_cluster(ip_entities=ips_out, **icon_props)
    icon_props = {"color": "purple"}
    folium_map.add_ip_cluster(ip_entities=ips_in, **icon_props)
    folium_map.center_map()
    return folium_map


# pylint: enable=too-many-branches


# pylint: disable=too-many-branches, too-many-locals
@set_text(docs=_CELL_DOCS, key="display_geo_map")
def _display_geo_map(flow_index, ip_locator, host_entity, ti_results, select_asn):
    folium_map = foliummap.FoliumMap(zoom_start=4)
    if flow_index is None or flow_index.empty:
        nb_markdown("No network flow data available.")
        return None

    ips_in: List[str] = []
    ips_out: List[str] = []
    # Get the flow records for all flows not in the TI results
    if "DestASN" in flow_index.columns:
        selected_out = flow_index[flow_index["DestASN"].isin(select_asn.selected_items)]
        sel_out_exp = selected_out.explode("dest_ips")
        sel_out_exp = sel_out_exp[~sel_out_exp["dest_ips"].isin(ti_results["Ioc"])]

        if not sel_out_exp.empty:
            nb_data_wait("IP Geolocation")
            ips_out = list(
                sel_out_exp.apply(
                    lambda x: _format_ip_entity(ip_locator, x, "dest_ips"), axis=1
                )
            )

    if "SourceASN" in flow_index.columns:
        selected_in = flow_index[
            flow_index["SourceASN"].isin(select_asn.selected_items)
        ]
        sel_in_exp = selected_in.explode("source_ips")
        sel_in_exp = sel_in_exp[~sel_in_exp["source_ips"].isin(ti_results["Ioc"])]

        if not sel_in_exp.empty:
            nb_data_wait("IP Geolocation")
            ips_in = list(
                sel_in_exp.apply(
                    lambda x: _format_ip_entity(ip_locator, x, "source_ips"), axis=1
                )
            )

    icon_props = {"color": "green"}
    host_ips = getattr(host_entity, "PublicIpAddresses", [])
    host_ip = getattr(host_entity, "IpAddress", None)
    if host_ip:
        host_ips.append(host_ip)
    if host_ips:
        for ip_addr in host_ips:
            ip_addr.AdditionalData["host"] = host_entity.HostName or "unknown hostname"
        folium_map.add_ip_cluster(ip_entities=host_ips, **icon_props)
    icon_props = {"color": "blue"}
    folium_map.add_ip_cluster(ip_entities=ips_out, **icon_props)
    icon_props = {"color": "purple"}
    folium_map.add_ip_cluster(ip_entities=ips_in, **icon_props)
    if not (ti_results is None or ti_results.empty):
        ips_threats = list(
            ti_results.apply(lambda x: _format_ip_entity(ip_locator, x, "Ioc"), axis=1)
        )
        icon_props = {"color": "red"}
        folium_map.add_ip_cluster(ip_entities=ips_threats, **icon_props)
    folium_map.center_map()

    return folium_map
