# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test the nb_template class."""
from pathlib import Path

# from contextlib import redirect_stdout
import pytest_check as check

from bokeh.models import LayoutDOM
import pandas as pd

from msticpy.common.timespan import TimeSpan
from msticnb import nblts
from msticnb import data_providers

from ....unit_test_lib import (
    TEST_DATA_PATH,
    DEF_PROV_TABLES,
    GeoIPLiteMock,
    TILookupMock,
)


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
    tspan = TimeSpan(period="1D")

    result = test_nb.run(value="11.1.2.3", timespan=tspan)
    check.is_not_none(result.ip_entity)
    check.equal(result.ip_type, "Public")
    check.equal(result.ip_origin, "External")
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
