Notebooklet Class - URLSummary
===============================

URLSummary Notebooklet class.

Queries and displays information about a URL including:

-  Domain and IP Whois Information

-  Threat Intelligence Results

-  TLS Certificates used the Domain

- Data about where URL appears in the environment.

**Default Options**

-  ti: Displays TI results for the URL.

-  whois: Display a summary of the URL.

-  ip_record: Display a summary of the IP address the URL resolves to.

-  cert: Display a summary of TLS certs used by the URL.

-  alerts: Displays a DataFrame of all alerts associated with the URL.

-  bookmarks: Displays a DataFrame of all bookmarks associated with the URL.

-  dns: Displays a DataFrame of all DNS events associated with the URL.

-  hosts: Displays a DataFrame of all hosts associated with the URL.


**Other Options**

- screenshot: Capture and display a screenshot of the URL.

--------------

Display Sections
----------------

URL Summary
~~~~~~~~~~~~~~~~~~~

This shows an overview of the URL in question including a large number of contextual items.
It will show overview of WhoIs information related to the URL, Threat Intelligence provider results
for the URL, and details of TLS certificates associated with the URL.
In addition this section will show a selection of data from an environment where the URL is present
including DNS lookup events, alerts and bookmarks referencing the URL, and network traffic to the URL.

Timeline of related alerts
^^^^^^^^^^^^^^^^^^^^^^^^^^

Each marker on the timeline indicates one or more alerts related to the
URL.

--------------

Results Class
-------------

URLSummaryResult
~~~~~~~~~~~~~~~~~

URL Details Results.

Attributes
~~~~~~~~~~

-  | summary : msticpy.datamodel.entities.Host
   | A summary of the URL provided.

-  | domain_record : pd.DataFrame
   | WhoIs data related to the domain.

-  | cert_details: pd.DataFrame
   | Details of TLS certificates used (if any).

-  | ip_record: pd.DataFrame
   | Details of the IP Address associated with the URL.

-  | related_alerts: pd.DataFrame
   | Any alerts referencing the URL.

-  | bookmarks: pd.DataFrame
   | Any bookmarks referencing the URL.

-  | hosts: List
   | A list of host names seen communicating with the URL.

-  | flows: pd.DataFrame
   | Details of network flows associated with the URL.

-  | flow_graph: LayoutDOM
   | A timeline plot showing network traffic volumes to the URL.

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

run
^^^

| run(self, value: Any = None, data:
  Optional[pandas.core.frame.DataFrame] = None, timespan:
  Optional[msticpy.common.timespan.TimeSpan] = None, options:
  Optional[Iterable[str]] = None, \**kwargs) ->
  msticnb.nb.azsent.host.host_summary.HostSummaryResult
| Return host summary data.

display_alert_timeline
^^^^^^^^^^^^^^^^^^^^^^
| display_alert_timeline(self)
| Display the alert timeline.


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

Return URL summary data.


Parameters
~~~~~~~~~~


value : str
    The URL

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

- ti: Displays TI results for the URL
- whois: Display a summary of the URL
- ip_record: Display a summary of the IP address the URL resolves to
- cert: Display a summary of TLS certs used by the URL.
- alerts: Displays a DataFrame of all alerts associated with the URL
- bookmarks: Displays a DataFrame of all bookmarks associated with the URL
- dns: Displays a DataFrame of all DNS events associated with the URL
- hosts: Displays a DataFrame of all hosts associated with the URL


Other Options
~~~~~~~~~~~~~


None