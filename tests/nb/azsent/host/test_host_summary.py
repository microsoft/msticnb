# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test the nb_template class."""
from pathlib import Path

import pandas as pd
import pytest
import pytest_check as check
from msticpy.common.timespan import TimeSpan

from msticnb import data_providers, discover_modules, nblts

from ....unit_test_lib import TEST_DATA_PATH, GeoIPLiteMock, TILookupMock

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


def test_host_summary_notebooklet(init_notebooklets):
    """Test basic run of notebooklet."""
    test_nb = nblts.azsent.host.HostSummary()
    tspan = TimeSpan(period="1D")

    result = test_nb.run(value="myhost", timespan=tspan)
    check.is_not_none(result.host_entity)
    check.is_not_none(result.related_alerts)
    check.is_instance(result.related_alerts, pd.DataFrame)
    check.is_not_none(result.display_alert_timeline())
    check.is_not_none(result.related_bookmarks)
    check.is_instance(result.related_bookmarks, pd.DataFrame)
