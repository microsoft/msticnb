# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""common test class."""
from io import StringIO
# from contextlib import redirect_stdout
import unittest

from lxml import etree  # nosec
from markdown import markdown
import pandas as pd

from ..common import MsticnbDataProviderError

from ..read_modules import Notebooklet, nblts
from ..nb.azsent.host.host_summary import HostSummaryResult


# pylint: disable=c-extension-no-member, protected-access
class TestNotebooklet(unittest.TestCase):
    """Unit test class."""

    def test_notebooklet(self):
        """Test method."""
        for _, nblt in nblts.iter_classes():
            # TODO -need test dataprovider
            with self.assertRaises(MsticnbDataProviderError):
                new_nblt = nblt()
                self.assertIsInstance(new_nblt, Notebooklet)
                self.assertIsNone(new_nblt.result)

    def test_class_doc(self):
        """Test method."""
        for _, nblt in nblts.iter_classes():
            html_doc = nblt.get_help()
            self.assertNotEqual(html_doc, "No documentation available.")
            self.assertGreater(len(html_doc), 100)

            md_doc = nblt.get_help(fmt="md")
            html_doc2 = markdown(md_doc)
            self.assertEqual(html_doc, html_doc2)

            _html_parser = etree.HTMLParser(recover=False)
            elem_tree = etree.parse(StringIO(html_doc), _html_parser)
            self.assertIsNotNone(elem_tree)

    def test_class_methods(self):
        """Test method."""
        for _, nblt in nblts.iter_classes():
            self.assertIsNotNone(nblt.description())
            self.assertIsNotNone(nblt.name())
            self.assertGreater(len(nblt.all_options()), 0)
            self.assertGreater(len(nblt.default_options()), 0)
            self.assertGreater(len(nblt.keywords()), 0)
            self.assertGreater(len(nblt.entity_types()), 0)
            metadata = nblt.get_settings(print_settings=False)
            self.assertIsNotNone(metadata)
            self.assertIn("mod_name", metadata)
            self.assertIn("default_options", metadata)
            self.assertIn("keywords", metadata)

    def test_nbresult(self):
        """Test method."""
        host_result = HostSummaryResult()
        host_result.related_alerts = pd.DataFrame()
        host_result.related_bookmarks = pd.DataFrame()
        self.assertIn("host_entity:", str(host_result))
        self.assertIn("DataFrame:", str(host_result))

        html_doc = host_result._repr_html_()
        _html_parser = etree.HTMLParser(recover=False)
        elem_tree = etree.parse(StringIO(html_doc), _html_parser)
        self.assertIsNotNone(elem_tree)
