# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test the nb_template class."""
from pathlib import Path

# from contextlib import redirect_stdout
import pytest_check as check

import pandas as pd

from msticpy.common.timespan import TimeSpan
from msticnb.data_providers import init
from msticnb.nb.template.nb_template import TemplateNB
from ...unit_test_lib import TEST_DATA_PATH


def test_template_notebooklet():
    """Test basic run of notebooklet."""
    test_data = str(Path(TEST_DATA_PATH).absolute())
    init(
        query_provider="LocalData",
        LocalData_data_paths=[test_data],
        LocalData_query_paths=[test_data],
    )

    test_nb = TemplateNB()
    tspan = TimeSpan(period="1D")

    result = test_nb.run(value="myhost", timespan=tspan)
    check.is_not_none(result.all_events)
    check.is_not_none(result.description)
    check.is_not_none(result.plot)

    result = test_nb.run(value="myhost", timespan=tspan, options=["+get_metadata"])
    check.is_not_none(result.additional_info)

    evts = test_nb.run_additional_operation(["4679", "5058", "5061", "5059", "4776"])
    check.is_instance(evts, pd.DataFrame)
