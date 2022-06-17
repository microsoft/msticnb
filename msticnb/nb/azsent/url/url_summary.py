# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklet for URL Summary."""
from typing import Any, Dict, Iterable, Optional, List
from collections import Counter

import pandas as pd
from IPython.display import display, Image
import tldextract
from whois import whois
import numpy as np
import dns.resolver

try:
    from msticpy.context.domain_utils import DomainValidator, screenshot
    from msticpy import nbwidgets
    from msticpy.vis.timeline import display_timeline, display_timeline_values
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.sectools.domain_utils import DomainValidator, screenshot
    from msticpy.nbtools import nbwidgets
    from msticpy.nbtools.nbdisplay import display_timeline, display_timeline_values


from msticpy.common.timespan import TimeSpan
from msticpy.common.utility import md

from bokeh.models import LayoutDOM

from ...._version import VERSION
from ....common import (
    MsticnbDataProviderError,
    MsticnbMissingParameterError,
    nb_markdown,
    nb_data_wait,
    set_text,
)
from ....nb_metadata import read_mod_metadata, update_class_doc
from ....notebooklet import NBMetadata, Notebooklet, NotebookletResult
from ....nblib.ti import get_ti_results
from ....nblib.azsent.alert import browse_alerts

__version__ = VERSION
__author__ = "Pete Bryan"


_CLS_METADATA: NBMetadata
_CELL_DOCS: Dict[str, Any]
_CLS_METADATA, _CELL_DOCS = read_mod_metadata(__file__, __name__)


# pylint: disable=too-few-public-methods
class URLSummaryResult(NotebookletResult):
    """
    URL Summary Results.

    """

    def __init__(
        self,
        description: Optional[str] = None,
        timespan: Optional[TimeSpan] = None,
        notebooklet: Optional["Notebooklet"] = None,
    ):
        """
        Create new Notebooklet result instance.

        """
        super().__init__(description, timespan, notebooklet)
        self.summary: pd.DataFrame = None
        self.domain_record: pd.DataFrame = None
        self.cert_details: pd.DataFrame = None
        self.ip_record: pd.DataFrame = None
        self.related_alerts: pd.DataFrame = None
        self.bookmarks: pd.DataFrame = None
        self.dns_results: pd.DataFrame = None
        self.hosts: List = None
        self.flows: pd.DataFrame = None
        self.flow_graph: LayoutDOM = None


# pylint: disable=too-few-public-methods
class URLSummary(Notebooklet):
    """
    URLSummary Notebooklet class.

    Queries and displays information about a URL including:

    - Overview of URL and Domain
    - Related alerts
    - TI results

    """

    metadata = _CLS_METADATA
    __doc__ = update_class_doc(__doc__, metadata)
    _cell_docs = _CELL_DOCS

    # pylint: disable=too-many-branches
    @set_text(docs=_CELL_DOCS, key="run")  # noqa: MC0001
    def run(  # noqa:MC0001
        self,
        value: Any = None,
        data: Optional[pd.DataFrame] = None,
        timespan: Optional[TimeSpan] = None,
        options: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> URLSummaryResult:
        """
        Return host summary data.

        Parameters
        ----------
        value : str
            URL to investigate
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
        URLSummaryResult
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
        result = URLSummaryResult(
            notebooklet=self, description=self.metadata.description, timespan=timespan
        )

        url = value.strip().lower()
        _, domain, tld = tldextract.extract(url)
        domain = f"{domain.lower()}.{tld.lower()}"
        domain_validator = DomainValidator()
        validated = domain_validator.validate_tld(domain)

        result.summary = pd.DataFrame(
            {"URL": [url], "Domain": [domain], "Validated TLD": [validated]}
        )
        if not self.silent:
            nb_markdown(f"Summary of {url}:")
            display(result.summary)

        if "ti" in self.options:
            if "tilookup" in self.data_providers.providers:
                ti_prov = self.data_providers.providers["tilookup"]
            else:
                raise MsticnbDataProviderError("No TI providers avaliable")
            nb_data_wait("Threat Intelligence Results")
            ti_results, ti_results_merged = get_ti_results(
                ti_prov, result.summary, "URL"
            )
            if isinstance(ti_results, pd.DataFrame) and not ti_results.empty:
                result.summary = ti_results_merged
            if not self.silent:
                nb_markdown(f"Threat Intelligence Results for {url}.")
                display(ti_results_merged)

        if "whois" in self.options:
            result.domain_record = _domain_whois_record(
                domain, self.data_providers.providers["tilookup"]
            )
            if not self.silent:
                nb_markdown(f"WhoIs Results for {url}.")
                display(
                    result.domain_record.T.style.applymap(
                        color_domain_record_cells,
                        subset=pd.IndexSlice[["Page Rank", "Domain Name Entropy"], 0],
                    )
                )

        if "cert" in self.options:
            result.cert_details = _get_tls_cert_details(url, domain_validator)
            if not self.silent and not result.cert_details.empty:
                nb_markdown(f"TLS Certificate Details for {url}.")
                display(result.cert_details)

        if "ip_record" in self.options:
            result.ip_record = _get_ip_record(
                domain, domain_validator, self.data_providers.providers["tilookup"]
            )
            if not self.silent:
                nb_markdown(f"IP Address Details for {url}.")
                display(result.ip_record.T)

        if "screenshot" in self.options:
            image_data = screenshot(url)
            with open("screenshot.png", "wb") as f:
                f.write(image_data.content)
            if not self.silent:
                nb_markdown(f"Screenshot of {url}")
                display(Image(filename="screenshot.png"))

        if "alerts" in self.options:
            alerts = self.query_provider.SecurityAlert.list_alerts(timespan)
            result.related_alerts = alerts[alerts["Entities"].str.contains(url)]
            if not self.silent and not result.related_alerts.empty:
                nb_markdown(f"Alerts related to {url}")
                display(result.related_alerts)

        if "bookmarks" in self.options:
            result.bookmarks = (
                self.query_provider.AzureSentinel.list_bookmarks_for_entity(
                    url=url, start=timespan.start, end=timespan.end
                )
            )
            if not self.silent and not result.bookmarks.empty:
                nb_markdown(f"Bookmarks related to {url}")
                display(result.bookmarks)

        if "dns" in self.options:
            result.dns_results = (
                self.query_provider.AzureNetwork.dns_lookups_for_domain(
                    domain=domain, start=timespan.start, end=timespan.end
                )
            )
            if not self.silent and not result.dns_results.empty:
                nb_markdown(f"DNS events related to {url}")
                display(result.dns_results)

        if "hosts" in self.options:
            syslog_hosts = self.query_provider.LinuxSyslog.all_syslog(
                add_query_items=f"| where SyslogMessage has '{url}'",
                start=timespan.start,
                end=timespan.end,
            )["Computer"].unique()
            mde_hosts = self.query_provider.MDE.host_connections(
                time_column="TimeGenerated",
                host_name="",
                add_query_items=f"| where RemoteUrl has '{url}'",
                start=timespan.start,
                end=timespan.end,
            )["DeviceName"].unique()
            windows_hosts = self.query_provider.WindowsSecurity.list_events(
                add_query_items=f"| where CommandLine has '{url}'",
                start=timespan.start,
                end=timespan.end,
            )["Computer"].unique()
            all_hosts = list(syslog_hosts) + list(mde_hosts) + list(windows_hosts)
            result.hosts = all_hosts
            if not self.silent:
                nb_markdown(f"Hosts connecting to {url}")
                display(result.hosts)

        if "flows" in self.options:
            result.flows = self.query_provider.Network.network_connections_to_url(
                start=timespan.start, end=timespan.end, url="com"
            )
            flow_graph_data = self.query_provider.Network.network_connections_to_url(
                start=timespan.start,
                end=timespan.end,
                url="com",
                add_query_items="| summarize sum(SentBytes) by RequestURL, bin(TimeGenerated, 10m)",
            )
            result.flow_graph = display_timeline_values(
                flow_graph_data,
                value_col="sum_SentBytes",
                title=f"Network traffic volume to {url}",
            )
            if not self.silent:
                display(result.flow_graph)
                nb_markdown(f"Network connections to {url}")
                display(result.flows)

        self._last_result = result
        return self._last_result

    @set_text(docs=_CELL_DOCS, key="browse_alerts")
    def browse_alerts(self) -> nbwidgets.SelectAlert:
        """Return alert browser/viewer."""
        if self.check_valid_result_data("related_alerts"):
            return browse_alerts(self._last_result)
        return None

    def display_alert_timeline(self):
        """Display the alert timeline."""
        if self.check_valid_result_data("related_alerts"):
            if len(self._last_result.related_alerts) > 1:
                return _show_alert_timeline(self._last_result.related_alerts)
            print("Cannot plot timeline with 0 or 1 event.")
        return None


def entropy(data):
    s, lens = Counter(data), np.float(len(data))
    return -sum(count / lens * np.log2(count / lens) for count in s.values())


def color_domain_record_cells(val):
    if isinstance(val, int):
        color = "yellow" if val < 3 else None
    elif isinstance(val, float):
        color = "yellow" if val > 4.30891 or val < 2.72120 else None
    else:
        color = None
    return f"background-color: {color}"


@set_text(docs=_CELL_DOCS, key="display_alert_timeline")
def _show_alert_timeline(related_alerts):
    if len(related_alerts) > 1:
        return display_timeline(
            data=related_alerts,
            title="Related Alerts",
            source_columns=["AlertName", "TimeGenerated"],
            height=200,
        )
    if len(related_alerts) == 1:
        nb_markdown("A single alert cannot be plotted on a timeline.")
    else:
        nb_markdown("No alerts available to be plotted.")
    return None


@set_text(docs=_CELL_DOCS, key="show_domain_record")
def _domain_whois_record(domain, ti_prov):
    dom_record = pd.DataFrame()
    whois_result = whois(domain)
    if whois_result.domain_name is not None:
        # Create domain record from whois data
        dom_record = pd.DataFrame(
            {
                "Domain": [domain],
                "Name": [whois_result.get("name", None)],
                "Org": [whois_result.get("org", None)],
                "DNSSec": [whois_result.get("dnssec", None)],
                "City": [whois_result.get("city", None)],
                "State": [whois_result.get("state", None)],
                "Country": [whois_result.get("country", None)],
                "Registrar": [whois_result.get("registrar", None)],
                "Status": [whois_result.get("status", None)],
                "Created": [whois_result.get("creation_date", None)],
                "Expiration": [whois_result.get("expiration_date", None)],
                "Last Updated": [whois_result.get("updated_date", None)],
                "Name Servers": [whois_result.get("name_servers", None)],
            }
        )
        ns_domains = []

        # Identity domains populatirty with Open Page Rank
        page_rank = ti_prov.result_to_df(
            ti_prov.lookup_ioc(observable=domain, providers=["OPR"])
        )
        if page_rank["RawResult"][0]:
            page_rank_score = page_rank["RawResult"][0]["response"][0][
                "page_rank_integer"
            ]
        else:
            page_rank_score = 0
        dom_record["Page Rank"] = [page_rank_score]

        # Get a list of subdomains for the domain
        url_ti = ti_prov.result_to_df(
            ti_prov.lookup_ioc(observable=domain, providers=["VirusTotal"])
        )
        try:
            sub_doms = url_ti["RawResult"][0]["subdomains"]
        except TypeError:
            sub_doms = "None found"
        dom_record["Sub Domains"] = [sub_doms]

        # Work out domain entropy to identity possible DGA
        dom_ent = entropy(domain)
        dom_record["Domain Name Entropy"] = [dom_ent]

        # Remove duplicate Name Server records
        for server in whois_result["name_servers"]:
            _, ns_domain, ns_tld = tldextract.extract(server)
            ns_dom = ns_domain.lower() + "." + ns_tld.lower()
            if domain not in ns_domains:
                ns_domains.append(ns_dom)
    return dom_record


@set_text(docs=_CELL_DOCS, key="show_TLS_cert")
def _get_tls_cert_details(url, domain_validator):
    result, x509 = domain_validator.in_abuse_list(url)
    cert_df = pd.DataFrame()
    if x509 is not None:
        cert_df = pd.DataFrame(
            {
                "SN": [x509.serial_number],
                "Subject": [[(i.value) for i in x509.subject]],
                "Issuer": [[(i.value) for i in x509.issuer]],
                "Expired": [x509.not_valid_after],
                "InAbuseList": result,
            }
        )
    return cert_df


@set_text(docs=_CELL_DOCS, key="show_IP_record")
def _get_ip_record(domain, domain_validator, ti_prov):
    if domain_validator.is_resolvable(domain) is True:
        try:
            answer = dns.resolver.query(domain, "A")
        except dns.resolver.NXDOMAIN:
            md("Could not resolve IP addresses from domain.")
        resolved_domain_ip = answer[0].to_text()
        ip_whois_result = whois(resolved_domain_ip)
        ip_record = pd.DataFrame(
            {
                "IP Address": [resolved_domain_ip],
                "Domain": [ip_whois_result.get("domain_name", None)],
                "Registrar": [ip_whois_result.get("asn_description", None)],
                "Country": [ip_whois_result.get("country", None)],
                "Creation Date": [ip_whois_result.get("creation_date", None)],
            }
        )
    tor = None
    if "Tor" in ti_prov.loaded_providers:
        tor = ti_prov.result_to_df(
            ti_prov.lookup_ioc(observable=ip_record["IP Address"][0], providers=["Tor"])
        )
    if tor is None or tor["Details"][0] == "Not found.":
        ip_record["Tor Node?"] = "No"
    else:
        ip_record["Tor Node?"] = "Yes"
    if "VirusTotal" in ti_prov.loaded_providers:
        ip_ti_results = ti_prov.result_to_df(
            ti_prov.lookup_ioc(
                observable=ip_record["IP Address"][0], providers=["VirusTotal"]
            )
        )
        try:
            last_10 = ip_ti_results.T["VirusTotal"]["RawResult"]["resolutions"][:10]
            prev_domains = [record["hostname"] for record in last_10]
        except TypeError:
            prev_domains = None
        ip_record["Last 10 resolutions"] = [prev_domains]
    return ip_record
