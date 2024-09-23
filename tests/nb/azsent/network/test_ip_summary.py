# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test the nb_template class."""
import json
import re
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import pytest_check as check
import respx
from bokeh.models import LayoutDOM
from msticpy.common.timespan import TimeSpan

from msticnb import data_providers, discover_modules, nblts

from ....unit_test_lib import (
    DEF_PROV_TABLES,
    TEST_DATA_PATH,
    GeoIPLiteMock,
    TILookupMock,
    get_test_data_path,
)


def create_mocked_exec_query(func):
    """Create decorator for mocked exec_query."""

    def exec_query_mock(query, *args, **kwargs):
        """Mock exec query for driver."""
        if (
            "SecurityEvent" in query
            and "| summarize Count=count(), FirstOperation=min(TimeGenerated)" in query
        ):
            win_host_df = pd.read_pickle(
                str(Path(TEST_DATA_PATH).joinpath("all_events_df.pkl"))
            ).head(10)
            return (
                win_host_df[["Computer", "Account", "TimeGenerated"]]
                .groupby(["Computer", "Account"])
                .agg(
                    Count=pd.NamedAgg("Computer", "count"),
                    FirstOperation=pd.NamedAgg("TimeGenerated", "min"),
                    LastOperation=pd.NamedAgg("TimeGenerated", "max"),
                )
                .reset_index()
            )
        if query.strip().startswith("DeviceInfo"):
            return pd.read_pickle(
                str(Path(TEST_DATA_PATH).joinpath("mde_device_info.pkl"))
            )
        if query.strip().startswith("DeviceNetworkInfo"):
            return pd.read_pickle(
                str(Path(TEST_DATA_PATH).joinpath("mde_device_network_info.pkl"))
            )
        if query.strip().startswith("DeviceNetworkEvents"):
            return pd.read_pickle(
                str(Path(TEST_DATA_PATH).joinpath("mde_device_network_events.pkl"))
            )
        # if no special handling, pass to original function
        return func(query, *args, **kwargs)

    return exec_query_mock


def create_check_table(valid_tables):
    """Create mock for check_table_exists."""

    def check_table_exists(table):
        """Mock check table exists."""
        return table in valid_tables

    return check_table_exists


# pylint: disable=protected-access, no-member, redefined-outer-name, unused-argument


@pytest.fixture
def init_notebooklets(monkeypatch):
    """Initialize notebooklets."""
    test_data = str(Path(TEST_DATA_PATH).absolute())

    discover_modules()
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    monkeypatch.setattr(data_providers, "TILookup", TILookupMock)
    data_providers.init(
        query_provider="LocalData",
        LocalData_data_paths=[test_data],
        LocalData_query_paths=[test_data],
        providers=["tilookup", "geolitelookup"],
    )


@pytest.fixture(scope="session")
def whois_response():
    """Return mock responses for Whois."""
    json_text = (
        get_test_data_path().joinpath("whois_response.json").read_text(encoding="utf-8")
    )
    return json.loads(json_text)


@pytest.fixture(scope="session")
def rdap_response():
    """Return mock responses for Whois."""
    json_text = (
        get_test_data_path().joinpath("rdap_response.json").read_text(encoding="utf-8")
    )
    return json.loads(json_text)


@respx.mock
@patch("msticpy.context.ip_utils._asn_whois_query")
def test_ip_summary_notebooklet(
    mock_whois, init_notebooklets, monkeypatch, rdap_response, whois_response
):
    """Test basic run of notebooklet."""
    test_nb = nblts.azsent.network.IpAddressSummary()
    # test_nb.query_provider.schema.update(
    #     {tab: {} for tab in DEF_PROV_TABLES + valid_tables}
    # )
    eq_mock = create_mocked_exec_query(test_nb.query_provider.exec_query)
    monkeypatch.setattr(test_nb.query_provider, "exec_query", eq_mock)
    mock_whois.return_value = whois_response["asn_response_1"]
    respx.get(re.compile(r"http://rdap\.arin\.net/.*")).respond(200, json=rdap_response)
    respx.get(
        re.compile(r"https://otx\.alienvault.*|https://www\.virustotal.*")
    ).respond(200, json=OTX_RESP)
    respx.get(re.compile(r"https://check\.torproject\.org.*")).respond(404)
    respx.get(re.compile(r"https://api\.greynoise\.io.*")).respond(404)
    respx.get(re.compile(r".*SecOps-Institute/Tor-IP-Addresses.*")).respond(
        200, content=b"12.34.56.78\n12.34.56.78\n12.34.56.78"
    )
    respx.get(re.compile(r"https://api\.greynoise\.io/.*")).respond(404)
    tspan = TimeSpan(period="1D")

    assert test_nb.get_provider("tilookup") is not None
    assert isinstance(test_nb.get_provider("tilookup"), TILookupMock)

    result = test_nb.run(value="11.1.2.3", timespan=tspan)
    check.is_not_none(result.ip_entity)
    check.equal(result.ip_type, "Public")
    # we've set exclude heartbeat, etc. from available tables
    # so should conclude that it's an external IP address.
    check.equal(result.ip_origin, "External")
    check.is_in("CountryCode", result.geoip)
    check.is_not_none(result.location)
    check.is_not_none(result.notebooklet)
    check.is_not_none(result.whois)
    check.is_instance(result.related_alerts, pd.DataFrame)
    check.is_not_none(test_nb.browse_alerts())
    # check.is_instance(result.passive_dns, pd.DataFrame)
    check.is_instance(result.ti_results, pd.DataFrame)


@respx.mock
@patch("msticpy.context.ip_utils._asn_whois_query")
def test_ip_summary_notebooklet_internal(
    mock_whois, init_notebooklets, monkeypatch, rdap_response, whois_response
):
    """Test basic run of notebooklet."""
    # test_data = str(Path(TEST_DATA_PATH).absolute())
    # monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    # monkeypatch.setattr(data_providers, "TILookup", TILookupMock)
    # data_providers.init(
    #     query_provider="LocalData",
    #     LocalData_data_paths=[test_data],
    #     LocalData_query_paths=[test_data],
    #     providers=["tilookup", "geolitelookup"],
    # )

    test_nb = nblts.azsent.network.IpAddressSummary()
    eq_mock = create_mocked_exec_query(test_nb.query_provider.exec_query)
    monkeypatch.setattr(test_nb.query_provider, "exec_query", eq_mock)
    mock_whois.return_value = whois_response["asn_response_1"]
    respx.get(re.compile(r"http://rdap\.arin\.net/.*")).respond(200, json=rdap_response)
    respx.get(re.compile(r"https://check\.torproject\.org.*")).respond(404)
    respx.get(re.compile(r".*SecOps-Institute/Tor-IP-Addresses.*")).respond(
        200, content=b"12.34.56.78\n12.34.56.78\n12.34.56.78"
    )

    tspan = TimeSpan(period="1D")

    valid_tables = [
        "SigninLogs",
        "AzureActivity",
        "OfficeActivity",
        "Heartbeat",
        "AzureNetworkAnalytics_CL",
    ]
    test_nb.query_provider.schema.update(
        {tab: {} for tab in DEF_PROV_TABLES + valid_tables}
    )
    result = test_nb.run(value="40.76.43.124", timespan=tspan)
    check.is_not_none(result.ip_entity)
    check.equal(result.ip_type, "Public")
    check.equal(result.ip_origin, "Internal")
    check.is_not_none(result.whois)
    check.is_instance(result.related_alerts, pd.DataFrame)
    check.is_instance(result.heartbeat, pd.DataFrame)
    check.is_instance(result.az_network_if, pd.DataFrame)
    check.is_none(result.ti_results)


@respx.mock
@patch("msticpy.context.ip_utils._asn_whois_query")
def test_ip_summary_notebooklet_all(
    mock_whois, init_notebooklets, monkeypatch, rdap_response, whois_response
):
    """Test basic run of notebooklet."""
    # test_data = str(Path(TEST_DATA_PATH).absolute())
    # monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    # monkeypatch.setattr(data_providers, "TILookup", TILookupMock)
    # data_providers.init(
    #     query_provider="LocalData",
    #     LocalData_data_paths=[test_data],
    #     LocalData_query_paths=[test_data],
    #     providers=["tilookup", "geolitelookup"],
    # )

    opts = ["+az_netflow", "+passive_dns", "+az_activity", "+office_365", "+ti"]
    test_nb = nblts.azsent.network.IpAddressSummary()
    tspan = TimeSpan(period="1D")
    test_nb.query_provider.schema.update({tab: {} for tab in DEF_PROV_TABLES})
    eq_mock = create_mocked_exec_query(test_nb.query_provider.exec_query)
    monkeypatch.setattr(test_nb.query_provider, "exec_query", eq_mock)
    mock_whois.return_value = whois_response["asn_response_1"]
    respx.get(re.compile(r"http://rdap\.arin\.net/.*")).respond(200, json=rdap_response)
    respx.get(
        re.compile(r"https://otx\.alienvault.*|https://www\.virustotal.*")
    ).respond(200, json=OTX_RESP)
    respx.get(re.compile(r"https://check\.torproject\.org.*")).respond(404)
    respx.get(re.compile(r"https://api\.greynoise\.io.*")).respond(404)
    respx.get(re.compile(r".*SecOps-Institute/Tor-IP-Addresses.*")).respond(
        200, content=b"12.34.56.78\n12.34.56.78\n12.34.56.78"
    )
    respx.get(re.compile(r"https://api\.greynoise\.io/.*")).respond(404)
    tspan = TimeSpan(period="1D")

    result = test_nb.run(value="40.76.43.124", timespan=tspan, options=opts)
    check.is_not_none(result.ip_entity)
    check.greater_equal(len(result.host_entities), 1)
    check.equal(result.host_entities[0].HostName, "MSTICAlertsWin1")
    check.equal(result.host_entities[0].OSFamily.name, "Linux")
    check.equal(result.ip_type, "Public")
    check.equal(result.ip_origin, "Internal")
    check.is_instance(result.heartbeat, pd.DataFrame)
    check.is_instance(result.az_network_if, pd.DataFrame)
    check.is_instance(result.az_network_flows, pd.DataFrame)
    check.is_instance(result.az_network_flow_summary, pd.DataFrame)
    check.is_instance(result.az_network_flows_timeline, LayoutDOM)
    check.is_instance(result.aad_signins, pd.DataFrame)
    check.is_instance(result.office_activity, pd.DataFrame)
    check.is_instance(result.vmcomputer, pd.DataFrame)

    check.is_instance(test_nb.netflow_total_by_protocol(), LayoutDOM)
    check.is_instance(test_nb.netflow_by_direction(), LayoutDOM)

    check.is_not_none(result.whois)
    check.is_instance(result.related_alerts, pd.DataFrame)
    check.is_instance(result.ti_results, pd.DataFrame)


@respx.mock
@patch("msticpy.context.ip_utils._asn_whois_query")
def test_ip_summary_mde_data(
    mock_whois, init_notebooklets, monkeypatch, rdap_response, whois_response
):
    """Test MDE data sets in run of notebooklet."""
    # test_data = str(Path(TEST_DATA_PATH).absolute())
    # monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    # monkeypatch.setattr(data_providers, "TILookup", TILookupMock)
    # data_providers.init(
    #     query_provider="LocalData",
    #     LocalData_data_paths=[test_data],
    #     LocalData_query_paths=[test_data],
    #     providers=["tilookup", "geolitelookup"],
    # )

    opts = ["+az_netflow", "+passive_dns", "+az_activity", "+office_365", "+ti"]
    test_nb = nblts.azsent.network.IpAddressSummary()
    tspan = TimeSpan(period="1D")
    valid_tables = [
        "DeviceInfo",
        "DeviceNetworkInfo",
        "DeviceNetworkEvents",
    ]
    test_nb.query_provider.schema.update(
        {tab: {} for tab in DEF_PROV_TABLES + valid_tables}
    )
    eq_mock = create_mocked_exec_query(test_nb.query_provider.exec_query)
    monkeypatch.setattr(test_nb.query_provider, "exec_query", eq_mock)
    mock_whois.return_value = whois_response["asn_response_1"]
    respx.get(re.compile(r"http://rdap\.arin\.net/.*")).respond(200, json=rdap_response)
    respx.get(
        re.compile(r"https://otx\.alienvault.*|https://www\.virustotal.*")
    ).respond(200, json=OTX_RESP)
    respx.get(re.compile(r"https://check\.torproject\.org.*")).respond(404)
    respx.get(re.compile(r"https://api\.greynoise\.io.*")).respond(404)
    respx.get(re.compile(r".*SecOps-Institute/Tor-IP-Addresses.*")).respond(
        200, content=b"12.34.56.78\n12.34.56.78\n12.34.56.78"
    )
    respx.get(re.compile(r"https://api\.greynoise\.io/.*")).respond(404)
    tspan = TimeSpan(period="1D")

    result = test_nb.run(value="40.76.43.124", timespan=tspan, options=opts)
    check.is_not_none(result.ip_entity)
    check.greater_equal(len(result.host_entities), 1)
    check.equal(result.host_entities[0].HostName, "aadcon")
    check.equal(result.host_entities[0].OSFamily.name, "Windows")
    check.equal(result.ip_type, "Public")
    check.equal(result.ip_origin, "Internal")
    check.is_none(result.heartbeat)
    check.is_none(result.az_network_if)
    check.is_instance(result.host_logons, pd.DataFrame)
    check.is_instance(result.related_accounts, pd.DataFrame)
    check.is_instance(result.az_network_flows, pd.DataFrame)
    check.is_instance(result.az_network_flow_summary, pd.DataFrame)
    check.is_instance(result.az_network_flows_timeline, LayoutDOM)
    check.is_instance(result.associated_hosts, pd.DataFrame)
    check.is_instance(result.device_info, pd.DataFrame)
    check.is_instance(result.network_connections, pd.DataFrame)

    check.is_instance(test_nb.netflow_total_by_protocol(), LayoutDOM)
    check.is_instance(test_nb.netflow_by_direction(), LayoutDOM)

    check.is_not_none(result.whois)
    check.is_instance(result.related_alerts, pd.DataFrame)
    check.is_instance(result.ti_results, pd.DataFrame)


OTX_RESP = {
    "ioc_param": "url",
    "response": {
        "response": "Found stuff",
        "pulse_info": {
            "pulses": [
                {
                    "name": ["somename"],
                    "tags": ["bad", "good", "ugly"],
                    "references": ["url1", "url2"],
                }
            ]
        },
    },
}
