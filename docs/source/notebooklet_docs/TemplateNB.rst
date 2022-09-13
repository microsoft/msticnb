Notebooklet Class - TemplateNB
==============================

Template Notebooklet class.

Detailed description of things this notebooklet does:

-  Fetches all events from XYZ

-  Plots interesting stuff

-  Returns extended metadata about the thing

Document the options that the Notebooklet takes, if any,

Use these control which parts of the notebooklet get run.

**Default Options**

-  all_events: Gets all events about blah

-  plot_events: Display and summary and timeline of events.

**Other Options**

-  get_metadata: fetches additional metadata about the entity

--------------

Display Sections
----------------

Title for the run method (main title)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Write your introductory text here Data and plots are stored in the
result class returned by this function. If you use **markdown** syntax
in this block add the following to use markdown processing.

Display the timeline.
^^^^^^^^^^^^^^^^^^^^^

This may take some time to complete for large numbers of events. It will
do: - Item one - Item two Since some groups will be undefined these can
show up as ``NaN``. Note: use a quoted string if you want to include
yaml reserved chars such as ":"

Do something else
'''''''''''''''''

This may take some time to complete for large numbers of events.

It will do: - Item one - Item two

--------------

Results Class
-------------

TemplateResult
~~~~~~~~~~~~~~

Template Results.

Attributes
~~~~~~~~~~

-  | all_events : pd.DataFrame
   | DataFrame of all raw events retrieved.

-  | plot : bokeh.models.LayoutDOM
   | Bokeh plot figure showing the account events on an interactive
     timeline.

-  | additional_info: dict
   | Additional information for my notebooklet.

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

run
^^^

| run(self, value: Any = None, data:
  Optional[pandas.core.frame.DataFrame] = None, timespan:
  Optional[msticpy.common.timespan.TimeSpan] = None, options:
  Optional[Iterable[str]] = None, \**kwargs) ->
  msticnb.nb.template.nb_template.TemplateResult
| Return XYZ summary.

run_additional_operation
^^^^^^^^^^^^^^^^^^^^^^^^

| run_additional_operation(self, event_ids: Union[int, Iterable[int],
  NoneType] = None) -> pandas.core.frame.DataFrame
| Addition method.

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

Return XYZ summary.


Parameters
~~~~~~~~~~


value : str
    Host name - The key for searches - e.g. host, account, IPaddress

data : Optional[pd.DataFrame], optional
    Alternatively use a DataFrame as input.

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


TemplateResult
    Result object with attributes for each result type.


Raises
~~~~~~


MsticnbMissingParameterError
    If required parameters are missing



Default Options
~~~~~~~~~~~~~~~

- all_events: Gets all events about blah
- plot_events: Display and summary and timeline of events.


Other Options
~~~~~~~~~~~~~

- get_metadata: fetches additional metadata about the entity