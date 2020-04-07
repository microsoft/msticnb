# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""read_modules test class."""
import unittest
# from datetime import datetime
# import pytest
# import warnings

from ..read_modules import discover_modules


class TestReadModules(unittest.TestCase):
    """Unit test class."""

    def test_read_modules(self):
        discover_modules()
