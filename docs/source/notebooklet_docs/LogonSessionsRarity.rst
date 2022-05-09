Notebooklet Class - LogonSessionsRarity
=======================================

Calculates the relative rarity of logon sessions.

It clusters the data based on process, command line and account.

Then calculates the rarity of the process pattern.

Then returns a result containing a summary of the logon sessions by
rarity.

To see the methods available for the class and result class, run

cls.list_methods()

**Default Options**

None

**Other Options**

None

--------------

Display Sections
----------------

Calculate process rarity statistics for logon sessions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This first transforms the input data into features suitable for a
clustering algorithm. It then clusters the data based on process,
command line and account and calculates the rarity of the process
pattern. It returns a result containing a summary of the logon sessions
along with full results of the clustering. Methods available to view
this data graphically include - list_sessions_by_rarity - table of
sessions ordered by degree of rarity - plot_sessions_by_rarity -
timeline plot of processes grouped by account and showing relative
rarity of each process. - process_tree - a process tree of all processes
or processes belonging to a single account.

--------------

Results Class
-------------

LogonSessionsRarityResult
~~~~~~~~~~~~~~~~~~~~~~~~~

Logon Sessions rarity.

Attributes
~~~~~~~~~~

-  | process_clusters : pd.DataFrame
   | Process clusters based on account, process, commandline and showing
     the an example process from each cluster

-  | processes_with_cluster : pd.DataFrame
   | Merged data with rarity value assigned to each process event.

-  | session_rarity: pd.DataFrame
   | List of sessions with averaged process rarity.

--------------

Methods
-------

Instance Methods
~~~~~~~~~~~~~~~~

\__init_\_
^^^^^^^^^^

| \__init__(self, \**kwargs)
| Initialize instance of LogonSessionRarity.

browse_events
^^^^^^^^^^^^^

| browse_events(self)
| Browse the events by logon session.

list_sessions_by_rarity
^^^^^^^^^^^^^^^^^^^^^^^

| list_sessions_by_rarity(self)
| Display sessions by process rarity.

plot_sessions_by_rarity
^^^^^^^^^^^^^^^^^^^^^^^

| plot_sessions_by_rarity(self)
| Display timeline plot of processes by rarity.

process_tree
^^^^^^^^^^^^

| process_tree(self, account: Optional[str] = None, session:
  Optional[str] = None)
| View a process tree of current session.

run
^^^

| run(self, value: Any = None, data:
  Optional[pandas.core.frame.DataFrame] = None, timespan:
  Optional[msticpy.common.timespan.TimeSpan] = None, options:
  Optional[Iterable[str]] = None, \**kwargs) ->
  msticnb.nb.azsent.host.logon_session_rarity.LogonSessionsRarityResult
| Calculate Logon sessions ordered by process rarity summary.

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

Calculate Logon sessions ordered by process rarity summary.


Parameters
~~~~~~~~~~


value : str
    Not used

data : Optional[pd.DataFrame], optional
    Process event data.

timespan : TimeSpan
    Not used

options : Optional[Iterable[str]], optional
    List of options to use, by default None.
    A value of None means use default options.
    Options prefixed with "+" will be added to the default options.
    To see the list of available options type `help(cls)` where
    "cls" is the notebooklet class or an instance of this class.


Returns
~~~~~~~


LogonSessionsRarityResult
    LogonSessionsRarityResult.


Raises
~~~~~~


MsticnbMissingParameterError
    If required parameters are missing



Default Options
~~~~~~~~~~~~~~~


None


Other Options
~~~~~~~~~~~~~


None