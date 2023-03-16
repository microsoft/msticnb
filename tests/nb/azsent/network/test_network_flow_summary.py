# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test the nb_template class."""
import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import pytest_check as check
import respx
from bokeh.models import LayoutDOM
from msticpy.common.timespan import TimeSpan
from msticpy.vis import foliummap

from msticnb import data_providers, discover_modules, nblts

from ....unit_test_lib import (
    DEF_PROV_TABLES,
    TEST_DATA_PATH,
    GeoIPLiteMock,
    TILookupMock,
    get_test_data_path,
)

# pylint: disable=no-member

if not sys.platform.startswith("win"):
    pytest.skip(
        "skipping Linux and Mac for these tests since Matplotlib fails with no gui",
        allow_module_level=True,
    )


@pytest.fixture
def init_notebooklets(monkeypatch):
    """Initialize notebooklets."""
    test_data = str(Path(TEST_DATA_PATH).absolute())

    discover_modules()
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    monkeypatch.setattr(foliummap, "GeoLiteLookup", GeoIPLiteMock)
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
def test_network_flow_summary_notebooklet(
    mock_whois, init_notebooklets, rdap_response, whois_response
):
    """Test basic run of notebooklet."""
    # discover_modules()
    # test_data = str(Path(TEST_DATA_PATH).absolute())
    mock_whois.return_value = whois_response["asn_response_1"]
    # monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    # monkeypatch.setattr(data_providers, "TILookup", TILookupMock)
    # data_providers.init(
    #     query_provider="LocalData",
    #     LocalData_data_paths=[test_data],
    #     LocalData_query_paths=[test_data],
    # )
    respx.get(re.compile(r"http://rdap\.arin\.net/.*")).respond(200, json=rdap_response)

    test_nb = nblts.azsent.network.NetworkFlowSummary()
    tspan = TimeSpan(period="1D")

    test_nb.query_provider.schema.update({tab: {} for tab in DEF_PROV_TABLES})
    options = ["+geo_map"]
    result = test_nb.run(value="myhost", timespan=tspan, options=options)
    check.is_not_none(result.host_entity)
    check.is_not_none(result.network_flows)
    check.is_instance(result.network_flows, pd.DataFrame)
    check.is_not_none(result.plot_flows_by_protocol)
    check.is_instance(result.plot_flows_by_protocol, LayoutDOM)
    check.is_not_none(result.plot_flows_by_direction)
    check.is_instance(result.plot_flows_by_direction, LayoutDOM)
    check.is_not_none(result.plot_flow_values)
    check.is_instance(result.plot_flow_values, LayoutDOM)
    check.is_not_none(result.flow_index)
    check.is_instance(result.flow_summary, pd.DataFrame)

    result.select_asns()
    result.lookup_ti_for_asn_ips()
    result.show_selected_asn_map()
