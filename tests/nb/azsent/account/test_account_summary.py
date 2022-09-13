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
from bokeh.models import LayoutDOM
from msticpy.common.timespan import TimeSpan
from msticpy.datamodel import entities

try:
    from msticpy import nbwidgets

    if not hasattr(nbwidgets, "SelectItem"):
        raise ImportError("Invalid nbwidgets")
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.nbtools import nbwidgets

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


def test_account_summary_notebooklet(init_notebooklets):
    """Test basic run of notebooklet."""
    test_nb = nblts.azsent.account.AccountSummary()
    tspan = TimeSpan(period="1D")

    result = test_nb.run(value="accountname", timespan=tspan)
    check.is_not_none(result.account_selector)
    acct_select = test_nb.browse_accounts()
    check.is_instance(acct_select, nbwidgets.SelectItem)

    select_opts = result.account_selector.options
    disp_account = result.account_selector.item_action
    for item_value in select_opts.values():
        # Programatically select the item list control
        result.account_selector._wgt_select.value = item_value
        disp_account(item_value)
        check.is_instance(result.account_activity, pd.DataFrame)
        check.is_instance(result.related_alerts, pd.DataFrame)
        check.is_instance(result.related_bookmarks, pd.DataFrame)
        check.is_instance(result.alert_timeline, LayoutDOM)
        check.is_instance(result.account_entity, entities.Account)

        alert_select = test_nb.browse_alerts()
        check.is_instance(alert_select, nbwidgets.SelectAlert)
        bm_select = test_nb.browse_bookmarks()
        assert isinstance(bm_select, nbwidgets.SelectItem)

        test_nb.get_additional_data()

        check.is_instance(result.account_timeline_by_ip, LayoutDOM)
        if "Windows" in item_value or "Linux" in item_value:
            check.is_instance(result.host_logons, pd.DataFrame)
            check.is_instance(result.host_logon_summary, pd.DataFrame)
            check.is_none(result.azure_activity)
            check.is_none(result.azure_activity_summary)
            check.is_none(result.azure_timeline_by_provider)
            check.is_none(result.azure_timeline_by_operation)
            vwr = result.view_events(
                attrib="host_logons",
                summary_cols=["Computer", "LogonResult", "LogonType"],
            )
        else:
            check.is_none(result.host_logons)
            check.is_none(result.host_logon_summary)
            check.is_instance(result.azure_activity, pd.DataFrame)
            check.is_instance(result.azure_activity_summary, pd.DataFrame)
            check.is_instance(result.azure_timeline_by_provider, LayoutDOM)
            check.is_instance(result.azure_timeline_by_operation, LayoutDOM)
            vwr = result.view_events(
                attrib="azure_activity",
                summary_cols=["Source", "Operation", "IPAddress"],
            )
        check.is_instance(vwr, nbwidgets.SelectItem)

        result.display_alert_timeline()
        result.browse_accounts()
        result.browse_alerts()
        result.browse_bookmarks()
        result.az_activity_timeline_by_provider()
        result.az_activity_timeline_by_ip()
        result.az_activity_timeline_by_operation()
        result.host_logon_timeline()
        check.is_not_none(result.get_geoip_map())
