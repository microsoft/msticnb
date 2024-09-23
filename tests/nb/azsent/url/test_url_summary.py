# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test the url_summary class."""
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

    check.is_true(hasattr(nblts.azsent.url, "URLSummary"))
    if not hasattr(nblts.azsent.url, "URLSummary"):
        print(nblts.azsent.url)

    test_nb = nblts.azsent.url.URLSummary()

    result = test_nb.run(
        value="http://www.microsoft.com", timespan=TimeSpan(period="1D")
    )
    check.is_not_none(result)
    check.is_instance(result.ip_record, pd.DataFrame)
    check.is_instance(result.related_alerts, pd.DataFrame)
    check.is_instance(result.summary, pd.DataFrame)
    check.is_instance(result.domain_record, pd.DataFrame)
    result._display_summary()
    result._display_ti_data()
    result._display_domain_record()
    result._display_ip_record()
    result._display_cert_details()
    result._display_related_alerts()
    result._display_bookmarks()
    result._display_dns_results()
    result._display_hosts()
    result.browse_alerts()
    result.display_alert_timeline()
    result._display_flows()
