# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test the nb_template class."""
# from contextlib import redirect_stdout
from pathlib import Path

import pandas as pd
import pytest_check as check
from msticnb import nblts
from msticnb import data_providers
from msticpy.common.timespan import TimeSpan

from ....unit_test_lib import TEST_DATA_PATH, GeoIPLiteMock

# pylint: disable=no-member


def test_host_summary_notebooklet(monkeypatch):
    """Test basic run of notebooklet."""
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    test_data = str(Path(TEST_DATA_PATH).absolute())
    data_providers.init(
        query_provider="LocalData",
        LocalData_data_paths=[test_data],
        LocalData_query_paths=[test_data],
    )

    test_nb = nblts.azsent.host.HostSummary()
    tspan = TimeSpan(period="1D")

    result = test_nb.run(value="myhost", timespan=tspan)
    check.is_not_none(result.host_entity)
    check.is_not_none(result.related_alerts)
    check.is_instance(result.related_alerts, pd.DataFrame)
    check.is_not_none(result.alert_timeline)
    check.is_not_none(result.related_bookmarks)
    check.is_instance(result.related_bookmarks, pd.DataFrame)
