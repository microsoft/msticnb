# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""IP Helper functions."""
import pandas as pd

from msticpy.sectools.ip_utils import get_whois_df

from ..common import nb_markdown
from .._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


def get_ip_ti(ti_lookup: "TILookup", data: pd.DataFrame, ip_col: str) -> pd.DataFrame:
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


def get_geoip_whois(geo_lookup: "GeoIpLookup", data: pd.DataFrame, ip_col: str):
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
