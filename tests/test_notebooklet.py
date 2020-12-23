# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""common test class."""
# from contextlib import redirect_stdout
import unittest
from contextlib import redirect_stdout
from io import StringIO

import pandas as pd
from lxml import etree  # nosec
from markdown import markdown
from msticnb.common import MsticnbDataProviderError
from msticnb.data_providers import init
from msticnb.nb.azsent.host.host_summary import HostSummaryResult
from msticnb.read_modules import Notebooklet, nblts
from msticpy.common.exceptions import MsticpyUserConfigError
from msticpy.common.timespan import TimeSpan
from msticpy.sectools import GeoLiteLookup

from .nb_test import TstNBSummary


# pylint: disable=c-extension-no-member, protected-access
class TestNotebooklet(unittest.TestCase):
    """Unit test class."""

    def test_notebooklet_create(self):
        """Test method."""
        test_with_geop = True
        try:
            geoip = GeoLiteLookup()
            if not geoip._api_key:
                test_with_geop = False
            del geoip
        except MsticpyUserConfigError:
            test_with_geop = False

        if test_with_geop:
            # Should run because required providers are loaded
            init(query_provider="LocalData", providers=["tilookup", "geolitelookup"])
            for _, nblt in nblts.iter_classes():
                new_nblt = nblt()
                self.assertIsInstance(new_nblt, Notebooklet)
                self.assertIsNone(new_nblt.result)

        # Should throw a warning because of unrecognized provider
        init(query_provider="LocalData")
        with self.assertRaises(MsticnbDataProviderError) as err:
            for _, nblt in nblts.iter_classes():
                curr_provs = nblt.metadata.req_providers
                bad_provs = [*curr_provs, "bad_provider"]
                try:
                    nblt.metadata.req_providers = bad_provs
                    new_nblt = nblt()
                    self.assertIsInstance(new_nblt, Notebooklet)
                    self.assertIsNone(new_nblt.result)
                finally:
                    nblt.metadata.req_providers = curr_provs
        self.assertIn("bad_provider", err.exception.args[0])
        test_nb = TstNBSummary()
        self.assertIsNotNone(test_nb.get_provider("LocalData"))
        with self.assertRaises(MsticnbDataProviderError):
            test_nb.get_provider("otherprovider")

    def test_notebooklet_params(self):
        """Test supplying timespan param."""
        init(query_provider="LocalData", providers=["tilookup"])
        test_nb = TstNBSummary()

        tspan = TimeSpan(period="1D")
        test_nb.run(timespan=tspan)
        self.assertEqual(tspan, test_nb.timespan)

        test_nb.run(start=tspan.start, end=tspan.end)
        self.assertEqual(tspan, test_nb.timespan)

    def test_notebooklet_options(self):
        """Test option logic for notebooklet."""
        init(query_provider="LocalData")
        nb_test = TstNBSummary()

        # default options
        nb_res = nb_test.run()
        self.assertIsNotNone(nb_res.default_property)
        self.assertIsNone(nb_res.optional_property)

        # add optional option
        nb_res = nb_test.run(options=["+optional_opt"])
        self.assertIsNotNone(nb_res.default_property)
        self.assertIsNotNone(nb_res.optional_property)

        # remove default option
        nb_res = nb_test.run(options=["-default_opt"])
        self.assertIsNone(nb_res.default_property)
        self.assertIsNone(nb_res.optional_property)

        # specific options
        nb_res = nb_test.run(options=["heartbest", "azure_net"])
        self.assertIsNone(nb_res.default_property)
        self.assertIsNone(nb_res.optional_property)

        # invalid option
        f_stream = StringIO()
        with redirect_stdout(f_stream):
            nb_test.run(options=["invalid_opt"])
        output = str(f_stream.getvalue())
        self.assertIn("Invalid options ['invalid_opt']", output)

    def test_class_doc(self):
        """Test class documentation."""
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
        host_result.host_entity = {"host_name": "myhost"}
        host_result.related_alerts = pd.DataFrame()
        host_result.related_bookmarks = pd.DataFrame()
        self.assertIn("host_entity:", str(host_result))
        self.assertIn("DataFrame:", str(host_result))
        self.assertIn("host_entity", host_result.properties)

        html_doc = host_result._repr_html_()
        _html_parser = etree.HTMLParser(recover=False)
        elem_tree = etree.parse(StringIO(html_doc), _html_parser)
        self.assertIsNotNone(elem_tree)
