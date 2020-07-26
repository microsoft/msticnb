# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test the nb_template class."""
from pathlib import Path

# from contextlib import redirect_stdout
import unittest

import pandas as pd

from msticnb.common import TimeSpan
from msticnb.data_providers import init
from msticnb.nb.template.nb_template import TemplateNB
from ...unit_test_lib import TEST_DATA_PATH


class TestTemplateNB(unittest.TestCase):
    """Tests for nb_template."""

    def test_template_notebooklet(self):
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
        self.assertIsNotNone(result.all_events)
        self.assertIsNotNone(result.description)
        self.assertIsNotNone(result.plot)

        result = test_nb.run(value="myhost", timespan=tspan, options=["+get_metadata"])
        self.assertIsNotNone(result.additional_info)

        evts = test_nb.run_additional_operation(
            ["4679", "5058", "5061", "5059", "4776"]
        )
        self.assertIsInstance(evts, pd.DataFrame)
