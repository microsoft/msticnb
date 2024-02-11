# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""read_modules test class."""
from pathlib import Path

import pytest_check as check

from msticnb.read_modules import Notebooklet, discover_modules, find, nb_index, nblts

from .unit_test_lib import TEST_DATA_PATH


def test_read_modules():
    """Test method."""
    nbklts = discover_modules()
    check.greater_equal(len(list(nbklts.iter_classes())), 4)

    # pylint: disable=no-member
    match, m_count = nblts.azsent.host.HostSummary.match_terms("host, linux, azure")
    check.is_true(match)
    check.equal(m_count, 3)

    for key, value in nbklts.iter_classes():
        check.is_instance(key, str)
        check.is_true(issubclass(value, Notebooklet))

    find_res = find("host windows azure")
    check.greater(len(find_res), 0)
    not_found = find("monkey stew")
    check.equal(len(not_found), 0)


def test_read_custom_path():
    """Test method."""
    cust_nb_path = Path(TEST_DATA_PATH).parent / "custom_nb"
    nbklts = discover_modules(nb_path=str(cust_nb_path))
    check.greater_equal(len(list(nbklts.iter_classes())), 5)

    # pylint: disable=no-member
    match, m_count = nblts.custom_nb.host.CustomNB.match_terms("Custom")
    check.is_true(match)
    check.equal(m_count, 1)

    for key, value in nbklts.iter_classes():
        check.is_instance(key, str)
        check.is_true(issubclass(value, Notebooklet))

    find_res = find("banana")
    check.equal(len(find_res), 1)
    find_res = find("<<Test Marker>>")
    check.equal(len(find_res), 1)
    check.equal(find_res[0][0], "CustomNB")
    check.is_in("nblts.host.CustomNB", nb_index)
