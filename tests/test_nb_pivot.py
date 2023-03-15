# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test module for nb_pivot."""
from pathlib import Path

import pytest
import pytest_check as check
from msticpy.datamodel import entities

try:
    from msticpy.init.pivot import Pivot
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.datamodel.pivot import Pivot

from msticnb import data_providers, init, nblts
from msticnb.nb_pivot import add_pivot_funcs
from msticnb.notebooklet import NotebookletResult

from .unit_test_lib import TEST_DATA_PATH, GeoIPLiteMock

__author__ = "Ian Hellen"

# pylint: disable=redefined-outer-name

_EXPECTED_FUNCS = [
    (
        "Host",
        (
            "host_logons_summary",
            "host_summary",
            "win_host_events",
            "network_flow_summary",
        ),
        "test_host",
    ),
    ("Account", ("account_summary",), "test_acct"),
    ("IpAddress", ("network_flow_summary",), "11.1.2.3"),
]


@pytest.fixture
def _init_pivot(monkeypatch):
    init()
    test_data = str(Path(TEST_DATA_PATH).absolute())
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    if "azuredata" in nblts.azsent.host.HostSummary.metadata.req_providers:
        nblts.azsent.host.HostSummary.metadata.req_providers.remove("azuredata")
    data_providers.init(
        query_provider="LocalData",
        providers=["geolitelookup"],
        LocalData_data_paths=[test_data],
        LocalData_query_paths=[test_data],
    )
    return Pivot()


@pytest.mark.parametrize("ent_name, funcs, test_val", _EXPECTED_FUNCS)
def test_add_pivot_funcs(_init_pivot, ent_name, funcs, test_val):
    """Test adding notebooklets to pivot."""
    del test_val
    add_pivot_funcs(_init_pivot)

    entity = getattr(entities, ent_name)
    container = getattr(entity, "nblt")
    for func_name in funcs:
        check.is_true(hasattr(container, func_name))


@pytest.mark.parametrize("ent_name, funcs, test_val", _EXPECTED_FUNCS)
def test_run_pivot_funcs(_init_pivot, ent_name, funcs, test_val):
    """Test running notebooklets run functions."""
    add_pivot_funcs(_init_pivot)

    entity = getattr(entities, ent_name)

    check.is_true(hasattr(entity, "nblt"))
    container = getattr(entity, "nblt")
    for _, p_func in container:
        if p_func.__name__ not in funcs:
            continue
        check.is_true(callable(p_func))
        result = p_func(value=test_val)
        test_result = result[0] if isinstance(result, list) else result
        check.is_true(isinstance(test_result, NotebookletResult))
        check.equal(test_result.timespan, _init_pivot.get_timespan())
