# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""host_network_summary notebooklet."""
from collections import namedtuple
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set

import pandas as pd
from msticpy.common.timespan import TimeSpan
from msticpy.data import QueryProvider  # pylint: disable=no-name-in-module
from msticpy.datamodel import entities

from ..._version import VERSION
from ...common import MsticnbMissingParameterError, df_has_data, nb_data_wait, nb_print
from ..iptools import convert_to_ip_entities

__version__ = VERSION
__author__ = "Ian Hellen"


@lru_cache()
def get_heartbeat(
    qry_prov: QueryProvider,
    host_name: Optional[str] = None,
    host_ip: Optional[str] = None,
) -> entities.Host:
    """
    Get Heartbeat information for host or IP.

    Parameters
    ----------
    qry_prov : QueryProvider
        Query provider to use for queries
    host_name : str, optional
        Host name, by default None
    host_ip : str, optional
        Host IP Address, by default None

    Returns
    -------
    Host
        Host entity

    """
    host_entity = entities.Host(HostName=host_name)
    if "Heartbeat" in qry_prov.schema_tables:
        nb_data_wait("Heartbeat")
        host_hb_df = None
        if host_name:
            host_hb_df = qry_prov.Network.get_heartbeat_for_host(host_name=host_name)
        elif host_ip:
            host_hb_df = qry_prov.Network.get_heartbeat_for_ip(ip_address=host_ip)
        if df_has_data(host_hb_df):
            host_entity = populate_host_entity(heartbeat_df=host_hb_df)

    return host_entity


# %%
# Get IP Information from Azure Network Topology
# pylint: disable=too-many-branches
@lru_cache()
def get_aznet_topology(
    qry_prov: QueryProvider,
    host_entity: entities.Host,
    host_name: Optional[str] = None,
    host_ip: Optional[str] = None,
):
    """
    Get Azure Network topology information for host or IP address.

    Parameters
    ----------
    qry_prov : QueryProvider
        Query provider to use for queries
    host_entity : Host
        Host entity to populate data with
    host_name : str, optional
        Host name, by default None
    host_ip : str, optional
        Host IP Address, by default None

    """
    if "AzureNetworkAnalytics_CL" not in qry_prov.schema_tables:
        return None
    nb_data_wait("AzureNetworkAnalytics")
    az_net_df = None
    if host_name:
        az_net_df = qry_prov.Network.get_ips_for_host(host_name=host_name)
    elif host_ip:
        az_net_df = qry_prov.Network.host_for_ip(ip_address=host_ip)

    if df_has_data(az_net_df):
        host_entity = populate_host_entity(az_net_df=az_net_df, host_entity=host_entity)
    return host_entity


HostNameVerif = namedtuple("HostNameVerif", "host_name, host_type, host_names")


@lru_cache()  # noqa:MC0001
def verify_host_name(  # noqa: MC0001, C901
    qry_prov: QueryProvider, host_name: str, timespan: TimeSpan = None, **kwargs
) -> HostNameVerif:
    """
    Verify unique hostname by checking Win and Linux logs.

    Parameters
    ----------
    qry_prov : QueryProvider
        Kql query provider
    timespan : TimeSpan
        Time span over which to query
    host_name : str
        The full or partial hostname.

    Returns
    -------
    HostNameVerif
        Tuple[Optional[str], Optional[str], Optional[Dict[str, str]]]
        Named tuple HostNameVerif
        fields: host_name, host_type, host_names
        If unique hostname found, host_name is populated.
        If multiple matching hostnames found, host_names is
        populated and host_name is None.
        host_type is either Windows or Linux.
        If no matching host then all fields are None.

    """
    # Check if a time span is provide as TimeSpan object or start and end parameters
    if timespan is None and ("start" in kwargs and "end" in kwargs):
        start = kwargs["start"]
        end = kwargs["end"]
    elif timespan is not None:
        start = timespan.start
        end = timespan.end
    else:
        raise MsticnbMissingParameterError("timespan")
    host_names: Dict = {}
    # Check for Windows hosts matching host_name
    if "SecurityEvent" in qry_prov.schema_tables:
        sec_event_host = f"""
            SecurityEvent
            | where TimeGenerated between (datetime({start})..datetime({end}))
            | where Computer has "{host_name}"
            | distinct Computer
             """
        nb_data_wait("SecurityEvent")

        win_hosts_df = qry_prov.exec_query(sec_event_host)
        if win_hosts_df is not None and not win_hosts_df.empty:
            for host in win_hosts_df["Computer"].to_list():
                host_names.update({host: "Windows"})

    # Check for Linux hosts matching host_name
    if "Syslog" in qry_prov.schema_tables:
        syslog_host = f"""
            Syslog
            | where TimeGenerated between (datetime({start})..datetime({end}))
            | where Computer has "{host_name}"
            | distinct Computer
            """
        nb_data_wait("Syslog")

        lx_hosts_df = qry_prov.exec_query(syslog_host)

        if lx_hosts_df is not None and not lx_hosts_df.empty:
            for host in lx_hosts_df["Computer"].to_list():
                host_names.update({host: "Linux"})

    # If we have more than one host let the user decide
    if len(host_names.keys()) > 1:
        print(
            f"Multiple matches for '{host_name}'.",
            "Please select a host and re-run.",
            "\n".join(host_names.keys()),
        )
        return HostNameVerif(None, None, host_names)

    if host_names:
        unique_host = next(iter(host_names))
        nb_print(f"Unique host found: {unique_host}")
        return HostNameVerif(unique_host, host_names[unique_host], None)

    nb_print(f"Host not found: {host_name}")
    return HostNameVerif(None, None, None)


# %%
# Populate or create a host entity from Heartbeat and Azure Topology information
def populate_host_entity(
    heartbeat_df: pd.DataFrame = None,
    az_net_df: pd.DataFrame = None,
    vmcomputer_df: pd.DataFrame = None,
    host_entity: entities.Host = None,
    geo_lookup: Any = None,
) -> entities.Host:
    """
    Populate host with IP and other data.

    Parameters
    ----------
    heartbeat_df : pd.DataFrame
        Optional dataframe of heartbeat data for the host
    az_net_df : pd.DataFrame
        Optional dataframe of Azure network data for the host
    vmcomputer_df : pd.DataFrame
        Optional dataframe of VMComputer data for the host
    host_entity : Host
        Host entity in which to populate data. By default,
        a new host entity will be created.
    geo_lookup : Any
        GeoIP Provider to use, if needed.

    Returns
    -------
    Host
        How with details of the IP data collected

    """
    if host_entity is None:
        host_entity = entities.Host()

    ip_entities: List[entities.IpAddress] = []
    ip_unique: Set[str] = set()
    # Extract data from available dataframes
    if df_has_data(heartbeat_df):
        ip_hb = heartbeat_df.iloc[0]  # type: ignore
        ip_entity = _extract_heartbeat(ip_hb, host_entity)
        ip_entities.append(ip_entity)
        ip_unique.add(ip_entity.Address)

    if df_has_data(vmcomputer_df):
        ip_vm = vmcomputer_df.iloc[0]  # type: ignore
        _extract_vmcomputer(ip_vm, host_entity)
        ip_ents = convert_to_ip_entities(
            data=vmcomputer_df, ip_col="Ipv4Addresses", geo_lookup=geo_lookup
        )
        ip_entities.extend(
            ip_ent for ip_ent in ip_ents if ip_ent.Address not in ip_unique
        )
        ip_unique |= {ip_ent.Address for ip_ent in ip_ents}
        ip_ents = convert_to_ip_entities(
            data=vmcomputer_df, ip_col="Ipv6Addresses", geo_lookup=geo_lookup
        )
        ip_entities.extend(
            ip_ent for ip_ent in ip_ents if ip_ent.Address not in ip_unique
        )
        ip_unique |= {ip_ent.Address for ip_ent in ip_ents}

    # If Azure network data present add this to host record
    if df_has_data(az_net_df):
        if not host_entity.HostName:
            host_entity.HostName = az_net_df.iloc[0].Computer  # type: ignore
        ip_priv = convert_to_ip_entities(
            data=az_net_df, ip_col="PrivateIPAddresses", geo_lookup=geo_lookup
        )
        ip_pub = convert_to_ip_entities(
            data=az_net_df, ip_col="PublicIPAddresses", geo_lookup=geo_lookup
        )
        host_entity["PrivateIpAddresses"] = []
        host_entity["PrivateIpAddresses"].extend(
            ip_ent for ip_ent in ip_priv if ip_ent.Address not in ip_unique
        )
        host_entity["PublicIpAddresses"] = []
        host_entity["PublicIpAddresses"].extend(
            ip_ent for ip_ent in ip_pub if ip_ent.Address not in ip_unique
        )
        ip_entities.extend(host_entity["PrivateIpAddresses"])
        ip_entities.extend(host_entity["PublicIpAddresses"])

    host_entity["IpAddresses"] = ip_entities
    if not hasattr(host_entity, "IpAddress") and len(ip_entities) == 1:
        host_entity["IpAddress"] = ip_entities[0]

    return host_entity


def _extract_heartbeat(ip_hb, host_entity):
    if not host_entity.HostName:
        host_entity.HostName = ip_hb["Computer"]  # type: ignore
    host_entity.SourceComputerId = ip_hb["SourceComputerId"]  # type: ignore
    host_entity.OSFamily = (
        entities.OSFamily.Windows
        if ip_hb["OSType"] == "Windows"
        else entities.OSFamily.Linux
    )
    host_entity.OSName = ip_hb["OSName"]  # type: ignore
    host_entity.OSVMajorVersion = ip_hb["OSMajorVersion"]  # type: ignore
    host_entity.OSVMinorVersion = ip_hb["OSMinorVersion"]  # type: ignore
    host_entity.Environment = ip_hb["ComputerEnvironment"]  # type: ignore
    host_entity.AgentId = ip_hb["SourceComputerId"]
    host_entity.OmsSolutions = [  # type: ignore
        sol.strip() for sol in ip_hb["Solutions"].split(",")
    ]
    host_entity.VMUUID = ip_hb["VMUUID"]  # type: ignore
    if host_entity.Environment == "Azure":
        host_entity.AzureDetails = {  # type: ignore
            "SubscriptionId": ip_hb["SubscriptionId"],
            "ResourceProvider": ip_hb["ResourceProvider"],
            "ResourceType": ip_hb["ResourceType"],
            "ResourceGroup": ip_hb["ResourceGroup"],
            "ResourceId": ip_hb["ResourceId"],
        }

    # Populate IP data
    ip_entity = entities.IpAddress(Address=ip_hb["ComputerIP"])
    geoloc_entity = entities.GeoLocation()  # type: ignore
    geoloc_entity.CountryName = ip_hb["RemoteIPCountry"]  # type: ignore
    geoloc_entity.Longitude = ip_hb["RemoteIPLongitude"]  # type: ignore
    geoloc_entity.Latitude = ip_hb["RemoteIPLatitude"]  # type: ignore
    ip_entity.Location = geoloc_entity  # type: ignore
    host_entity.IpAddress = ip_entity  # type: ignore
    return ip_entity


def _extract_vmcomputer(ip_vm, host_entity):
    if not host_entity.HostName:
        host_entity.HostName = ip_vm["Computer"]  # type: ignore
    host_entity.OSFamily = (
        entities.OSFamily.Windows
        if ip_vm["OperatingSystemFamily"].casefold() == "windows"
        else entities.OSFamily.Linux
    )
    host_entity.OSName = ip_vm["OperatingSystemFullName"]  # type: ignore
    host_entity.Environment = "Azure"  # type: ignore
    host_entity.AgentId = ip_vm["AgentId"]
    host_entity.VMUUID = ip_vm["AzureVmId"]  # type: ignore
    if host_entity.Environment == "Azure":
        host_entity.AzureDetails = {  # type: ignore
            "SubscriptionId": ip_vm["AzureSubscriptionId"],
            "ResourceProvider": ip_vm["HostingProvider"],
            "ResourceType": ip_vm["VirtualMachineType"],
            "ResourceGroup": ip_vm["AzureResourceGroup"],
            "ResourceId": ip_vm["_ResourceId"],
        }
