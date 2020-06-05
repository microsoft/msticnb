# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Unit test common utilities."""
from pathlib import Path

__author__ = "Ian Hellen"


def get_test_data_path():
    """Get path to testdata folder."""
    cur_dir = Path(".").absolute()
    td_paths = []
    td_path = None
    while not td_paths:
        td_paths = list(cur_dir.glob("**/tests/testdata"))
        if td_paths:
            td_path = str(td_paths[0])
            break
        if cur_dir.root() == cur_dir:
            raise FileNotFoundError("Cannot find testdata folder")
        cur_dir = cur_dir.parent

    return td_path


TEST_DATA_PATH = get_test_data_path()
