# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test case for hostslogonsummary nblet."""
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest
from bokeh.layouts import Column
from bokeh.plotting import Figure
from msticnb import nblts
from msticnb import data_providers
from msticpy.common.timespan import TimeSpan
from msticpy.nbtools.foliummap import FoliumMap

from ....unit_test_lib import TEST_DATA_PATH, GeoIPLiteMock

# nosec
# pylint: disable=no-member
if not sys.platform.startswith("win"):
    pytest.skip(
        "skipping Linux and Mac for these tests since Matplotlib fails with no gui",
        allow_module_level=True,
    )


@pytest.fixture
def nbltdata(monkeypatch):
    """Generate test nblt output."""
    test_file = Path.cwd().joinpath(TEST_DATA_PATH).joinpath("lx_host_logons.pkl")
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    data_providers.init("LocalData", providers=["tilookup", "geolitelookup"])
    test_nblt = nblts.azsent.host.HostLogonsSummary()
    test_df = pd.read_pickle(test_file)
    return test_nblt.run(data=test_df, options=["-map"], silent=True)


def test_output_types(nbltdata):  # pylint: disable=redefined-outer-name
    """Test nblt output types."""
    assert isinstance(nbltdata.failed_success, pd.DataFrame)
    assert isinstance(nbltdata.logon_sessions, pd.DataFrame)
    assert isinstance(nbltdata.logon_matrix, pd.io.formats.style.Styler)
    assert isinstance(nbltdata.plots, dict)
    assert isinstance(nbltdata.plots["User Pie Chart"], Figure)
    assert isinstance(nbltdata.timeline, Column)


def test_output_values(nbltdata):  # pylint: disable=redefined-outer-name
    """Test nblt output values."""
    assert nbltdata.failed_success.iloc[0]["LogonResult"] == "Success"
    assert nbltdata.logon_sessions.iloc[0]["HostName"] == "VictimHost"
    assert nbltdata.logon_matrix.index[0] == ("peteb", "sshd")


def test_local_data(monkeypatch):
    """Test nblt output types and values using LocalData provider."""
    test_data = str(Path.cwd().joinpath(TEST_DATA_PATH))
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    data_providers.init(
        query_provider="LocalData",
        LocalData_data_paths=[test_data],
        LocalData_query_paths=[test_data],
        providers=["tilookup", "geolitelookup"],
    )

    test_nblt = nblts.azsent.host.HostLogonsSummary()
    tspan = TimeSpan(
        start=datetime(2020, 6, 23, 4, 20), end=datetime(2020, 6, 29, 21, 32)
    )
    nbltlocaldata = test_nblt.run(value="WinAttackSim", timespan=tspan)
    assert isinstance(nbltlocaldata.logon_sessions, pd.DataFrame)
    assert nbltlocaldata.logon_sessions["SubjectUserName"].iloc[0] == "WinAttackSim$"
    assert nbltlocaldata.logon_sessions["LogonProcessName"].iloc[3] == "Advapi  "
    assert "User Pie Chart" in nbltlocaldata.plots.keys()
    assert isinstance(nbltlocaldata.plots["Process Bar Chart"], Figure)
    assert isinstance(nbltlocaldata.logon_matrix, pd.io.formats.style.Styler)
    assert nbltlocaldata.logon_matrix.index[0][0] == "Font Driver Host\\UMFD-0"
    assert isinstance(nbltlocaldata.logon_map, FoliumMap)
    assert isinstance(nbltlocaldata.timeline, Column)
