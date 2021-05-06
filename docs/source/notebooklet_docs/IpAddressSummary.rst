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

-  heartbeat: Get the latest heartbeat record for for this IP Address.

-  az_net_if: Get the latest Azure network analytics interface data for
   this IP Address.

-  vmcomputer: Get the latest VMComputer record for this IP Address.

**Other Options**

-  bookmarks: Get any hunting bookmarks listing the IP address.

-  az_netflow: Get netflow information from AzureNetworkAnalytics table.

-  passive_dns: Force fetching passive DNS data from a TI Provider even
   if IP is internal.

-  az_activity: AAD sign-ins and Azure Activity logs

-  office_365: Office 365 activity

-  ti: Force get threat intelligence reports even for internal public
   IPs.

--------------

Display Sections
----------------

Azure Sign-ins and audit activity from IP Address
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(only available for Azure)

Azure network analytics netflow data for IP.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

Azure Sentinel alerts related to the IP.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``nblt.browse_alerts()`` to retrieve a list of alerts.

.. _azure-sentinel-alerts-related-to-the-ip.-1:

Azure Sentinel alerts related to the IP.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``nblt.browse_alerts()`` to retrieve a list of alerts.

IP Address summary
~~~~~~~~~~~~~~~~~~

Retrieving data for IP Address Data and plots are stored in the result
class returned by this function.

Azure Network Analytics Topology record for the IP.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(only available for Azure VMs)

Azure Sentinel heartbeat record for the IP.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(only available for IP addresses that belong to the subscription)

Azure VMComputer record for the IP.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(only available for Azure VMs)

Summary of network flow data for this IP Address
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

-  | host_entity : Host
   | Host entity associated with IP Address

-  | ip_type : str
   | IP address type - "Public", "Private", etc.

-  | vps_network : IPv4Network
   | If this is not None, the address is part of a know VPS network.

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
   | Azure Network analytics interface record, if available

-  | vmcomputer : pd.DataFrame
   | VMComputer latest record

-  | az_network_flows : pd.DataFrame
   | Azure Network analytics flows for IP, if available

-  | az_network_flows_timeline: Figure
   | Azure Network analytics flows timeline, if data is available

-  | aad_signins : pd.DataFrame = None
   | AAD signin activity

-  | azure_activity : pd.DataFrame = None
   | Azure Activity log entries

-  | azure_activity_summary : pd.DataFrame = None
   | Azure Activity (AAD and Az Activity) summarized view

-  | office_activity : pd.DataFrame = None
   | Office 365 activity

-  | related_alerts : pd.DataFrame
   | Alerts related to IP Address

-  | related_bookmarks : pd.DataFrame
   | Bookmarks related to IP Address

-  | alert_timeline : Figure
   | Timeline plot of alerts

-  | ti_results: pd.DataFrame
   | Threat intel lookup results

-  | passive_dns: pd.DataFrame
   | Passive DNS lookup results

--------------

Methods
-------

Instance Methods
~~~~~~~~~~~~~~~~

\__init_\_
^^^^^^^^^^

| \__init__(self, data_providers:
  Union[<msticnb.data_providers.SingletonDecorator object at
  0x00000130B3F78788>, NoneType] = None, \**kwargs)
| Intialize a new instance of the notebooklet class.

browse_alerts
^^^^^^^^^^^^^

| browse_alerts(self) -> msticpy.nbtools.nbwidgets.SelectAlert
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

| run(self, value: Any = None, data: Union[pandas.core.frame.DataFrame,
  NoneType] = None, timespan: Union[msticpy.common.timespan.TimeSpan,
  NoneType] = None, options: Union[Iterable[str], NoneType] = None,
  \**kwargs) -> msticnb.nb.azsent.network.ip_summary.IpSummaryResult
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

Other Methods
~~~~~~~~~~~~~

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

| get_settings(print_settings=True) -> Union[str, NoneType]
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

---------

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
- heartbeat: Get the latest heartbeat record for for this IP Address.
- az_net_if: Get the latest Azure network analytics interface data for this IP Address.
- vmcomputer: Get the latest VMComputer record for this IP Address.


Other Options
~~~~~~~~~~~~~

- bookmarks: Get any hunting bookmarks listing the IP address.
- az_netflow: Get netflow information from AzureNetworkAnalytics table.
- passive_dns: Force fetching passive DNS data from a TI Provider even if IP is internal.
- az_activity: AAD sign-ins and Azure Activity logs
- office_365: Office 365 activity
- ti: Force get threat intelligence reports even for internal public IPs.