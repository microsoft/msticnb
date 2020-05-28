# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""NB metadata test class."""
import unittest

from .. import init
from ..nb_metadata import NBMetaData, read_module_metadata
from ..nb.azsent.host import host_summary


class TestMetadata(unittest.TestCase):
    """Unit test class."""

    def test_read_metadata(self):
        """Tests reading metadata yaml file."""
        nb_md, docs = read_module_metadata(host_summary.__name__)
        self.assertIsInstance(nb_md, NBMetaData)
        self.assertIsInstance(docs, dict)

        opts = nb_md.get_options("all")
        self.assertIn("heartbeat", [opt[0] for opt in opts])
        self.assertIn("alerts", [opt[0] for opt in opts])

        for item in ("Default Options", "alerts", "azure_api"):
            self.assertIn(item, nb_md.options_doc)

        # try adding metadata to this class docstring
        self.__class__.__doc__ += nb_md.options_doc
        self.assertTrue(self.__class__.__doc__)
        for item in ("Default Options", "alerts", "azure_api"):
            self.assertIn(item, self.__class__.__doc__)

    # pylint: disable=protected-access
    def test_class_metadata(self):
        """Test class correctly loads yaml metadata."""
        init(query_provider="LocalData", providers=["tilookup"])
        host_nb = host_summary.HostSummary()

        self.assertTrue(hasattr(host_summary, "_CLS_METADATA"))
        self.assertIsInstance(host_summary._CLS_METADATA, NBMetaData)
        self.assertTrue(hasattr(host_summary, "_CELL_DOCS"))
        self.assertIsInstance(host_summary._CELL_DOCS, dict)

        self.assertTrue(hasattr(host_nb, "metadata"))
        self.assertIsInstance(host_nb.metadata, NBMetaData)
        self.assertEqual(host_nb.metadata.mod_name, host_summary.__name__)
        self.assertEqual(host_nb.description(), "Host summary")
        self.assertEqual(host_nb.name(), "HostSummary")
        self.assertIn("host", host_nb.entity_types())
        self.assertIn("host", host_nb.keywords())

        self.assertIn("heartbeat", host_nb.default_options())
        self.assertIn("alerts", host_nb.default_options())

        self.assertIn("alerts", host_nb.all_options())

        for item in ("Default Options", "alerts", "azure_api"):
            self.assertIn(item, host_nb.list_options())
