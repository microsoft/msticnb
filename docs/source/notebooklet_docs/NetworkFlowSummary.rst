Notebooklet Class - NetworkFlowSummary
======================================

Network Flow Summary Notebooklet class.

Queries network data and plots time lines for network

traffic to/from a host or IP address.

-  Plot flows events by protocol and direction

-  Plot flow count by protocol

-  Display flow summary table

-  Display flow summary by ASN

-  Display results on map

**Methods**

-  run: main method for notebooklet.

-  select_asns: Open an interactive dialog to choose which ASNs to

investigate further.

-  lookup_ti_for_asn_ips: For selected ASNs, lookup Threat Intelligence

data for the IPs belonging to those ASNs.

-  show_selected_asn_map: Show IP address locations for selected IP

(including any threats highlighted)

**Default Options**

-  plot_flows: Create plots of flows by protocol and direction.

-  plot_flow_values: Plot flow county by protocol.

-  flow_summary: Create a summarization of all flows and all flows
   grouped by ASN.

-  resolve_host: Try to resolve the host name before other operations.

**Other Options**

-  geo_map: Plot a map of all IP address locations in communication with
   the host (see the method below for plotting selected IPs only).

--------------

Display Sections
----------------

Host Network Summary
~~~~~~~~~~~~~~~~~~~~

This shows a summary of network flows for this endpoint. Data and plots
are stored in the result class returned by this function.

Map of geographic location of selected IPs communicating with host
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Numbered circles indicate multiple items - click to expand these.
Hovering over a location shows brief details, clicking on an IP location
shows more detail. Location marker key - Blue = outbound - Purple =
inbound - Green = Host - Red = Threats

Map of geographic location of all IPs communicating with host
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Numbered circles indicate multiple items - click to expand these.
Hovering over a location shows brief details, clicking on an IP location
shows more detail. Location marker key - Blue = outbound - Purple =
inbound - Green = Host

Flow Index.
^^^^^^^^^^^

List of flows grouped by source, dest, protocol and direction.

Flow Summary with ASN details.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Gets the ASN details from WhoIs. The data shows flows grouped by source
and destination ASNs. All protocol types and all source IP addresses are
grouped into lists for each ASN.

TI Lookup for IP Addresses in selected ASNs.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The remote IPs from each selected ASN are are searched for your selected
Threat Intelligence providers. Check the results to see if there are
indications of malicious activity associated with these IPs.

Timeline of network flows quantity.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each protocol is plotted as a separate colored series. The vertical axis
indicates the number for flows recorded for that time slot.

Timeline of network flows by direction.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

I = inbound, O = outbound.

Timeline of network flows by protocol type.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Select the ASNs to process.
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Choose any unusual looking ASNs that you want to examine. The remote IPs
from each selected ASN will be sent to your selected Threat Intelligence
providers to check if there are indications of malicious activity
associated with these IPs. By default, the most infrequently accessed
ASNs are selected.

--------------

Results Class
-------------

NetworkFlowResult
~~~~~~~~~~~~~~~~~

Network Flow Details Results.

Attributes
~~~~~~~~~~

-  | host_entity : msticpy.datamodel.entities.Host
   | The host entity object contains data about the host such as name,
     environment, operating system version, IP addresses and Azure VM
     details. Depending on the type of host, not all of this data may be
     populated.

-  | network_flows : pd.DataFrame
   | The raw network flows recorded for this host.

-  | plot_flows_by_protocol : Figure
   | Bokeh timeline plot of flow events by protocol.

-  | plot_flows_by_direction : Figure
   | Bokeh timeline plot of flow events by direction (in/out).

-  | plot_flow_values : Figure
   | Bokeh values plot of flow events by protocol.

-  | flow_index : pd.DataFrame
   | Summarized DataFrame of flows

-  | flow_index_data : pd.DataFrame
   | Raw summary data of flows.

-  | flow_summary : pd.DataFrame
   | Summarized flows grouped by ASN

-  | ti_results : pd.DataFrame
   | Threat Intelligence results for selected IP Addreses.

-  | geo_map : foliummap.FoliumMap
   | Folium map showing locations of all IP Addresses.

-  | geo_map_selected : foliummap.FoliumMap
   | Folium map showing locations of selected IP Addresses.

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
| Intialize a new instance of the notebooklet class.

lookup_ti_for_asn_ips
^^^^^^^^^^^^^^^^^^^^^

| lookup_ti_for_asn_ips(self)
| Lookup Threat Intel data for IPs of selected ASNs.

run
^^^

| run(self, value: Any = None, data:
  Optional[pandas.core.frame.DataFrame] = None, timespan:
  Optional[msticpy.common.timespan.TimeSpan] = None, options:
  Optional[Iterable[str]] = None, \**kwargs) ->
  msticnb.nb.azsent.network.network_flow_summary.NetworkFlowResult
| Return host summary data.

select_asns
^^^^^^^^^^^

| select_asns(self)
| Show interactive selector to choose which ASNs to process.

show_selected_asn_map
^^^^^^^^^^^^^^^^^^^^^

| show_selected_asn_map(self) -> msticpy.nbtools.foliummap.FoliumMap
| Display map of IP locations for selected ASNs.

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

Return host summary data.


Parameters
~~~~~~~~~~


value : str
    Host entity, hostname or host IP Address

data : Optional[pd.DataFrame], optional
    Not used, by default None

timespan : TimeSpan
    Timespan over which operations such as queries will be
    performed, by default None.
    This can be a TimeStamp object or another object that
    has valid `start`, `end`, or `period` attributes.

options : Optional[Iterable[str]], optional
    List of options to use, by default None
    A value of None means use default options.
    Options prefixed with "+" will be added to the default options.
    To see the list of available options type `help(cls)` where
    "cls" is the notebooklet class or an instance of this class.


Other Parameters
~~~~~~~~~~~~~~~~


start : Union[datetime, datelike-string]
    Alternative to specifying timespan parameter.

end : Union[datetime, datelike-string]
    Alternative to specifying timespan parameter.


Returns
~~~~~~~


HostNetworkResult
    Result object with attributes for each result type.


Raises
~~~~~~


MsticnbMissingParameterError
    If required parameters are missing



Default Options
~~~~~~~~~~~~~~~

- plot_flows: Create plots of flows by protocol and direction.
- plot_flow_values: Plot flow county by protocol.
- flow_summary: Create a summarization of all flows and all flows grouped by ASN.
- resolve_host: Try to resolve the host name before other operations.


Other Options
~~~~~~~~~~~~~

- geo_map: Plot a map of all IP address locations in communication with the host (see the method below for plotting selected IPs only).