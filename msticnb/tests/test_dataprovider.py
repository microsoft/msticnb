# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""data_providers test class."""
import sys
import unittest
from msticpy.data import QueryProvider
from msticpy.sectools.geoip import GeoLiteLookup
from msticpy.sectools import TILookup

from ..data_providers import DataProviders, init


# pylint: disable=no-member


class TestDataProviders(unittest.TestCase):
    """Unit test class."""

    def test_init_data_providers(self):
        """Test creating DataProviders instance."""
        dprov = DataProviders(query_provider="LocalData")

        self.assertIsNotNone(dprov)
        self.assertIs(dprov, DataProviders.current())

        self.assertIn("LocalData", dprov.providers)
        self.assertIn("geolitelookup", dprov.providers)
        self.assertIn("tilookup", dprov.providers)
        self.assertIsInstance(dprov.providers["LocalData"], QueryProvider)
        self.assertIsInstance(dprov.providers["geolitelookup"], GeoLiteLookup)
        self.assertIsInstance(dprov.providers["tilookup"], TILookup)

    def test_new_init_data_providers(self):
        """Test creating new provider with new provider list."""
        init(query_provider="LocalData", providers=[])
        dprov = DataProviders.current()
        init(query_provider="LocalData", providers=[])
        dprov2 = DataProviders.current()
        self.assertIs(dprov2, dprov)

        # specify provider
        dprov = DataProviders(query_provider="LocalData")
        init(query_provider="LocalData", providers=["tilookup"])
        msticnb = sys.modules["msticnb"]
        dprov2 = DataProviders.current()
        pkg_providers = getattr(msticnb, "data_providers")
        self.assertIsNot(dprov2, dprov)
        self.assertIn("LocalData", dprov2.providers)
        self.assertIn("tilookup", dprov2.providers)
        self.assertNotIn("geolitelookup", dprov2.providers)
        self.assertNotIn("ipstacklookup", dprov2.providers)
        self.assertIn("LocalData", pkg_providers)
        self.assertIn("tilookup", pkg_providers)
        self.assertNotIn("geolitelookup", pkg_providers)
        self.assertNotIn("ipstacklookup", pkg_providers)

        self.assertIsInstance(dprov2.providers["tilookup"], TILookup)

    def test_add_sub_data_providers(self):
        """Test intializing adding and subtracting providers."""
        dprov = DataProviders(query_provider="LocalData")
        init(query_provider="LocalData", providers=["tilookup"])
        msticnb = sys.modules["msticnb"]
        dprov2 = DataProviders.current()

        # Add and remove a provider from defaults
        init(query_provider="LocalData", providers=["+ipstacklookup", "-geolitelookup"])

        dprov3 = DataProviders.current()
        pkg_providers = getattr(msticnb, "data_providers")
        self.assertIsNot(dprov3, dprov)
        self.assertIsNot(dprov3, dprov2)
        self.assertIn("ipstacklookup", dprov3.providers)
        self.assertNotIn("geolitelookup", dprov3.providers)
        self.assertIn("tilookup", dprov3.providers)
        self.assertIn("ipstacklookup", pkg_providers)
        self.assertNotIn("geolitelookup", pkg_providers)
        self.assertIn("tilookup", pkg_providers)
