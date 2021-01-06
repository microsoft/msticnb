# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test case for EnrichAlerts nblet."""
from pathlib import Path

import pandas as pd
import pytest

from msticnb import nblts
from msticnb.data_providers import init
from msticpy.nbtools.nbwidgets import SelectAlert

from ....unit_test_lib import TEST_DATA_PATH


@pytest.fixture
def nbltdata():
    """Generate test nblt output."""
    test_file = Path.cwd().joinpath(TEST_DATA_PATH).joinpath("alerts_list.pkl")
    test_config = str(
        Path.cwd().joinpath(TEST_DATA_PATH).joinpath("msticpyconfig-test.yaml")
    )
    init("LocalData", providers=["tilookup"])
    test_nblt = nblts.azsent.alert.EnrichAlerts()  # pylint: disable=no-member
    test_df = pd.read_pickle(test_file)
    test_df["Entities"] = ""
    return test_nblt.run(data=test_df, silent=True)


def test_output_types(nbltdata):  # pylint: disable=redefined-outer-name
    """Test nblt output types."""
    assert isinstance(nbltdata.enriched_results, pd.DataFrame)
    assert isinstance(nbltdata.picker, SelectAlert)


def test_output_values(nbltdata):  # pylint: disable=redefined-outer-name
    """Test nblt output values."""
    assert nbltdata.enriched_results.iloc[0]["Severity"] == "Low"
    assert (
        nbltdata.picker.alerts.iloc[0]["SystemAlertId"]
        == "f1ce87ca-8863-4a66-a0bd-a4d3776a7c64"
    )
