# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test case for hostslogonsummary nblet."""
from pathlib import Path

import pytest
import pandas as pd
from bokeh.plotting import Figure
from bokeh.layouts import Column

from .....data_providers import init
from .....read_modules import nblts

_TESTDATA_FOLDER = Path("msticnb\\tests\\nb\\azsent\\host\\testdata")


@pytest.fixture
def nbltdata():
    """Generate test nblt output."""
    test_file = Path.cwd().joinpath(_TESTDATA_FOLDER).joinpath("host_logons_sample.pkl")
    init("LocalData", providers=["tilookup"])
    for name, nblt in nblts.iter_classes():
        if name == "HostLogonsSummary":
            test_nblt = nblt()
    test_df = pd.read_pickle(test_file)
    test_data_out = test_nblt.run(data=test_df, options=["-map"], silent=True)
    return test_data_out


def test_ouput_types(nbltdata):  # pylint: disable=redefined-outer-name
    """Test nblt output types."""
    assert isinstance(nbltdata.failed_success, pd.DataFrame)
    assert isinstance(nbltdata.logon_sessions, pd.DataFrame)
    assert isinstance(nbltdata.logon_matrix, pd.io.formats.style.Styler)
    assert isinstance(nbltdata.plots, dict)
    assert isinstance(nbltdata.plots["User Pie Chart"], Figure)
    assert isinstance(nbltdata.timeline, Column)


def test_ouput_values(nbltdata):  # pylint: disable=redefined-outer-name
    """Test nblt output values."""
    assert nbltdata.failed_success.iloc[0]["LogonResult"] == "Success"
    assert nbltdata.logon_sessions.iloc[0]["HostName"] == "VictimHost"
    assert nbltdata.logon_matrix.index[0] == ("peteb", "sshd")
