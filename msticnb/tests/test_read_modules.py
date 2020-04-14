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

from ..read_modules import discover_modules, Notebooklet


class TestReadModules(unittest.TestCase):
    """Unit test class."""

    def test_read_modules(self):
        nbklts = discover_modules()
        self.assertTrue(len(nbklts) > 1)

        match, m_count = nbklts.host.HostSummary.match_terms("host, linux, azure")
        self.assertTrue(match)
        self.assertEqual(m_count, 3)

        for key, value in nbklts.iter_classes():
            self.assertIsInstance(key, str)
            self.assertTrue(issubclass(value, Notebooklet))
