# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Unit test common utilities."""
import random
from pathlib import Path

import attr
import pandas as pd

try:
    from msticpy.context import TILookup
    from msticpy.context.geoip import GeoIpLookup
    from msticpy.context.tiproviders.ti_provider_base import LookupResult
except ImportError:
    from msticpy.sectools.geoip import GeoIpLookup
    from msticpy.sectools.tilookup import TILookup
    from msticpy.sectools.tiproviders.ti_provider_base import LookupResult

from msticpy.datamodel.entities import GeoLocation, IpAddress

from msticnb.common import check_mp_version

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


# Need to keep same signatire as mocked class
# pylint: disable=no-self-use
class TILookupMock:
    """Test class for TILookup."""

    def __init__(self, *args, **kwargs):
        """Initialize mock class."""
        del args, kwargs

    def lookup_ioc(self, observable, ioc_type: str = None, **kwargs):
        """Lookup fake TI."""
        del kwargs
        result_list = []
        for i in range(3):
            hit = random.randint(1, 10) > 5

            result_args = dict(
                ioc=observable,
                ioc_type=ioc_type,
                query_subtype="mock",
                provider="mockTI",
                result=True,
                severity=2 if hit else 0,
                details=f"Details for {observable}",
                raw_result=f"Raw details for {observable}",
            )
            if check_mp_version("2.0"):
                result_args["sanitized_value"] = observable
            else:
                result_args["safe_ioc"] = observable
            result_list.append((f"TIProv{i}", LookupResult(**result_args)))
        return True, result_list

    def lookup_iocs(self, data, obs_col: str = None, **kwargs):
        """Lookup fake TI."""
        del kwargs
        if isinstance(data, dict):
            for obs, ioc_type in data.items():
                _, item_result = self.lookup_ioc(observable=obs, ioc_type=ioc_type)
        elif isinstance(data, pd.DataFrame):
            for row in data.itertuples():
                _, item_result = self.lookup_ioc(observable=row[obs_col])
        elif isinstance(data, list):
            for obs in data:
                _, item_result = self.lookup_ioc(observable=obs)
        results = [pd.Series(attr.asdict(ti_result)) for _, ti_result in item_result]
        return pd.DataFrame(data=results).rename(columns=LookupResult.column_map())

    @classmethod
    def result_to_df(cls, ioc_lookup):
        """Redirect to original method."""
        return TILookup.result_to_df(ioc_lookup)
