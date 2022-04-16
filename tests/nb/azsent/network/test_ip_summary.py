# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test the nb_template class."""
from pathlib import Path

import pandas as pd

# from contextlib import redirect_stdout
import pytest_check as check
from bokeh.models import LayoutDOM
from msticpy.common.timespan import TimeSpan

from msticnb import data_providers, nblts

from ....unit_test_lib import (
    DEF_PROV_TABLES,
    TEST_DATA_PATH,
    GeoIPLiteMock,
    TILookupMock,
)


def create_mocked_exec_query(func):
    """Create decorator for mocked exec_query"""

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
        # if no special handling, pass to original function
        return func(query, *args, **kwargs)

    return exec_query_mock


def create_check_table(valid_tables):
    """Create mock for check_table_exists."""

    def check_table_exists(table):
        """Mock check table exists."""
        return table in valid_tables

    return check_table_exists


def patch_nb(test_nb, patch):
    """Monkeypatch notebooklet to emulate queries."""
    patch.setattr(test_nb, "check_table_exists", check_table_exists)
    eq_mock = create_mocked_exec_query(test_nb.query_provider.exec_query)
    patch.setattr(test_nb.query_provider, "exec_query", eq_mock)


# pylint: disable=no-member


def test_ip_summary_notebooklet(monkeypatch):
    """Test basic run of notebooklet."""
    test_data = str(Path(TEST_DATA_PATH).absolute())
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    monkeypatch.setattr(data_providers, "TILookup", TILookupMock)

    data_providers.init(
        query_provider="LocalData",
        LocalData_data_paths=[test_data],
        LocalData_query_paths=[test_data],
        providers=["tilookup", "geolitelookup"],
    )

    test_nb = nblts.azsent.network.IpAddressSummary()
    check_tables = create_check_table(
        valid_tables=["SigninLogs", "AzureActivity", "OfficeActivity"]
    )
    monkeypatch.setattr(test_nb, "check_table_exists", check_tables)
    eq_mock = create_mocked_exec_query(test_nb.query_provider.exec_query)
    monkeypatch.setattr(test_nb.query_provider, "exec_query", eq_mock)

    tspan = TimeSpan(period="1D")

    result = test_nb.run(value="11.1.2.3", timespan=tspan)
    check.is_not_none(result.ip_entity)
    check.equal(result.ip_type, "Public")
    check.equal(result.ip_origin, "Internal")
    check.is_in("CountryCode", result.geoip)
    check.is_not_none(result.location)
    check.is_not_none(result.notebooklet)
    check.is_not_none(result.whois)
    check.is_instance(result.related_alerts, pd.DataFrame)
    check.is_not_none(test_nb.browse_alerts())
    check.is_instance(result.passive_dns, pd.DataFrame)
    check.is_instance(result.ti_results, pd.DataFrame)


def test_ip_summary_notebooklet_internal(monkeypatch):
    """Test basic run of notebooklet."""
    test_data = str(Path(TEST_DATA_PATH).absolute())
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    monkeypatch.setattr(data_providers, "TILookup", TILookupMock)
    data_providers.init(
        query_provider="LocalData",
        LocalData_data_paths=[test_data],
        LocalData_query_paths=[test_data],
        providers=["tilookup", "geolitelookup"],
    )

    test_nb = nblts.azsent.network.IpAddressSummary()

    tspan = TimeSpan(period="1D")

    test_nb.query_provider.schema.update({tab: {} for tab in DEF_PROV_TABLES})
    result = test_nb.run(value="40.76.43.124", timespan=tspan)
    check.is_not_none(result.ip_entity)
    check.equal(result.ip_type, "Public")
    check.equal(result.ip_origin, "Internal")
    check.is_not_none(result.whois)
    check.is_instance(result.related_alerts, pd.DataFrame)
    check.is_instance(result.heartbeat, pd.DataFrame)
    check.is_instance(result.az_network_if, pd.DataFrame)
    check.is_none(result.passive_dns)
    check.is_none(result.ti_results)


def test_ip_summary_notebooklet_all(monkeypatch):
    """Test basic run of notebooklet."""
    test_data = str(Path(TEST_DATA_PATH).absolute())
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    monkeypatch.setattr(data_providers, "TILookup", TILookupMock)
    data_providers.init(
        query_provider="LocalData",
        LocalData_data_paths=[test_data],
        LocalData_query_paths=[test_data],
        providers=["tilookup", "geolitelookup"],
    )

    opts = ["+az_netflow", "+passive_dns", "+az_activity", "+office_365", "+ti"]
    test_nb = nblts.azsent.network.IpAddressSummary()
    tspan = TimeSpan(period="1D")
    test_nb.query_provider.schema.update({tab: {} for tab in DEF_PROV_TABLES})

    result = test_nb.run(value="40.76.43.124", timespan=tspan, options=opts)
    check.is_not_none(result.ip_entity)
    check.is_not_none(result.host_entity)
    check.equal(result.host_entity.HostName, "MSTICAlertsWin1")
    check.equal(result.host_entity.OSFamily.name, "Linux")
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
    check.is_instance(result.passive_dns, pd.DataFrame)
    check.is_instance(result.ti_results, pd.DataFrame)
