# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""IP Helper functions."""
import re
from collections import defaultdict
from ipaddress import AddressValueError, IPv4Address, IPv4Network, ip_address
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import requests

from msticpy.datamodel.entities import IpAddress
from msticpy.nbtools.foliummap import FoliumMap
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
    ip4_match = data[ip_col].str.match(ip4_rgx).fillna(False)

    ipv4_df = data[ip4_match]
    other_df = data[~ip4_match]
    ipv4_df = (
        ipv4_df.assign(IP_ext=lambda x: x[ip_col].str.extract(ip4_rgx, expand=False))
        .rename(columns={ip_col: ip_col + "_orig"})
        .rename(columns={"IP_ext": ip_col})
    )
    return pd.concat([ipv4_df, other_df])


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


def map_ips(
    data: pd.DataFrame,
    ip_col: str,
    summary_cols: Optional[List[str]] = None,
    geo_lookup: Any = None,
) -> FoliumMap:
    """
    Produce a map of IP locations.

    Parameters
    ----------
    geo_lookup: Any
        Geo-IP provider instance
    data : pd.DataFrame
        Data containing the IPAddress
    ip_col : str
        [description]
    summary_cols : Optional[List[str]], optional
        [description], by default None
    geo_lookup : Any
        GeoIP Provider instance.

    Returns
    -------
    FoliumMap
        Folium map with items plotted.

    """
    data = _normalize_ip4(data, ip_col=ip_col)
    ip_ent_list = []
    for _, row in data.iterrows():
        if not isinstance(row[ip_col], str) or row[ip_col] in ("", "NaN", "-"):
            continue
        ip_ent_rslt = convert_to_ip_entities(row[ip_col], geo_lookup=geo_lookup)
        if summary_cols:
            for ip_ent in ip_ent_rslt:
                for col in summary_cols:
                    ip_ent.AdditionalData[col] = row[col]
        ip_ent_list.extend(ip_ent_rslt)

    # Get center point of logons and build map acount that
    folium_map = FoliumMap(zoom_start=4)
    folium_map.center_map()
    if ip_ent_list:
        icon_props = {"color": "green"}
        folium_map.add_ip_cluster(ip_entities=ip_ent_list, **icon_props)
    return folium_map


def convert_to_ip_entities(  # noqa: MC0001
    ip_str: Optional[str] = None,
    data: Optional[pd.DataFrame] = None,
    ip_col: Optional[str] = None,
    geo_lookup: Any = None,
) -> List[IpAddress]:
    """
    Take in an IP Address string and converts it to an IP Entity.

    Parameters
    ----------
    ip_str : str
        A string with a single IP Address or multiple addresses
        delimited by comma or space
    data : pd.DataFrame
        Use DataFrame as input
    ip_col : str
        Column containing IP addresses
    geo_lookup : bool
        If true, do geolocation lookup on IPs,
        by default, True

    Returns
    -------
    List
        The populated IP entities including address and geo-location

    Raises
    ------
    ValueError
        If neither ip_string or data/column provided as input

    """
    ip_entities: List[IpAddress] = []
    all_ips: Dict[str, IpAddress] = {}

    if ip_str:
        addrs = arg_to_list(ip_str)
    elif data is not None and ip_col:
        addrs = data[ip_col].values
    else:
        raise ValueError("Must specify either ip_str or data + ip_col parameters.")

    for addr in addrs:
        if isinstance(addr, list):
            ip_list = set(addr)
        elif isinstance(addr, str) and "," in addr:
            ip_list = {ip.strip() for ip in addr.split(",")}
        else:
            ip_list = {addr}

        for ip_addr in ip_list:
            if ip_addr in all_ips:
                ip_entities.append(all_ips[ip_addr])
                continue
            ip_entity = IpAddress(Address=ip_addr)

            if geo_lookup:
                try:
                    geo_lookup.lookup_ip(ip_entity=ip_entity)
                except Exception:  # pylint: disable=broad-except
                    pass
            ip_entities.append(ip_entity)
    return ip_entities


def arg_to_list(arg: Union[str, List[str]], delims=",; ") -> List[str]:
    """
    Convert an optional list/str/str with delims into a list.

    Parameters
    ----------
    arg : Union[str, List[str]]
        A string, delimited string or list
    delims : str, optional
        The default delimiters to use, by default ",; "

    Returns
    -------
    List[str]
        List of string components

    Raises
    ------
    TypeError
        If `arg` is not a string or list

    """
    if isinstance(arg, list):
        return arg
    if isinstance(arg, str):
        for char in delims:
            if char in arg:
                return [item.strip() for item in arg.split(char)]
        return [arg]
    raise TypeError("`arg` must be a string or a list.")
