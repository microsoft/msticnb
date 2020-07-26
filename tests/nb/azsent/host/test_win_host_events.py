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
from msticnb import nblts
from msticnb.data_providers import init

from ....unit_test_lib import TEST_DATA_PATH


# pylint: disable=no-member


class TestWinHostEvents(unittest.TestCase):
    """Tests for nb_template."""

    def test_winhostevents_notebooklet(self):
        """Test basic run of notebooklet."""
        test_data = str(Path(TEST_DATA_PATH).absolute())
        init(
            query_provider="LocalData",
            LocalData_data_paths=[test_data],
            LocalData_query_paths=[test_data],
        )

        test_nb = nblts.azsent.host.WinHostEvents()
        tspan = TimeSpan(period="1D")

        result = test_nb.run(value="myhost", timespan=tspan)
        self.assertIsNotNone(result.all_events)
        self.assertIsInstance(result.all_events, pd.DataFrame)
        self.assertIsNotNone(result.event_pivot)
        self.assertIsInstance(result.event_pivot, pd.DataFrame)
        self.assertIsNotNone(result.account_events)
        self.assertIsInstance(result.account_events, pd.DataFrame)
        self.assertIsNotNone(result.event_pivot)
        self.assertIsInstance(result.event_pivot, pd.DataFrame)
        # self.assertIsNotNone(result.account_timeline)

        exp_events = test_nb.expand_events(["5058", "5061"])
        self.assertIsInstance(exp_events, pd.DataFrame)
