# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test the nb_template class."""
from pathlib import Path

import pandas as pd
from bokeh.models import LayoutDOM
from msticnb import nblts
from msticnb import data_providers
from msticpy.common.timespan import TimeSpan
from msticpy.datamodel import entities
from msticpy.nbtools import nbwidgets

from ....unit_test_lib import TEST_DATA_PATH, GeoIPLiteMock

# pylint: disable=protected-access, no-member


def test_account_summary_notebooklet(monkeypatch):
    """Test basic run of notebooklet."""
    test_data = str(Path(TEST_DATA_PATH).absolute())
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    data_providers.init(
        query_provider="LocalData",
        LocalData_data_paths=[test_data],
        LocalData_query_paths=[test_data],
    )

    test_nb = nblts.azsent.account.AccountSummary()
    tspan = TimeSpan(period="1D")

    result = test_nb.run(value="accountname", timespan=tspan)
    assert result.account_selector is not None
    acct_select = test_nb.browse_accounts()
    assert isinstance(acct_select, nbwidgets.SelectItem)

    select_opts = result.account_selector._item_dict
    disp_account = result.account_selector.item_action
    for acct_item in select_opts.values():
        # Programatically select the item list control
        select_item = [key for key, value in select_opts.items() if value == acct_item]
        if select_item:
            result.account_selector._wgt_select.value = select_item[0]
        disp_account(acct_item)
        assert isinstance(result.account_activity, pd.DataFrame)
        assert isinstance(result.related_alerts, pd.DataFrame)
        assert isinstance(result.related_bookmarks, pd.DataFrame)
        assert isinstance(result.alert_timeline, LayoutDOM)
        assert isinstance(result.account_entity, entities.Account)

        alert_select = test_nb.browse_alerts()
        assert isinstance(alert_select, nbwidgets.SelectAlert)
        bm_select = test_nb.browse_bookmarks()
        assert isinstance(bm_select, nbwidgets.SelectItem)

        test_nb.get_additional_data()

        assert isinstance(result.account_timeline_by_ip, LayoutDOM)
        if "Windows" in acct_item or "Linux" in acct_item:
            assert isinstance(result.host_logons, pd.DataFrame)
            assert isinstance(result.host_logon_summary, pd.DataFrame)
            assert result.azure_activity is None
            assert result.azure_activity_summary is None
            assert result.azure_timeline_by_provider is None
            assert result.azure_timeline_by_operation is None

        else:
            assert result.host_logons is None
            assert result.host_logon_summary is None
            assert isinstance(result.azure_activity, pd.DataFrame)
            assert isinstance(result.azure_activity_summary, pd.DataFrame)
            assert isinstance(result.azure_timeline_by_provider, LayoutDOM)
            assert isinstance(result.azure_timeline_by_operation, LayoutDOM)

        result.display_alert_timeline()
        result.browse_accounts()
        result.browse_alerts()
        result.browse_bookmarks()
        result.az_activity_timeline_by_provider()
        result.az_activity_timeline_by_ip()
        result.az_activity_timeline_by_operation()
        result.host_logon_timeline()
