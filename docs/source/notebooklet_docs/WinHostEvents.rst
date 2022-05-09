Notebooklet Class - WinHostEvents
=================================

Windows host Security Events Notebooklet class.

Queries and displays Windows Security Events including:

-  All security events summary

-  Extracting and displaying account management events

-  Account management event timeline

-  Optionally parsing packed event data into DataFrame columns

Process (4688) and Account Logon (4624, 4625) are not included

in the event types processed by this module.

**Default Options**

-  event_pivot: Display a summary of all event types.

-  acct_events: Display a summary and timeline of account management
   events.

**Other Options**

-  expand_events: parses the XML EventData column into separate
   DataFrame columns. This can be very expensive with a large event set.
   We recommend using the expand_events() method to select a specific
   subset of events to process.

--------------

Display Sections
----------------

Host Security Events Summary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This shows a summary of security events for the host. These are grouped
by EventID and Account. Data and plots are stored in the result class
returned by this function.

Summary of Account Management Events on host
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This shows the subset of events related to account management, for
example, creation/deletion of accounts, changes to group membership,
etc. Yellow highlights indicate account with highest event count.

Timeline of Account Management Events on host
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Summary of Security Events on host
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is a summary of Security events for the host (excluding process
creation and account logon - 4688, 4624, 4625). Yellow highlights
indicate account with highest event count for an EventID.

Parsing eventdata into columns
''''''''''''''''''''''''''''''

This may take some time to complete for large numbers of events. Since
event types have different schema, some of the columns will not be
populated for certain Event IDs and will show as ``NaN``.

--------------

Results Class
-------------

WinHostEventsResult
~~~~~~~~~~~~~~~~~~~

Windows Host Security Events Results.

Attributes
~~~~~~~~~~

-  | all_events : pd.DataFrame
   | DataFrame of all raw events retrieved.

-  | event_pivot : pd.DataFrame
   | DataFrame that is a pivot table of event ID vs. Account

-  | account_events : pd.DataFrame
   | DataFrame containing a subset of account management events such as
     account and group modification.

-  | acct_pivot : pd.DataFrame
   | DataFrame that is a pivot table of event ID vs. Account of account
     management events

-  | account_timeline : Union[Figure, LayoutDOM]
   | Bokeh plot figure or Layout showing the account events on an
     interactive timeline.

-  | expanded_events : pd.DataFrame
   | If ``expand_events`` option is specified, this will contain the
     parsed/expanded EventData as individual columns.

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

expand_events
^^^^^^^^^^^^^

| expand_events(self, event_ids: Union[int, Iterable[int], NoneType] =
  None) -> pandas.core.frame.DataFrame
| Expand ``EventData`` for ``event_ids`` into separate columns.

run
^^^

| run(self, value: Any = None, data:
  Optional[pandas.core.frame.DataFrame] = None, timespan:
  Optional[msticpy.common.timespan.TimeSpan] = None, options:
  Optional[Iterable[str]] = None, \**kwargs) ->
  msticnb.nb.azsent.host.win_host_events.WinHostEventsResult
| Return Windows Security Event summary.

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

Return Windows Security Event summary.


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
    List of options to use, by default None.
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

- event_pivot: Display a summary of all event types.
- acct_events: Display a summary and timeline of account management events.


Other Options
~~~~~~~~~~~~~

- expand_events: parses the XML EventData column into separate DataFrame columns. This can be very expensive with a large event set. We recommend using the expand_events() method to select a specific subset of events to process.