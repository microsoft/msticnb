# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""data_providers test class."""
import sys

import pytest_check as check
from msticpy.data import QueryProvider
from msticpy.sectools.geoip import GeoLiteLookup
from msticpy.sectools import TILookup

from msticnb.data_providers import DataProviders, init


# pylint: disable=no-member


def test_init_data_providers():
    """Test creating DataProviders instance."""
    dprov = DataProviders(query_provider="LocalData")

    check.is_not_none(dprov)
    check.equal(dprov, DataProviders.current())

    check.is_in("LocalData", dprov.providers)
    check.is_in("geolitelookup", dprov.providers)
    check.is_in("tilookup", dprov.providers)
    check.is_instance(dprov.providers["LocalData"], QueryProvider)
    check.is_instance(dprov.providers["geolitelookup"], GeoLiteLookup)
    check.is_instance(dprov.providers["tilookup"], TILookup)


def test_new_init_data_providers():
    """Test creating new provider with new provider list."""
    init(query_provider="LocalData", providers=[])
    dprov = DataProviders.current()
    init(query_provider="LocalData", providers=[])
    dprov2 = DataProviders.current()
    check.equal(dprov2, dprov)

    # specify provider
    dprov = DataProviders(query_provider="LocalData")
    init(query_provider="LocalData", providers=["tilookup"])
    msticnb = sys.modules["msticnb"]
    dprov2 = DataProviders.current()
    pkg_providers = getattr(msticnb, "data_providers")
    check.not_equal(dprov2, dprov)
    check.is_in("LocalData", dprov2.providers)
    check.is_in("tilookup", dprov2.providers)
    check.is_not_in("geolitelookup", dprov2.providers)
    check.is_not_in("ipstacklookup", dprov2.providers)
    check.is_in("LocalData", pkg_providers)
    check.is_in("tilookup", pkg_providers)
    check.is_not_in("geolitelookup", pkg_providers)
    check.is_not_in("ipstacklookup", pkg_providers)

    check.is_instance(dprov2.providers["tilookup"], TILookup)


def test_add_sub_data_providers():
    """Test intializing adding and subtracting providers."""
    dprov = DataProviders(query_provider="LocalData")
    init(query_provider="LocalData", providers=["tilookup"])
    msticnb = sys.modules["msticnb"]
    dprov2 = DataProviders.current()

    # Add and remove a provider from defaults
    init(query_provider="LocalData", providers=["+ipstacklookup", "-geolitelookup"])

    dprov3 = DataProviders.current()
    pkg_providers = getattr(msticnb, "data_providers")
    check.not_equal(dprov3, dprov)
    check.not_equal(dprov3, dprov2)
    check.is_in("ipstacklookup", dprov3.providers)
    check.is_not_in("geolitelookup", dprov3.providers)
    check.is_in("tilookup", dprov3.providers)
    check.is_in("ipstacklookup", pkg_providers)
    check.is_not_in("geolitelookup", pkg_providers)
    check.is_in("tilookup", pkg_providers)
