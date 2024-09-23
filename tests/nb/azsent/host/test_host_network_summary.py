# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test the host_network_summary class."""
import json
import re
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import pytest_check as check
import respx
from msticpy.common.timespan import TimeSpan

from msticnb import data_providers, discover_modules, nblts

from ....unit_test_lib import (
    TEST_DATA_PATH,
    GeoIPLiteMock,
    TILookupMock,
    get_test_data_path,
)

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
def test_url_summary_notebooklet(
    mock_whois, init_notebooklets, rdap_response, whois_response
):
    """Test basic run of notebooklet."""
    mock_whois.return_value = whois_response["asn_response_1"]
    respx.get(re.compile(r"http://rdap\.arin\.net/.*")).respond(200, json=rdap_response)
    check.is_true(hasattr(nblts.azsent.host, "HostNetworkSummary"))
    if not hasattr(nblts.azsent.host, "HostNetworkSummary"):
        print(nblts.azsent.host)

    test_nb = nblts.azsent.host.HostNetworkSummary()

    with pytest.raises(ValueError):
        result = test_nb.run(value="myhost", timespan=TimeSpan(period="1D"))
    result = test_nb.run(
        value=("myhost", "127.45.34.1"), timespan=TimeSpan(period="1D")
    )
    check.is_not_none(result)
    check.is_instance(result.flows, pd.DataFrame)
    check.is_true(result.flows.shape[0] > 0)
    check.is_instance(result.flow_whois, pd.DataFrame)
    check.is_not_none(result.flow_matrix)
    check.is_not_none(result.flow_map)
    check.is_instance(result.flow_ti, pd.DataFrame)
    check.is_true(result.flow_ti.shape[0] > 0)
