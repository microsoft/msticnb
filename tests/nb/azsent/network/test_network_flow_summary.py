# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test the nb_template class."""
from pathlib import Path

# from contextlib import redirect_stdout
import unittest

from bokeh.models import LayoutDOM
import pandas as pd

from msticpy.common.timespan import TimeSpan
from msticnb import nblts
from msticnb.data_providers import init

from ....unit_test_lib import TEST_DATA_PATH


# pylint: disable=no-member


class TestNetworkFlowSummary(unittest.TestCase):
    """Tests for nb_template."""

    def test_network_flow_summary_notebooklet(self):
        """Test basic run of notebooklet."""
        test_data = str(Path(TEST_DATA_PATH).absolute())
        init(
            query_provider="LocalData",
            LocalData_data_paths=[test_data],
            LocalData_query_paths=[test_data],
        )

        test_nb = nblts.azsent.network.NetworkFlowSummary()
        tspan = TimeSpan(period="1D")

        result = test_nb.run(value="myhost", timespan=tspan)
        self.assertIsNotNone(result.host_entity)
        self.assertIsNotNone(result.network_flows)
        self.assertIsInstance(result.network_flows, pd.DataFrame)
        self.assertIsNotNone(result.plot_flows_by_protocol)
        self.assertIsInstance(result.plot_flows_by_protocol, LayoutDOM)
        self.assertIsNotNone(result.plot_flows_by_direction)
        self.assertIsInstance(result.plot_flows_by_direction, LayoutDOM)
        self.assertIsNotNone(result.plot_flow_values)
        self.assertIsInstance(result.plot_flow_values, LayoutDOM)
        self.assertIsNotNone(result.flow_index)
        self.assertIsInstance(result.flow_summary, pd.DataFrame)
