Notebooklet Class - EnrichAlerts
================================

Alert Enrichment Notebooklet Class.

Enriches Azure Sentinel alerts with TI data.

--------------

Display Sections
----------------

--------------

Results Class
-------------

TIEnrichResult
~~~~~~~~~~~~~~

Template Results.

Attributes
~~~~~~~~~~

-  | enriched_results : pd.DataFrame
   | Alerts with additional TI enrichment

-  | picker : SelectAlert
   | Alert picker

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

| run(self, value: Union[str, NoneType] = None, data:
  Union[pandas.core.frame.DataFrame, NoneType] = None, timespan:
  Union[msticpy.common.timespan.TimeSpan, NoneType] = None, options:
  Union[Iterable[str], NoneType] = None, \**kwargs) ->
  msticnb.nb.azsent.alert.ti_enrich.TIEnrichResult
| Return an enriched set of Alerts.

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

Return an enriched set of Alerts.


Parameters
~~~~~~~~~~


timespan : TimeSpan
    Timespan for queries

options : Optional[Iterable[str]], optional
    List of options to use, by default None.
    A value of None means use default options.
    Options prefixed with "+" will be added to the default options.
    To see the list of available options type `help(cls)` where
    "cls" is the notebooklet class or an instance of this class.

value: Optional[str], optional
    If you want to filter Alerts based on a specific entity specify
    it as a string.

data: Optional[pd.DataFrame], optional
    If you have alerts in a DataFrame you can pass them rather than
    having the notebooklet query alerts.


Returns
~~~~~~~


TIEnrichResult
    Result object with attributes for each result type.


Raises
~~~~~~


MsticnbMissingParameterError
    If required parameters are missing


MsticnbDataProviderError
    If data is not avaliable



Default Options
~~~~~~~~~~~~~~~

- TI: Uses TI to enrich alert data. Will use your primary TI providers.
- details: Displays a widget allowing you to see more detail about an alert.


Other Options
~~~~~~~~~~~~~

- secondary: Uses secondary TI providers in lookups.