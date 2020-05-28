# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Alert TI encrichment - provides enrichment of alerts with threat intelligence."""
from typing import Optional, Iterable
import json
import attr
import pandas as pd
from tqdm.notebook import tqdm
from IPython.display import display
from msticpy.nbtools.nbwidgets import AlertSelector
from msticpy.nbtools.nbdisplay import display_alert
from msticpy.nbtools.security_alert import SecurityAlert
from msticpy.sectools.ip_utils import convert_to_ip_entities
from msticpy.nbtools.foliummap import FoliumMap, get_center_ip_entities
from msticpy.common.utility import md

from ....common import (
    TimeSpan,
    MsticnbMissingParameterError,
    MsticnbDataProviderError,
    nb_data_wait,
    nb_print,
    set_text,
)

from ....notebooklet import Notebooklet, NotebookletResult, NBMetaData
from ...._version import VERSION

__version__ = VERSION
__author__ = "Pete Bryan"


# pylint: disable=too-few-public-methods
# Rename this class
@attr.s(auto_attribs=True)
class TIEnrichResult(NotebookletResult):
    """
    Template Results.

    Attributes
    ----------
    enriched_results : pd.DataFrame
        Alerts with additional TI enrichment

    """

    description: str = "Enriched Alerts"
    enriched_results: pd.DataFrame = None
    picker: AlertSelector = None


# pylint: enable=too-few-public-methods
class EnrichAlerts(Notebooklet):
    """
    Alert Enrichment Notebooklet Class.

    Enriches Azure Sentinel alerts with TI data.

    Default Options
    ---------------
    - TI: Uses TI to enrich alert data. Will use your primary TI providers.
    - details - displays a widget allowing you to see more detail about an alert.

    Other Options
    -------------
    - secondary: If set uses secondary TI providers as well as primary for enrichment.


    """

    metadata = NBMetaData(
        # Note __qualname__ is the name of the current class
        name=__qualname__,  # type: ignore  # noqa
        mod_name=__name__,
        description="Enriches Alerts with TI data",
        default_options=["TI", "details"],
        other_options=["secondary"],
        keywords=["alert", "enrich", "TI", "windows"],
        entity_types=["alert"],
        req_providers=["LogAnalytics|LocalData", "tilookup"],
    )

    @set_text(
        title="Enriched Alerts",
        hd_level=1,
        text="Azure Sentinel Alerts enriched with TI data",
    )
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
            description=f"""Enriched alerts,
                            with the filter of {value}"""
        )

        # Establish TI providers
        if "tilookup" in self.data_providers.providers:
            ti_prov = self.data_providers.providers["tilookup"]
        else:
            raise MsticnbDataProviderError("No TI providers avaliable")

        if isinstance(data, pd.DataFrame) and not data.empty:
            data["Entities"] = data["Entities"].apply(_entity_load)
            tqdm.pandas(desc="TI lookup progress")
            ti_sec = False
            if "secondary" in self.options:
                ti_sec = True
            md(
                """Alerts enriched with threat intelligence -
                 TI Risk is the the hightest score provided by any of the configured providers."""
            )
            data["TI Risk"] = data.progress_apply(
                lambda row: _lookup(row, ti_prov, secondary=ti_sec), axis=1
            )
            display(
                data[
                    ["StartTimeUtc", "AlertName", "Severity", "TI Risk", "Description"]
                ]
                .sort_values(by=["StartTimeUtc"])
                .style.applymap(_color_cells)
                .hide_index()
            )
            if "details" in self.options:
                alert_pick = _alert_picker(data, ti_prov, secondary=ti_sec)
        else:
            raise MsticnbDataProviderError("No alerts avaliable")

        self._last_result.enriched_results = data
        self._last_result.picker = alert_pick

        return self._last_result


# %%
# Display Alert Picker
@set_text(
    title="Select Alert",
    text="""
Select and alert to view further details.
""",
)
def _alert_picker(data, ti_prov, secondary):
    ti_provs = "primary"
    if secondary is True:
        ti_provs = "all"

    def show_full_alert(alert):
        global security_alert  # pylint: disable=global-variable-undefined, invalid-name
        security_alert = SecurityAlert(alert)
        display_alert(security_alert, show_entities=True)
        ioc_list = []
        if security_alert["Entities"] is not None:
            for entity in security_alert["Entities"]:
                if entity["Type"] == "ipaddress" or entity["Type"] == "ip":
                    ioc_list.append(entity["Address"])
                elif entity["Type"] == "url":
                    ioc_list.append(entity["Url"])
            if len(ioc_list) > 0:
                # Get TI results for alert
                ti_data = ti_prov.lookup_iocs(data=ioc_list, prov_scope=ti_provs)
                display(
                    ti_data[
                        ["Ioc", "IocType", "Provider", "Result", "Severity", "Details"]
                    ]
                    .reset_index()
                    .style.applymap(_color_cells)
                    .hide_index()
                )
                ti_ips = ti_data[ti_data["IocType"] == "ipv4"]
                # If we have IP entities try and plot these on a map
                if not ti_ips.empty:
                    ip_ents = [
                        convert_to_ip_entities(i)[0] for i in ti_ips["Ioc"].unique()
                    ]
                    center = get_center_ip_entities(ip_ents)
                    ip_map = FoliumMap(location=center, zoom_start=4)
                    ip_map.add_ip_cluster(ip_ents, color="red")
                    display(ip_map)
            else:
                nb_print("No IoCs")
        else:
            nb_print("No IoCs")

    alert_select = AlertSelector(
        alerts=data,
        action=show_full_alert,
        columns=[
            "StartTimeUtc",
            "AlertName",
            "CompromisedEntity",
            "SystemAlertId",
            "TI Risk",
        ],
    )
    alert_select.display()

    return alert_select


# %%
# Get Alerts
def _get_all_alerts(qry_prov, timespan, filter_item=None):
    nb_data_wait("Alerts")
    if filter_item is not None:
        alerts_df = qry_prov.SecurityAlert.list_alerts(
            start=timespan.start,
            end=timespan.end,
            add_query_items=f'| where Entities contains "{filter_item}"',
        )
    else:
        alerts_df = qry_prov.SecurityAlert.list_alerts(
            start=timespan.start, end=timespan.end
        )
    return alerts_df


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
    if secondary is True:
        prov_scope = "all"
    if row["Entities"] is not None:
        for entity in row["Entities"]:
            try:
                if entity["Type"] == "ip" or entity["Type"] == "ipaddress":
                    resp = ti_prov.lookup_ioc(
                        observable=entity["Address"], prov_scope=prov_scope
                    )
                elif entity["Type"] == "url":
                    resp = ti_prov.lookup_ioc(
                        observable=entity["Url"], prov_scope=prov_scope
                    )
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
    return "background-color: %s" % color


def _sev_score(sev):
    if "high" in sev:
        severity = "High"
    elif "warning" in sev:
        severity = "Warning"
    elif "information" in sev:
        severity = "Information"
    else:
        severity = "None"
    return severity
