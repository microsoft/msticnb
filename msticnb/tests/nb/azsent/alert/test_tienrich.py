# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test case for EnrichAlerts nblet."""
import os
from pathlib import Path

from datetime import datetime
import pytest
import pandas as pd
from bokeh.plotting import Figure
from bokeh.layouts import Column
from msticpy.nbtools.foliummap import FoliumMap
from msticpy.nbtools.nbwidgets import SelectAlert

from .....data_providers import init
from .....read_modules import nblts
from .....common import TimeSpan

_TESTDATA_FOLDER = Path("msticnb\\tests\\testdata")


@pytest.fixture
def nbltdata():
    """Generate test nblt output."""
    test_file = Path.cwd().joinpath(_TESTDATA_FOLDER).joinpath("alerts_list.pkl")
    test_config = str(
        Path.cwd().joinpath(_TESTDATA_FOLDER).joinpath("msticpyconfig-test.yaml")
    )
    init("LocalData", providers=["tilookup"])
    test_nblt = nblts.azsent.alert.EnrichAlerts()
    test_df = pd.read_pickle(test_file)
    test_df["Entities"] = ""
    test_data_out = test_nblt.run(data=test_df, silent=True)
    return test_data_out


def test_ouput_types(nbltdata):  # pylint: disable=redefined-outer-name
    """Test nblt output types."""
    assert isinstance(nbltdata.enriched_results, pd.DataFrame)
    assert isinstance(nbltdata.picker, SelectAlert)


def test_ouput_values(nbltdata):  # pylint: disable=redefined-outer-name
    """Test nblt output values."""
    assert nbltdata.enriched_results.iloc[0]["Severity"] == "Low"
    assert (
        nbltdata.picker.alerts.iloc[0]["SystemAlertId"]
        == "f1ce87ca-8863-4a66-a0bd-a4d3776a7c64"
    )
