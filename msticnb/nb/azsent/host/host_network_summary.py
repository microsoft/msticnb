# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklet for Host Summary."""
from functools import lru_cache
from typing import Any, Dict, Iterable, Optional

import msticpy
import pandas as pd
from bokeh.models import LayoutDOM
from IPython.display import display

try:
    from msticpy.context.ip_utils import ip_whois as get_whois_info
    from msticpy.vis.foliummap import FoliumMap
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.nbtools.foliummap import FoliumMap
    from msticpy.sectools.ip_utils import get_whois_info

from msticpy.common.timespan import TimeSpan
from msticpy.common.utility import md
from msticpy.datamodel.entities import Host

from ...._version import VERSION
from ....common import (
    MsticnbDataProviderError,
    MsticnbMissingParameterError,
    nb_data_wait,
    nb_markdown,
    set_text,
)
from ....nb_metadata import read_mod_metadata, update_class_doc
from ....nblib.ti import get_ti_results
from ....notebooklet import NBMetadata, Notebooklet, NotebookletResult

__version__ = VERSION
__author__ = "Pete Bryan"


_MSTICPY_VER = msticpy.__version__
_CLS_METADATA: NBMetadata
_CELL_DOCS: Dict[str, Any]
_CLS_METADATA, _CELL_DOCS = read_mod_metadata(__file__, __name__)


# pylint: disable=too-few-public-methods
class HostNetworkSummaryResult(NotebookletResult):
    """Host Network Summary Results."""

    def __init__(
        self,
        description: Optional[str] = None,
        timespan: Optional[TimeSpan] = None,
        notebooklet: Optional["Notebooklet"] = None,
    ):
        """Create new Notebooklet result instance."""
        super().__init__(description, timespan, notebooklet)
        self.flows: Optional[pd.DataFrame] = None
        self.flow_matrix: Optional[LayoutDOM] = None
        self.flow_whois: Optional[pd.DataFrame] = None
        self.flow_map: Optional[FoliumMap] = None
        self.flow_ti: Optional[pd.DataFrame] = None


# pylint: disable=too-few-public-methods
class HostNetworkSummary(Notebooklet):
    """
    HostSummary Notebooklet class.

    Queries and displays information about a host including:

    - IP address assignment
    - Related alerts
    - Related hunting/investigation bookmarks
    - Azure subscription/resource data.

    """

    metadata = _CLS_METADATA
    __doc__ = update_class_doc(__doc__, metadata)
    _cell_docs = _CELL_DOCS

    def __init__(self, *args, **kwargs):
        """Initialize the Host Network Summary notebooklet."""
        super().__init__(*args, **kwargs)

    # pylint: disable=too-many-branches, too-many-locals
    @set_text(docs=_CELL_DOCS, key="run")  # noqa: MC0001
    def run(  # noqa:MC0001, C901
        self,
        value: Any = None,
        data: Optional[pd.DataFrame] = None,
        timespan: Optional[TimeSpan] = None,
        options: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> HostNetworkSummaryResult:
        """
        Return host summary data.

        Parameters
        ----------
        value : str
            Host entity
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

        self.timespan = timespan

        # pylint: disable=attribute-defined-outside-init
        result = HostNetworkSummaryResult(
            notebooklet=self, description=self.metadata.description, timespan=timespan
        )

        if isinstance(value, Host):
            host_name = value.HostName
            ip_addr = value.IpAddress.Address if "IpAddress" in value else None
        elif isinstance(value, tuple):
            host_name, ip_addr = value
        else:
            raise ValueError(
                "Could not determine host name or IP address from value parameter."
                "Please supply host and ip address in the form of a Host entity",
                "or tuple of (host_name, ip_address).",
            )

        if not host_name and not ip_addr:
            md(f"Could not obtain unique host name from {value}. Aborting.")
            self._last_result = result
            return self._last_result

        result.flows = _get_host_flows(
            host_name=host_name,
            ip_addr=ip_addr,
            qry_prov=self.query_provider,
            timespan=self.timespan,
        )
        if result.flows is None:
            nb_markdown("No network flow data found.")
            self._last_result = result
            return self._last_result

        remote_ip_col = "RemoteIP"
        local_ip_col = "LocalIP"
        if "SourceIP" in result.flows.columns:
            remote_ip_col = "DestinationIP"
            local_ip_col = "SourceIP"
        if not result.flows.empty:
            result.flow_matrix = result.flows.mp_plot.matrix(
                x=remote_ip_col, y=local_ip_col, title="IP Interaction", sort="asc"
            )

        flows_remote_ips = result.flows[[remote_ip_col]].drop_duplicates()
        flows_source_ips = (
            result.flows[[local_ip_col]]
            .drop_duplicates()
            .rename(columns={local_ip_col: remote_ip_col})
        )
        flows_all = pd.concat([flows_remote_ips, flows_source_ips]).drop_duplicates()
        if "ti" in self.options:
            if "tilookup" in self.data_providers.providers:
                ti_prov = self.data_providers.providers["tilookup"]
            else:
                raise MsticnbDataProviderError("No TI providers available")
            ti_results, ti_results_merged = get_ti_results(
                ti_prov, flows_all, remote_ip_col
            )
            if isinstance(ti_results, pd.DataFrame) and not ti_results.empty:
                result.flow_ti = ti_results_merged

        if (
            "map" in self.options
            and isinstance(flows_all, pd.DataFrame)
            and not flows_all.empty
        ):
            result.flow_map = flows_all.mp_plot.folium_map(ip_column=remote_ip_col)

        if "whois" in self.options:
            result.flow_whois = _get_whois_data(flows_all, col=remote_ip_col)

        self._last_result = result

        if not self.silent:
            self._display_results()

        return self._last_result

    @set_text(docs=_CELL_DOCS, key="flows")
    def _display_flows(self):
        if self.check_valid_result_data("flow_whois", silent=True):
            display(self._last_result.flow_whois)
        elif self.check_valid_result_data("flows", silent=True):
            display(self._last_result.flows)
        else:
            nb_markdown("No network flow data found.")

    @set_text(docs=_CELL_DOCS, key="ti")
    def _display_ti_results(self):
        if self.check_valid_result_data("flow_ti", silent=True):
            display(self._last_result.flow_ti)
        else:
            nb_markdown("No Threat Intelligence results found.")

    @set_text(docs=_CELL_DOCS, key="map")
    def _display_map(self):
        if (
            self.check_valid_result_data("flows", silent=True)
            and self._last_result.flow_map
        ):
            display(self._last_result.flow_map)

    @set_text(docs=_CELL_DOCS, key="matrix")
    def _display_matrix(self):
        if self._last_result.flow_matrix:
            display(self._last_result.flow_matrix)

    def _display_results(self):
        self._display_flows()
        self._display_ti_results()
        self._display_map()
        self._display_matrix()


@lru_cache()
def _get_host_flows(host_name, ip_addr, qry_prov, timespan) -> Optional[pd.DataFrame]:
    if host_name:
        nb_data_wait("Host flow events")
        host_flows = qry_prov.MDE.host_connections(timespan, host_name=host_name)
        host_flows["SourceIP"] = host_flows["LocalIP"]
        host_flows["DestinationIP"] = host_flows["RemoteIP"]
        host_flows_csl = qry_prov.Network.host_network_connections_csl(
            timespan, host_name=host_name
        )
    elif ip_addr:
        nb_data_wait("Host flow events")
        host_flows = qry_prov.Network.list_azure_network_flows_by_ip(
            timespan, ip_address_list=[ip_addr]
        )
        host_flows_csl = qry_prov.Network.ip_network_connections_csl(
            timespan, ip=ip_addr
        )
    else:
        return None
    return pd.concat([host_flows, host_flows_csl], sort=False)


def _get_whois_data(data, col) -> pd.DataFrame:
    if not data.empty:
        if _MSTICPY_VER < "2.13.0":
            data["ASN"] = data.apply(lambda x: get_whois_info(x[col]), axis=1)
        else:
            data["ASN"] = data.apply(
                lambda x: get_whois_info(x[col], True).name, axis=1
            )
            data["ASNProperties"] = data.apply(
                lambda x: get_whois_info(x[col], True).properties, axis=1
            )
    return data
