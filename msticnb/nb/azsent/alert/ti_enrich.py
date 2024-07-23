# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Alert TI enrichment - provides enrichment of alerts with threat intelligence."""
import json
from typing import Any, Dict, Iterable, Optional

import pandas as pd
from IPython.display import display
from msticpy.common.timespan import TimeSpan
from msticpy.common.utility import md
from tqdm.notebook import tqdm

# pylint: disable=ungrouped-imports
try:
    from msticpy.nbwidgets import SelectAlert
    from msticpy.vis.foliummap import FoliumMap, get_center_ip_entities
    from msticpy.vis.nbdisplay import format_alert
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.nbtools.foliummap import FoliumMap, get_center_ip_entities
    from msticpy.nbtools.nbdisplay import format_alert
    from msticpy.nbtools.nbwidgets import SelectAlert

from msticpy.nbtools.security_alert import SecurityAlert

from ...._version import VERSION
from ....common import (
    MsticnbDataProviderError,
    MsticnbMissingParameterError,
    nb_data_wait,
    nb_print,
    set_text,
)
from ....nb_metadata import read_mod_metadata
from ....nblib.iptools import convert_to_ip_entities
from ....notebooklet import NBMetadata, Notebooklet, NotebookletResult

__version__ = VERSION
__author__ = "Pete Bryan"


_CLS_METADATA: NBMetadata
_CELL_DOCS: Dict[str, Any]
_CLS_METADATA, _CELL_DOCS = read_mod_metadata(__file__, __name__)


# pylint: disable=too-few-public-methods
# Rename this class
class TIEnrichResult(NotebookletResult):
    """
    Template Results.

    Attributes
    ----------
    enriched_results : pd.DataFrame
        Alerts with additional TI enrichment
    picker : SelectAlert
        Alert picker

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
        self.description: str = "Enriched Alerts"
        self.enriched_results: Optional[pd.DataFrame] = None
        self.picker: Optional[SelectAlert] = None


# pylint: enable=too-few-public-methods
# pylint: disable=too-many-branches
class EnrichAlerts(Notebooklet):
    """
    Alert Enrichment Notebooklet Class.

    Enriches Azure Sentinel alerts with TI data.

    """

    metadata = _CLS_METADATA

    @set_text(docs=_CELL_DOCS, key="run")
    def run(
        self,
        value: Optional[str] = None,
        data: Optional[pd.DataFrame] = None,
        timespan: Optional[TimeSpan] = None,
        options: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> TIEnrichResult:
        """
        Return an enriched set of Alerts.

        Parameters
        ----------
        timespan : TimeSpan
            Timespan for queries
        options : Optional[Iterable[str]], optional
            List of options to use, by default None.
            A value of None means use default options.
            Options prefixed with "+" will be added to the default options.
            To see the list of available options type `help(cls)` where
            "cls" is the notebooklet class or an instance of this class.
        value: Optional[str], optional
            If you want to filter Alerts based on a specific entity specify
            it as a string.
        data: Optional[pd.DataFrame], optional
            If you have alerts in a DataFrame you can pass them rather than
            having the notebooklet query alerts.

        Returns
        -------
        TIEnrichResult
            Result object with attributes for each result type.

        Raises
        ------
        MsticnbMissingParameterError
            If required parameters are missing

        MsticnbDataProviderError
            If data is not avaliable

        """
        # This line use logic in the superclass to populate options
        # (including default options) into this class.
        super().run(
            value=value, data=data, timespan=timespan, options=options, **kwargs
        )

        if not timespan and data is None:
            raise MsticnbMissingParameterError("timespan.")

        # If data is not provided, query Sentinel to get it.
        if data is None:
            nb_print("Collecting alerts")
            if value is not None:
                data = _get_all_alerts(self.query_provider, timespan, value)
            else:
                data = _get_all_alerts(self.query_provider, timespan)

        # Create a result class
        # Add description to results for context
        self._last_result = TIEnrichResult(
            description=f"""Enriched alerts with the filter of {value}""",
            notebooklet=self,
            timespan=timespan,
        )

        # Establish TI providers
        if "tilookup" in self.data_providers.providers:
            ti_prov = self.data_providers.providers["tilookup"]
        else:
            raise MsticnbDataProviderError("No TI providers avaliable")

        if not isinstance(data, pd.DataFrame) or data.empty:
            raise MsticnbDataProviderError("No alerts avaliable")

        data["Entities"] = data["Entities"].apply(_entity_load)
        tqdm.pandas(desc="TI lookup progress")
        ti_sec = False
        if "secondary" in self.options:
            ti_sec = True
        md(
            """Alerts enriched with threat intelligence -
                 TI Risk is the the hightest score provided by any of
                 the configured providers."""
        )
        data["TI Risk"] = data.progress_apply(
            lambda row: _lookup(row, ti_prov, secondary=ti_sec), axis=1
        )
        if not self.silent:
            display(
                data[
                    ["StartTimeUtc", "AlertName", "Severity", "TI Risk", "Description"]
                ]
                .sort_values(by=["StartTimeUtc"])
                .style.map(_color_cells)
                .hide_index()
            )
        if "details" in self.options:
            geo_lookup = self.get_provider("geolitelookup") or self.get_provider(
                "ipstacklookup"
            )
            self._last_result.picker = _alert_picker(
                data,
                ti_prov,
                secondary=ti_sec,
                silent=self.silent,
                geo_lookup=geo_lookup,
            )
        self._last_result.enriched_results = data

        return self._last_result


# %%
# Display Alert Picker
@set_text(docs=_CELL_DOCS, key="select_alert")
def _alert_picker(data, ti_prov, secondary, silent: bool, geo_lookup: Any = None):
    ti_provs = "primary"
    if secondary is True:
        ti_provs = "all"

    def show_full_alert(selected_alert):
        global security_alert  # pylint: disable=global-variable-undefined, invalid-name
        output = []
        security_alert = SecurityAlert(selected_alert)
        output.append(format_alert(security_alert, show_entities=True))
        ioc_list = []
        if security_alert["Entities"] is not None:
            for entity in security_alert["Entities"]:
                if entity["Type"] in ("ipaddress", "ip"):
                    ioc_list.append(entity["Address"])
                elif entity["Type"] == "url":
                    ioc_list.append(entity["Url"])
            if ioc_list:
                ti_data = ti_prov.lookup_iocs(data=ioc_list, prov_scope=ti_provs)
                output.append(
                    ti_data[
                        ["Ioc", "IocType", "Provider", "Result", "Severity", "Details"]
                    ]
                    .reset_index()
                    .style.map(_color_cells)
                    .hide_index()
                )
                ti_ips = ti_data[ti_data["IocType"] == "ipv4"]
                # If we have IP entities try and plot these on a map
                if not ti_ips.empty:
                    ip_ents = [
                        convert_to_ip_entities(i, geo_lookup=geo_lookup)
                        for i in ti_ips["Ioc"].unique()
                    ]
                    ip_ents = [
                        ip_ent for ip_ent_list in ip_ents for ip_ent in ip_ent_list
                    ]
                    center = get_center_ip_entities(ip_ents)
                    ip_map = FoliumMap(location=center, zoom_start=4)
                    ip_map.add_ip_cluster(ip_ents, color="red")
                    output.append(ip_map)
                else:
                    output.append("")
            else:
                output.append("No IoCs")
        else:
            output.append("No Entities with IoCs")
        return output

    alert_select = SelectAlert(
        alerts=data,
        action=show_full_alert,
        columns=[
            "StartTimeUtc",
            "AlertName",
            "CompromisedEntity",
            "TI Risk",
            "SystemAlertId",
        ],
    )
    if silent is not True:
        alert_select.display()

    return alert_select


# pylint: disable=too-many-branches


# %%
# Get Alerts
def _get_all_alerts(qry_prov, timespan, filter_item=None):
    nb_data_wait("Alerts")
    if filter_item is not None:
        return qry_prov.SecurityAlert.list_alerts(
            start=timespan.start,
            end=timespan.end,
            add_query_items=f'| where Entities contains "{filter_item}"',
        )
    return qry_prov.SecurityAlert.list_alerts(start=timespan.start, end=timespan.end)


# Extract packed entity details
def _entity_load(entity):
    try:
        return json.loads(entity)
    except json.JSONDecodeError:
        return None


# Lookup details against TI
def _lookup(row, ti_prov, secondary: bool = False):
    sev = []
    prov_scope = "primary"
    if secondary:
        prov_scope = "all"
    if row["Entities"] is not None:
        for entity in row["Entities"]:
            try:
                if entity["Type"] in ("ipaddress", "ip"):
                    resp = ti_prov.lookup_ioc(entity["Address"], prov_scope=prov_scope)
                elif entity["Type"] == "url":
                    resp = ti_prov.lookup_ioc(entity["Url"], prov_scope=prov_scope)
                else:
                    resp = None
                if resp:
                    for response in resp[1]:
                        sev.append(response[1].severity)
            except KeyError:
                pass

    return _sev_score(sev)


# Color code cells based on TI results
def _color_cells(val):
    color_chart = {"high": "Red", "warning": "Orange", "information": "Green"}
    if isinstance(val, str) and val.casefold() in color_chart:
        color = color_chart[val.casefold()]
    else:
        color = "none"
    return f"background-color: {color}"


def _sev_score(sev):
    if "high" in sev:
        return "High"
    if "warning" in sev:
        return "Warning"
    if "information" in sev:
        return "Information"
    return "None"
