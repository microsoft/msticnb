# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""IP Helper functions."""
import re
from collections import defaultdict
from ipaddress import AddressValueError, IPv4Address, IPv4Network, ip_address
from typing import Optional

import pandas as pd
import requests
from msticpy.sectools.ip_utils import get_whois_df

from .._version import VERSION
from ..common import nb_markdown

__version__ = VERSION
__author__ = "Ian Hellen"


def get_ip_ti(
    ti_lookup,
    data: pd.DataFrame,
    ip_col: str,
) -> pd.DataFrame:
    """
    Lookup Threat Intel for IPAddress.

    Parameters
    ----------
    ti_lookup : TILookup
        TI Lookup provider
    data : pd.DataFrame
        Input data frame
    ip_col : str
        Name of Ip address column

    Returns
    -------
    pd.DataFrame
        DataFrame with TI results for IPs

    """
    data = _normalize_ip4(data, ip_col)
    src_ip_addrs = data[[ip_col]].dropna().drop_duplicates()
    nb_markdown(f"Querying TI for {len(src_ip_addrs)} indicators...")
    ti_results = ti_lookup.lookup_iocs(data=src_ip_addrs, obs_col=ip_col)
    ti_results = ti_results[ti_results["Severity"].isin(["warning", "high"])]

    ti_merged_df = data.merge(ti_results, how="left", left_on=ip_col, right_on="Ioc")
    return ti_results, ti_merged_df, src_ip_addrs


def _normalize_ip4(data, ip_col):
    ip4_rgx = r"((?:[0-9]{1,3}\.){3}[0-9]{1,3})"
    return (
        data.assign(IP_ext=lambda x: x[ip_col].str.extract(ip4_rgx, expand=False))
        .rename(columns={ip_col: ip_col + "_orig"})
        .rename(columns={"IP_ext": ip_col})
    )


def get_geoip_whois(geo_lookup, data: pd.DataFrame, ip_col: str):
    """
    Get GeoIP and WhoIs data for IPs.

    Parameters
    ----------
    geo_lookup : GeoIpLookup
        GeoIP Provider
    data : pd.DataFrame
        Input data frame
    ip_col : str
        Name of Ip address column

    Returns
    -------
    pd.DataFrame
        Results dataframe with GeoIP and WhoIs data

    """
    data = _normalize_ip4(data, ip_col)
    nb_markdown(f"Querying geolocation for {len(data)} ip addresses...")

    geo_ips = geo_lookup.lookup_ips(data, column=ip_col)
    geo_df = data.merge(geo_ips, how="left", left_on=ip_col, right_on="IpAddress")

    nb_markdown(f"Querying WhoIs for {len(data)} ip addresses...")
    # Get the WhoIs results
    return get_whois_df(geo_df, "IpAddress", whois_col="Whois_data")


_VPS_URL = (
    "https://raw.githubusercontent.com/Azure/Azure-Sentinel/"
    + "master/Sample%20Data/Feeds/VPS_Networks.csv"
)
_NET_DICT = defaultdict(list)


def _build_vps_dict():
    resp = requests.get(_VPS_URL)

    # get rid of unicode bytes
    net_list = re.sub(r"[^\d./\n]", "", resp.text).split("\n")

    # Build network dict - keyed by 16 bit prefix
    for net in net_list:
        pref, ip4_net = _to_ip4_net(net)
        if pref:
            _NET_DICT[pref].append(ip4_net)
    return _NET_DICT


def _get_prefix(ip_addr):
    return ".".join(ip_addr.split(".", maxsplit=2)[:2])


def _to_ip4_net(net):
    try:
        return _get_prefix(net), IPv4Network(net)
    except AddressValueError as err:
        print(err, type(err))
        return None, None


def is_in_vps_net(ip_addr: str) -> Optional[IPv4Network]:
    """
    Return IpV4 Network if `ip_addr` is in a found VPS network.

    Parameters
    ----------
    ip_addr : str
        IP Address

    Returns
    -------
    Optional[IPv4Network]
        IpV4 network if `ip_addr` is a member, else None

    """
    if not _NET_DICT:
        print("Please wait. Getting VPS data...", end="")
        _build_vps_dict()
        print("done")
    ip_pref = _get_prefix(ip_addr)
    ip4_addr = ip_address(ip_addr)
    if not isinstance(ip4_addr, IPv4Address):
        return None
    if ip_pref in _NET_DICT:
        for net in _NET_DICT[ip_pref]:
            if ip_addr in net:
                return net
    return None
