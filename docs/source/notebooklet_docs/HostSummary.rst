Notebooklet Class - HostSummary
===============================

HostSummary Notebooklet class.

Queries and displays information about a host including:

-  IP address assignment

-  Related alerts

-  Related hunting/investigation bookmarks

-  Azure subscription/resource data.

**Default Options**

-  heartbeat: Query Heartbeat table for host information.

-  azure_net: Query AzureNetworkAnalytics table for host network
   topology information.

-  alerts: Query any alerts for the host.

-  bookmarks: Query any bookmarks for the host.

-  azure_api: Query Azure API for VM information.

**Other Options**

None

--------------

Display Sections
----------------

Host Entity Summary
~~~~~~~~~~~~~~~~~~~

This shows a summary data for a host. It shows host properties obtained
from OMS Heartbeat and Azure API. It also lists Azure Sentinel alerts
and bookmakrs related to to the host. Data and plots are stored in the
result class returned by this function.

Timeline of related alerts
^^^^^^^^^^^^^^^^^^^^^^^^^^

Each marker on the timeline indicates one or more alerts related to the
host.

Host Entity details
^^^^^^^^^^^^^^^^^^^

These are the host entity details gathered from Heartbeat and, if
applicable, AzureNetworkAnalytics and Azure management API. The data
shows OS information, IP Addresses assigned the host and any Azure VM
information available.

--------------

Results Class
-------------

HostSummaryResult
~~~~~~~~~~~~~~~~~

Host Details Results.

Attributes
~~~~~~~~~~

-  | host_entity : msticpy.data.nbtools.entities.Host
   | The host entity object contains data about the host such as name,
     environment, operating system version, IP addresses and Azure VM
     details. Depending on the type of host, not all of this data may be
     populated.

-  | related_alerts : pd.DataFrame
   | Pandas DataFrame of any alerts recorded for the host within the
     query time span.

-  | alert_timeline:
   | Bokeh time plot of alerts recorded for host.

-  | related_bookmarks: pd.DataFrame
   | Pandas DataFrame of any investigation bookmarks relating to the
     host.

--------------

Methods
-------

Instance Methods
~~~~~~~~~~~~~~~~

\__init_\_
^^^^^^^^^^

| \__init__(self, data_providers:
  Union[<msticnb.data_providers.SingletonDecorator object at
  0x000001270177A588>, NoneType] = None, \**kwargs)
| Intialize a new instance of the notebooklet class.

run
^^^

| run(self, value: Any = None, data: Union[pandas.core.frame.DataFrame,
  NoneType] = None, timespan: Union[msticpy.common.timespan.TimeSpan,
  NoneType] = None, options: Union[Iterable[str], NoneType] = None,
  \**kwargs) -> msticnb.nb.azsent.host.host_summary.HostSummaryResult
| Return host summary data.

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

Return host summary data.


Parameters
~~~~~~~~~~


value : str
    Host name

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


HostSummaryResult
    Result object with attributes for each result type.


Raises
~~~~~~


MsticnbMissingParameterError
    If required parameters are missing



Default Options
~~~~~~~~~~~~~~~

- heartbeat: Query Heartbeat table for host information.
- azure_net: Query AzureNetworkAnalytics table for host network topology information.
- alerts: Query any alerts for the host.
- bookmarks: Query any bookmarks for the host.
- azure_api: Query Azure API for VM information.


Other Options
~~~~~~~~~~~~~


None