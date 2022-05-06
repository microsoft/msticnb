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

# from contextlib import redirect_stdout
import pytest_check as check
from msticpy.common.timespan import TimeSpan

from msticnb import data_providers, nblts

from ....unit_test_lib import TEST_DATA_PATH, GeoIPLiteMock

# pylint: disable=no-member

if not sys.platform.startswith("win"):
    pytest.skip(
        "skipping Linux and Mac for these tests since Matplotlib fails with no gui",
        allow_module_level=True,
    )


def test_winhostevents_notebooklet(monkeypatch):
    """Test basic run of notebooklet."""
    test_data = str(Path(TEST_DATA_PATH).absolute())
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    data_providers.init(
        query_provider="LocalData",
        LocalData_data_paths=[test_data],
        LocalData_query_paths=[test_data],
    )

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
