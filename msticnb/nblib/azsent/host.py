# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""host_network_summary notebooklet."""
from functools import lru_cache
from typing import Optional, Tuple, Dict

from msticpy.data import QueryProvider
from msticpy.nbtools import entities
from msticpy.sectools.ip_utils import populate_host_entity, convert_to_ip_entities

from ...common import TimeSpan, print_data_wait

from ..._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


@lru_cache()
def get_heartbeat(
    qry_prov: QueryProvider, host_name: str = None, host_ip: str = None
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
        print_data_wait("Heartbeat")
        host_hb_df = None
        if host_name:
            host_hb_df = qry_prov.Network.get_heartbeat_for_host(host_name=host_name)
        elif host_ip:
            host_hb_df = qry_prov.Network.get_heartbeat_for_ip(ip_address=host_ip)
        if host_hb_df is not None and not host_hb_df.empty:
            host_entity = populate_host_entity(heartbeat_df=host_hb_df)

    return host_entity


# %%
# Get IP Information from Azure Network Topology
@lru_cache()
def get_aznet_topology(
    qry_prov: QueryProvider,
    host_entity: entities.Host,
    host_name: str = None,
    host_ip: str = None,
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
    if "AzureNetworkAnalytics_CL" in qry_prov.schema_tables:
        print_data_wait("AzureNetworkAnalytics")
        if host_name:
            az_net_df = qry_prov.Network.get_ips_for_host(host_name=host_name)
        elif host_ip:
            az_net_df = qry_prov.Network.host_for_ip(ip_address=host_ip)

        if not az_net_df.empty:
            host_entity.private_ips = convert_to_ip_entities(
                az_net_df["PrivateIPAddresses"].iloc[0]
            )
            host_entity.public_ips = convert_to_ip_entities(
                az_net_df["PublicIPAddresses"].iloc[0]
            )

        else:
            if "private_ips" not in host_entity:
                host_entity.private_ips = []
            if "public_ips" not in host_entity:
                host_entity.public_ips = []


@lru_cache()
def verify_host_name(
    qry_prov: QueryProvider, timespan: TimeSpan, host_name: str
) -> Tuple[Optional[Tuple(str,str)], Optional[Dict[str:str]]]:
    """
    Verifies unique hostname by checking Win and Linux logs.

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
    Tuple[Optional[Tuple(str,str)], Optional[Dict[str:str]]]
        (host_name, host_names)
        If unique hostname found, host_name is populated.
        If multiple matching hostnames found, host_names is
        populated and host_name is None.
        If no matching host then both are None.

    """
    host_names: Dict = {}
    # Check for Windows hosts matching host_name
    if "SecurityEvent" in qry_prov.schema_tables:
        sec_event_host = """
            SecurityEvent
            | where TimeGenerated between (datetime({timespan.start})..datetime({timespan.end})
            | where Computer has {host_name}
            | distinct Computer
             """
        win_hosts_df = qry_prov.exec_query(
            sec_event_host.format(
                start=timespan.start, end=timespan.end, host=host_name
            )
        )
        if win_hosts_df is not None and not win_hosts_df.empty:
            for host in win_hosts_df["Computer"].to_list():
                host_names.update({host: "Windows"})

    # Check for Linux hosts matching host_name
    if "Syslog" in qry_prov.schema_tables:
        syslog_host = """
            Syslog
            | where TimeGenerated between (datetime({timespan.start})..datetime({timespan.end})
            | where Computer has {host_name}
            | distinct Computer
            """
        lx_hosts_df = qry_prov.exec_query(
            syslog_host.format(start=timespan.start, end=timespan.end, host=host_name)
        )
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
        return None, host_names

    if host_names:
        unique_host = next(iter(host_names))
        print(f"Unique host found: {unique_host}")
        return (unique_host, host_names[unique_host]), None

    print(f"Host not found: {host_name}")
    return None, None
