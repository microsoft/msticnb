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


class TestHostSummary(unittest.TestCase):
    """Tests for nb_template."""

    def test_host_summary_notebooklet(self):
        """Test basic run of notebooklet."""
        test_data = str(Path(TEST_DATA_PATH).absolute())
        init(
            query_provider="LocalData",
            LocalData_data_paths=[test_data],
            LocalData_query_paths=[test_data],
        )

        test_nb = nblts.azsent.host.HostSummary()
        tspan = TimeSpan(period="1D")

        result = test_nb.run(value="myhost", timespan=tspan)
        self.assertIsNotNone(result.host_entity)
        self.assertIsNotNone(result.related_alerts)
        self.assertIsInstance(result.related_alerts, pd.DataFrame)
        self.assertIsNotNone(result.alert_timeline)
        self.assertIsNotNone(result.related_bookmarks)
        self.assertIsInstance(result.related_bookmarks, pd.DataFrame)
