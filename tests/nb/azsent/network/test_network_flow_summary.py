# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test the nb_template class."""
import sys
from pathlib import Path

import pandas as pd
import pytest
import pytest_check as check
from bokeh.models import LayoutDOM
from msticpy.common.timespan import TimeSpan

from msticnb import data_providers, nblts

from ....unit_test_lib import (
    DEF_PROV_TABLES,
    TEST_DATA_PATH,
    GeoIPLiteMock,
    TILookupMock,
)

# pylint: disable=no-member

if not sys.platform.startswith("win"):
    pytest.skip(
        "skipping Linux and Mac for these tests since Matplotlib fails with no gui",
        allow_module_level=True,
    )


def test_network_flow_summary_notebooklet(monkeypatch):
    """Test basic run of notebooklet."""
    test_data = str(Path(TEST_DATA_PATH).absolute())
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    monkeypatch.setattr(data_providers, "TILookup", TILookupMock)
    data_providers.init(
        query_provider="LocalData",
        LocalData_data_paths=[test_data],
        LocalData_query_paths=[test_data],
    )

    test_nb = nblts.azsent.network.NetworkFlowSummary()
    tspan = TimeSpan(period="1D")

    test_nb.query_provider.schema.update({tab: {} for tab in DEF_PROV_TABLES})
    options = ["+geo_map"]
    result = test_nb.run(value="myhost", timespan=tspan, options=options)
    check.is_not_none(result.host_entity)
    check.is_not_none(result.network_flows)
    check.is_instance(result.network_flows, pd.DataFrame)
    check.is_not_none(result.plot_flows_by_protocol)
    check.is_instance(result.plot_flows_by_protocol, LayoutDOM)
    check.is_not_none(result.plot_flows_by_direction)
    check.is_instance(result.plot_flows_by_direction, LayoutDOM)
    check.is_not_none(result.plot_flow_values)
    check.is_instance(result.plot_flow_values, LayoutDOM)
    check.is_not_none(result.flow_index)
    check.is_instance(result.flow_summary, pd.DataFrame)

    result.select_asns()
    result.lookup_ti_for_asn_ips()
    result.show_selected_asn_map()
