# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Unit test common utilities."""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

try:
    from msticpy.context import TILookup
    from msticpy.context.geoip import GeoIpLookup
except ImportError:
    from msticpy.sectools.geoip import GeoIpLookup
    from msticpy.sectools.tilookup import TILookup

from msticpy.datamodel.entities import GeoLocation, IpAddress

from msticnb.common import check_mp_version

__author__ = "Ian Hellen"


def get_test_data_path():
    """Get path to testdata folder."""
    cur_dir = Path(".").absolute()
    td_paths = []
    if cur_dir.joinpath("tests/testdata").is_dir():
        return cur_dir.joinpath("tests/testdata")
    td_path = None
    while not td_paths:
        td_paths = list(cur_dir.glob("**/tests/testdata"))
        if td_paths:
            td_path = str(td_paths[0])
            break
        if cur_dir.root() == cur_dir:
            raise FileNotFoundError("Cannot find testdata folder")
        cur_dir = cur_dir.parent

    return Path(td_path).absolute()


TEST_DATA_PATH = str(get_test_data_path())


DEF_PROV_TABLES = [
    "SecurityEvent",
    "SecurityAlert",
    "Syslog",
    "AzureNetworkAnalytics_CL",
    "Heartbeat",
    "SigninLogs",
    "OfficeActivity",
    "Bookmark",
    "AzureActivity",
    "VMComputer",
]


class GeoIPLiteMock(GeoIpLookup):
    """Test class for GeoIPLookup."""

    def __init__(self, *args, **kwargs):
        """Initialize test GeoIPLite."""
        del args, kwargs
        super().__init__()

    def lookup_ip(
        self, ip_address: str = None, ip_addr_list: list = None, ip_entity=None
    ) -> tuple:
        """
        Lookup IP location abstract method.

        Parameters
        ----------
        ip_address : str, optional
            a single address to look up (the default is None)
        ip_addr_list : Iterable, optional
            a collection of addresses to lookup (the default is None)
        ip_entity : IpAddress, optional
            an IpAddress entity (the default is None) - any existing
            data in the Location property will be overwritten

        Returns
        -------
        Tuple[List[Any], List[IpAddress]]:
            raw geolocation results and same results as IpAddress entities with
            populated Location property.

        """
        if ip_address:
            geo = _get_geo_loc()
            ip_ent = IpAddress(Address=ip_address, Location=geo)
            return str(geo), [ip_ent]
        if ip_entity:
            geo = _get_geo_loc()
            ip_entity.Location = geo
            return [str(geo)], [ip_entity]

        if ip_addr_list:
            output_raw = []
            output_entities = []
            for addr in ip_addr_list:
                raw, ents = self.lookup_ip(ip_address=addr)
                output_raw.extend(raw)
                output_entities.extend(ents)
            return output_raw, output_entities
        return [], []


def _get_geo_loc():
    return GeoLocation(
        CountryCode="US",
        CountryName="United States",
        State="WA",
        City="Seattle",
        Longitude=float(random.randint(-179, +179)),
        Latitude=float(random.randint(-89, 89)),
        Asn="My ASN",
    )


# Need to keep same signature as mocked class
# pylint: disable=no-self-use
class TILookupMock:
    """Test class for TILookup."""

    def __init__(self, *args, **kwargs):
        """Initialize mock class."""
        del args, kwargs

    def lookup_ioc(
        self, ioc=None, observable=None, ioc_type: Optional[str] = None, **kwargs
    ):
        """Lookup fake TI."""
        ioc = ioc or kwargs.get("observable")
        result_list: List[Dict[str, Any]] = []
        providers = kwargs.get("providers", ["VirusTotal", "OTX", "Tor"])
        for provider in providers:
            hit = random.randint(1, 10) > 5

            result_args = {
                "Provider": provider,
                "Ioc": observable,
                "IocType": ioc_type,
                "QuerySubtype": "mock",
                "Result": True,
                "Severity": 2 if hit else 0,
                "Details": f"Details for {observable}",
                "RawResult": {"resolutions": f"Raw details for {observable}"},
            }
            if check_mp_version("2.0"):
                result_args["sanitized_value"] = observable
            else:
                result_args["SafeIoC"] = observable
            result_list.append(result_args)
        return pd.DataFrame(result_list)

    def lookup_iocs(self, data, ioc_col: Optional[str] = None, **kwargs):
        """Lookup fake TI."""
        del kwargs
        item_result: List[pd.DataFrame] = []
        if isinstance(data, dict):
            item_result.extend(
                self.lookup_ioc(observable=obs, ioc_type=ioc_type)
                for obs, ioc_type in data.items()
            )
        elif isinstance(data, pd.DataFrame):
            item_result.extend(
                self.lookup_ioc(observable=getattr(row, ioc_col))
                for row in data.itertuples()
            )
        elif isinstance(data, list):
            item_result.extend(self.lookup_ioc(observable=obs) for obs in data)
        return pd.concat(item_result) if item_result else pd.DataFrame()

    @classmethod
    def result_to_df(cls, ioc_lookup):
        """Redirect to original method."""
        return TILookup.result_to_df(ioc_lookup)

    @property
    def loaded_providers(self) -> List[str]:
        """Return list of loaded providers."""
        return ["VirusTotal", "OTX", "Tor"]
