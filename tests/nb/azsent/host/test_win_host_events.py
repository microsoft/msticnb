# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test the nb_template class."""
import sys
from pathlib import Path

import pandas as pd
import pytest
import pytest_check as check
from msticpy.common.timespan import TimeSpan

from msticnb import data_providers, discover_modules, nblts

from ....unit_test_lib import TEST_DATA_PATH, GeoIPLiteMock, TILookupMock

# pylint: disable=protected-access, no-member, redefined-outer-name, unused-argument

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
    monkeypatch.setattr(data_providers, "TILookup", TILookupMock)
    data_providers.init(
        query_provider="LocalData",
        LocalData_data_paths=[test_data],
        LocalData_query_paths=[test_data],
        providers=["tilookup", "geolitelookup"],
    )


def test_winhostevents_notebooklet(init_notebooklets):
    """Test basic run of notebooklet."""
    test_nb = nblts.azsent.host.WinHostEvents()
    tspan = TimeSpan(period="1D")

    result = test_nb.run(value="myhost", timespan=tspan)
    check.is_not_none(result.all_events)
    check.is_instance(result.all_events, pd.DataFrame)
    check.is_not_none(result.event_pivot)
    check.is_instance(result.event_pivot, pd.DataFrame)
    check.is_not_none(result.account_events)
    check.is_instance(result.account_events, pd.DataFrame)
    check.is_not_none(result.event_pivot)
    check.is_instance(result.event_pivot, pd.DataFrame)
    # check.is_not_none(result.account_timeline)

    exp_events = test_nb.expand_events([5058, 5061])
    check.is_instance(exp_events, pd.DataFrame)

    exp_events = test_nb.expand_events(5061)
    check.is_instance(exp_events, pd.DataFrame)

    exp_events = test_nb.expand_events(99999)
    check.is_none(exp_events)
