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


def test_logon_session_rarity_notebooklet(init_notebooklets):
    """Test basic run of notebooklet."""
    try:
        # pylint: disable=import-outside-toplevel, unused-import
        import sklearn
        import matplotlib
    except ImportError:
        pytest.skip("sklearn and matplotlib required for this test")
    d_path = Path(TEST_DATA_PATH).joinpath("processes_on_host.pkl")
    raw_data = pd.read_pickle(d_path)
    filt_sess = raw_data[raw_data["Account"] == "MSTICAlertsWin1\\MSTICAdmin"]
    data = pd.concat([raw_data.iloc[:1000], filt_sess])

    check.is_true(hasattr(nblts.azsent.host, "LogonSessionsRarity"))
    if not hasattr(nblts.azsent.host, "LogonSessionsRarity"):
        print(nblts.azsent.host)
    test_nb = nblts.azsent.host.LogonSessionsRarity()

    result = test_nb.run(data=data)
    check.is_instance(result.process_clusters, pd.DataFrame)
    check.is_instance(result.processes_with_cluster, pd.DataFrame)
    check.is_instance(result.session_rarity, pd.DataFrame)
    result.list_sessions_by_rarity()
    result.plot_sessions_by_rarity()
    # result.process_tree(account="MSTICAlertsWin1\\MSTICAdmin")  # process tree fails with test data.
