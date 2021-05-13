Notebooklet Class - HostLogonsSummary
=====================================

Host Logons Summary Notebooket class.

Queries and displays information about logons to a host including:

-  Summary of sucessfull logons

-  Visualizations of logon event times

-  Geolocation of remote logon sources

-  Visualizations of various logon elements depending on host type

-  Data on users with failed and sucessful logons

--------------

Display Sections
----------------

--------------

Results Class
-------------

HostLogonsSummaryResult
~~~~~~~~~~~~~~~~~~~~~~~

Host Logons Summary Results.

Attributes
~~~~~~~~~~

-  | logon_sessions: pd.DataFrame
   | A Dataframe summarizing all sucessfull and failed logon attempts
     observed during the specified time period.

-  |

-  | logon_map: FoliumMap
   | A map showing remote logon attempt source locations. Red points
     represent failed logons, green successful.

-  |

-  | plots: Dict
   | A collection of Bokeh plot figures showing various aspects of
     observed logons. Keys are a descriptive name of the plot and values
     are the plot figures.

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
  \**kwargs) ->
  msticnb.nb.azsent.host.host_logons_summary.HostLogonsSummaryResult
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
    Optionally pass raw data to use for analysis, by default None

timespan : TimeSpan
    Timespan over which operations such as queries will be
    performed, by default None.
    This can be a TimeStamp object or another object that
    has valid `start`, `end`, or `period` attributes.
    Alternatively you can pass `start` and `end` datetime objects.

options : Optional[Iterable[str]], optional
    List of options to use, by default None
    A value of None means use default options.


Returns
~~~~~~~


HostLogonsSummaryResults
    Result object with attributes for each result type.


Raises
~~~~~~


MsticnbMissingParameterError
    If required parameters are missing


MsticnbDataProviderError
    If data is not avaliable



Default Options
~~~~~~~~~~~~~~~

- map: Display a map of logon attempt locations.
- timeline: Display a timeline of logon atttempts.
- charts: Display a range of charts depicting different elements of logon events.
- failed_success: Displays a DataFrame of all users with both successful and failed logons.


Other Options
~~~~~~~~~~~~~


None