Notebooklet Class - IpAddressSummary
====================================

IP Address Summary Notebooklet class.

Queries and displays summary information about an IP address, including:

-  Basic IP address properties

-  IpAddress entity (and Host entity, if a host could be associated)

-  WhoIs and Geo-location

-  Azure activity and network data (optional)

-  Office activity summary (optional)

-  Threat intelligence reports

-  Related alerts and hunting bookmarks

**Default Options**

-  geoip: Get geo location information for IP address.

-  alerts: Get any alerts listing the IP address.

-  host_logons: Find any hosts with logons using this IP address as a
   source.

-  related_accounts: Find any accounts using this IP address in AAD or
   host logs.

-  device_info: Find any devices associated with this IP address.

-  device_network: Find any devices communicating with this IP address.

**Other Options**

-  bookmarks: Get any hunting bookmarks listing the IP address.

-  heartbeat: Get the latest heartbeat record for for this IP address.

-  az_net_if: Get the latest Azure network analytics interface data for
   this IP address.

-  vmcomputer: Get the latest VMComputer record for this IP address.

-  az_netflow: Get netflow information from AzureNetworkAnalytics table.

-  passive_dns: Force fetching passive DNS data from a TI Provider even
   if IP is internal.

-  az_activity: AAD sign-ins and Azure Activity logs.

-  office_365: Office 365 activity.

-  common_security: Get records from common security log.

-  ti: Force get threat intelligence reports even for internal public
   IPs.

--------------

Display Sections
----------------

Azure Sign-ins and audit activity from IP Address
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(only available for Azure)

Azure Azure NSG Flow Logs for IP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(only available for if Azure network analytics net flow enabled.) This
is is a list of netflow events for the IP. Timeline by protocol is
available in the ``result.az_network_flows_timeline`` property - Use
``nblt.netflow_total_by_protocol()`` method to view flow totals by
protocol - Use ``nblt.netflow_total_by_direction()`` to view a timeline
grouped by direction of flow

Office 365 operations summary from IP Address
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(only available for Office 365)

Public IP data (GeoIP, ThreatIntel, Passive DNS, VPS membership)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Azure Sentinel alerts related to the IP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``nblt.browse_alerts()`` to retrieve a list of alerts.

.. _azure-sentinel-alerts-related-to-the-ip-1:

Azure Sentinel alerts related to the IP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``nblt.browse_alerts()`` to retrieve a list of alerts.

IP Address summary
~~~~~~~~~~~~~~~~~~

Retrieving data for IP Address Data and plots are stored in the result
class returned by this function.

Azure Network Analytics Topology record for the IP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(only available for Azure VMs)

Common security log
^^^^^^^^^^^^^^^^^^^

The CommonSecurityLog contains log data from firewalls and network
devices.

Defender device information
^^^^^^^^^^^^^^^^^^^^^^^^^^^

MS Defender device network and host information.

Network connections
^^^^^^^^^^^^^^^^^^^

MS Defender network connections to/from this IP address.

Azure Sentinel heartbeat record for the IP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(only available for IP addresses that belong to the subscription)

Host logons
^^^^^^^^^^^

List of hosts with logon attempts from this IP address.

Related accounts
^^^^^^^^^^^^^^^^

List of accounts using the IP address.

Azure VMComputer record for the IP.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(only available for Azure VMs)

Summary of Azure NSG network flow data for this IP Address
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(only available for if Azure network analytics net flow enabled.)

--------------

Results Class
-------------

IpSummaryResult
~~~~~~~~~~~~~~~

IPSummary Results.

Attributes
~~~~~~~~~~

-  | ip_str : str
   | The input IP address as a string.

-  | ip_address : Optional[Union[IPv4Address, IPv6Address]]
   | Ip Address Python object

-  | ip_entity : IpAddress
   | IpAddress entity

-  | ip_origin : str
   | "External" or "Internal"

-  | host_entities : Host
   | Host entity or entities associated with IP Address

-  | ip_type : str
   | IP address type - "Public", "Private", etc.

-  | geoip : Optional[Dict[str, Any]]
   | Geo location information as a dictionary.

-  | location : Optional[GeoLocation]
   | Location entity context object.

-  | whois : pd.DataFrame
   | WhoIs information for IP Address

-  | whois_nets : pd.DataFrame
   | List of networks definitions from WhoIs data

-  | heartbeat : pd.DataFrame
   | Heartbeat record for IP Address or host

-  | az_network_if : pd.DataFrame
   | Azure NSG analytics interface record, if available

-  | vmcomputer : pd.DataFrame
   | VMComputer latest record

-  | az_network_flows : pd.DataFrame
   | Azure NSG flows for IP, if available

-  | az_network_flows_timeline: Figure
   | Azure NSG flows timeline, if data is available

-  | aad_signins : pd.DataFrame = None
   | AAD signin activity

-  | azure_activity : pd.DataFrame = None
   | Azure Activity log entries

-  | azure_activity_summary : pd.DataFrame = None
   | Azure Activity (AAD and Az Activity) summarized view

-  | office_activity : pd.DataFrame = None
   | Office 365 activity

-  | common_security : pd.DataFrame
   | Common Security Log entries for source IP

-  | related_bookmarks : pd.DataFrame
   | Bookmarks related to IP Address

-  | alert_timeline : Figure
   | Timeline plot of alerts

-  | ti_results: pd.DataFrame
   | Threat intel lookup results

-  | passive_dns: pd.DataFrame
   | Passive DNS lookup results

-  | self.host_logons : pd.DataFrame
   | Hosts with logons from this IP Address

-  | self.related_accounts : pd.DataFrame
   | Accounts with activity related to this IP Address

-  | self.associated_hosts : pd.DataFrame
   | Hosts using this IP Address

-  | self.device_info : pd.DataFrame
   | Device info of hosts using this IP Address

-  | self.network_connections : pd.DataFrame = None
   | Network connections to/from this IP on other devices

--------------

Methods
-------

Instance Methods
~~~~~~~~~~~~~~~~

\__init_\_
^^^^^^^^^^

| \__init__(self, data_providers:
  Optional[<msticnb.data_providers.SingletonDecorator object at
  0x0000023FAFA3A6A0>] = None, \**kwargs)
| Initialize a new instance of the notebooklet class.

browse_alerts
^^^^^^^^^^^^^

| browse_alerts(self) ->
  msticpy.nbtools.nbwidgets.select_alert.SelectAlert
| Return alert browser/viewer.

browse_ti_results
^^^^^^^^^^^^^^^^^

| browse_ti_results(self)
| Display Threat intel results.

display_alert_timeline
^^^^^^^^^^^^^^^^^^^^^^

| display_alert_timeline(self)
| Display the alert timeline.

netflow_by_direction
^^^^^^^^^^^^^^^^^^^^

| netflow_by_direction(self) -> bokeh.plotting.figure.Figure
| Display netflows grouped by direction.

netflow_by_protocol
^^^^^^^^^^^^^^^^^^^

| netflow_by_protocol(self) -> bokeh.plotting.figure.Figure
| Display netflows grouped by protocol.

netflow_total_by_protocol
^^^^^^^^^^^^^^^^^^^^^^^^^

| netflow_total_by_protocol(self) -> bokeh.plotting.figure.Figure
| Display netflows grouped by protocol.

run
^^^

| run(self, value: Any = None, data:
  Optional[pandas.core.frame.DataFrame] = None, timespan:
  Optional[msticpy.common.timespan.TimeSpan] = None, options:
  Optional[Iterable[str]] = None, \**kwargs) ->
  msticnb.nb.azsent.network.ip_summary.IpSummaryResult
| Return IP Address activity summary.

Inherited methods
~~~~~~~~~~~~~~~~~

check_table_exists
^^^^^^^^^^^^^^^^^^

| check_table_exists(self, table: str) -> bool
| Check to see if the table exists in the provider.

check_valid_result_data
^^^^^^^^^^^^^^^^^^^^^^^

| check_valid_result_data(self, attrib: str = None, silent: bool =
  False) -> bool
| Check that the result is valid and ``attrib`` contains data.

get_methods
^^^^^^^^^^^

| get_methods(self) -> Dict[str, Callable[[Any], Any]]
| Return methods available for this class.

get_pivot_run
^^^^^^^^^^^^^

| get_pivot_run(self, get_timespan: Callable[[],
  msticpy.common.timespan.TimeSpan])
| Return Pivot-wrappable run function.

get_provider
^^^^^^^^^^^^

| get_provider(self, provider_name: str)
| Return data provider for the specified name.

list_methods
^^^^^^^^^^^^

| list_methods(self) -> List[str]
| Return list of methods with descriptions.

run_nb_func
^^^^^^^^^^^

| run_nb_func(self, nb_func: Union[str,
  msticnb.notebooklet_func.NBFunc], \**kwargs)
| Run the notebooklet function and return the results.

run_nb_funcs
^^^^^^^^^^^^

| run_nb_funcs(self)
| Run all notebooklet functions defined for the notebooklet.

Other Methods
~~~~~~~~~~~~~

add_nb_function
^^^^^^^^^^^^^^^

| add_nb_function(nb_func: Union[str, msticnb.notebooklet_func.NBFunc],
  \**kwargs)
| Add a notebooklet function to the class.

all_options
^^^^^^^^^^^

| all_options() -> List[str]
| Return supported options for Notebooklet run function.

default_options
^^^^^^^^^^^^^^^

| default_options() -> List[str]
| Return default options for Notebooklet run function.

description
^^^^^^^^^^^

| description() -> str
| Return description of the Notebooklet.

entity_types
^^^^^^^^^^^^

| entity_types() -> List[str]
| Entity types supported by the notebooklet.

get_help
^^^^^^^^

| get_help(fmt='html') -> str
| Return HTML document for class.

get_settings
^^^^^^^^^^^^

| get_settings(print_settings=True) -> Optional[str]
| Print or return metadata for class.

import_cell
^^^^^^^^^^^

| import_cell()
| Import the text of this module into a new cell.

keywords
^^^^^^^^

| keywords() -> List[str]
| Return search keywords for Notebooklet.

list_options
^^^^^^^^^^^^

| list_options() -> str
| Return options document for Notebooklet run function.

match_terms
^^^^^^^^^^^

| match_terms(search_terms: str) -> Tuple[bool, int]
| Search class definition for ``search_terms``.

name
^^^^

| name() -> str
| Return name of the Notebooklet.

print_options
^^^^^^^^^^^^^

| print_options()
| Print options for Notebooklet run function.

result
^^^^^^

result [property] Return result of the most recent notebooklet run.

show_help
^^^^^^^^^

| show_help()
| Display Documentation for class.

silent
^^^^^^

silent [property] Get the current instance setting for silent running.

<hr>

``run`` function documentation
------------------------------

Return IP Address activity summary.


Parameters
~~~~~~~~~~


value : str
    IP Address - The key for searches

data : Optional[pd.DataFrame], optional
    Not supported for this notebooklet.

timespan : TimeSpan
    Timespan for queries

options : Optional[Iterable[str]], optional
    List of options to use, by default None.
    A value of None means use default options.
    Options prefixed with "+" will be added to the default options.
    To see the list of available options type `help(cls)` where
    "cls" is the notebooklet class or an instance of this class.


Returns
~~~~~~~


IpSummaryResult
    Result object with attributes for each result type.


Raises
~~~~~~


MsticnbMissingParameterError
    If required parameters are missing



Default Options
~~~~~~~~~~~~~~~

- geoip: Get geo location information for IP address.
- alerts: Get any alerts listing the IP address.
- host_logons: Find any hosts with logons using this IP address as a source.
- related_accounts: Find any accounts using this IP address in AAD or host logs.
- device_info: Find any devices associated with this IP address.
- device_network: Find any devices communicating with this IP address.


Other Options
~~~~~~~~~~~~~

- bookmarks: Get any hunting bookmarks listing the IP address.
- heartbeat: Get the latest heartbeat record for for this IP address.
- az_net_if: Get the latest Azure network analytics interface data for this IP address.
- vmcomputer: Get the latest VMComputer record for this IP address.
- az_netflow: Get netflow information from AzureNetworkAnalytics table.
- passive_dns: Force fetching passive DNS data from a TI Provider even if IP is internal.
- az_activity: AAD sign-ins and Azure Activity logs.
- office_365: Office 365 activity.
- common_security: Get records from common security log.
- ti: Force get threat intelligence reports even for internal public IPs.