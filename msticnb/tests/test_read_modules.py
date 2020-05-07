# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""read_modules test class."""
import unittest

from ..read_modules import discover_modules, Notebooklet, find, nblts


class TestReadModules(unittest.TestCase):
    """Unit test class."""

    def test_read_modules(self):
        """Test method."""
        nbklts = discover_modules()
        self.assertGreaterEqual(len(list(nbklts.iter_classes())), 3)

        # pylint: disable=no-member
        match, m_count = nblts.azsent.host.HostSummary.match_terms("host, linux, azure")
        self.assertTrue(match)
        self.assertEqual(m_count, 3)

        for key, value in nbklts.iter_classes():
            self.assertIsInstance(key, str)
            self.assertTrue(issubclass(value, Notebooklet))

        find_res = find("host windows azure")
        self.assertGreater(len(find_res), 0)
        not_found = find("monkey stew")
        self.assertEqual(len(not_found), 0)
