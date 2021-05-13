Notebooklet Class - AccountSummary
==================================

Retrieves account summary for the selected account.

Main operations:

-  Searches for matches for the account name in Active Directory,

Windows and Linux host logs.

-  If one or more matches are found it will return a selection

widget that you can use to pick the account.

-  Selecting the account displays a summary of recent activity and

retrieves any alerts and hunting bookmarks related to the account

-  The alerts and bookmarks are browseable using the ``browse_alerts``

and ``browse_bookmarks`` methods

-  You can call the ``get_additional_data`` method to retrieve and

display more detailed activity information for the account.

All of the returned data items are stored in the results class

as entities, pandas DataFrames or Bokeh visualizations.

Run help(nblt) on the notebooklet class to see usage.

Run help(result) on the result class to see documentation of its

properties.

Run the print_options() method on either the notebooklet or

results class to see information about the ``options`` parameter

for the run() method.

**Default Options**

-  get_alerts: Retrieve alerts and display timeline for the account.

-  get_bookmarks: Retrieve investigation bookmarks for the account

**Other Options**

None

--------------

Display Sections
----------------

Account Summary
~~~~~~~~~~~~~~~

This function searches Active Directory, Azure, Office365, Windows and
Linux logs for matching accounts. If any matches are found you can
choose an account to explore, viewing the times of recent event types,
any alerts and hunting bookmarks that relate to the account name. You
can also retrieve recent details of the logon activity or cloud activity
for the account. For further investigation use the host_logons_summary
notebooklet for Windows and Linux host logons.

Host logon attempt timeline
'''''''''''''''''''''''''''

Hover over each timeline event to see details.

IP Address details summary
''''''''''''''''''''''''''

Number of operations detected by IP Address. The table shows WhoIs ASN
Description and Country Code. If UserAgent is contained in the data,
operations are also grouped by this.

Querying for account matches.
'''''''''''''''''''''''''''''

Searching through Active Directory, Windows and Linux events. This may
take a few moments to complete.

Summary of azure activity for AAD, Azure resource and O365
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Shows the total number of operations, the list of unique operations, the
list of unique resource IDs and the first and last operation recorded in
the selected time range. The data is grouped by: - Data source - User -
Type - Azure activity type/source - Client IP Address - Application
resource provider - User type

Summary of host logon activity.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Shows the total number of logons attempts by host. FailedLogons shows
the breakdown of successfully and failed logons. IPAddresses is a list
of distinct source IP addresses for the logons. LogonTypeCount breaks
down the logon type used by count. First and LastLogon shows the
earliest and latest logons on each host by this account in the selected
time range.

--------------

Results Class
-------------

AccountSummaryResult
~~~~~~~~~~~~~~~~~~~~

Account Summary Result.

Attributes
~~~~~~~~~~

-  | account_activity : pd.DataFrame
   | DataFrame of most recent activity.

-  | account_selector : msticpy.nbtools.nbwidgets.SelectString
   | Selection widget for accounts.

-  | related_alerts : pd.DataFrame
   | Alerts related to the account.

-  | alert_timeline : LayoutDOM
   | Timeline of alerts.

-  | related_bookmarks : pd.DataFrame
   | Investigation bookmarks related to the account.

-  | host_logons : pd.DataFrame
   | Host logon attemtps for selected account.

-  | host_logon_summary : pd.DataFrame
   | Host logon summary for selected account.

-  | azure_activity : pd.DataFrame
   | Azure Account activity for selected account.

-  | account_activity_summary : pd.DataFrame
   | Azure activity summary.

-  | azure_timeline_by_provider : LayoutDOM
   | Azure activity timeline grouped by provider

-  | account_timeline_by_ip : LayoutDOM
   | Host or Azure activity timeline by IP Address.

-  | azure_timeline_by_operation : LayoutDOM
   | Azure activity timeline grouped by operation

-  | ip_address_summary : pd.DataFrame
   | Summary of IP address properties and usage for the current
     activity.

-  | ip_all_data : pd.DataFrame
   | Full details of operations with IP WhoIs and GeoIP data.

--------------

Methods
-------

Instance Methods
~~~~~~~~~~~~~~~~

\__init_\_
^^^^^^^^^^

| \__init__(self, *args,* \*kwargs)
| Initialize the Account Summary notebooklet.

az_activity_timeline_by_ip
^^^^^^^^^^^^^^^^^^^^^^^^^^

| az_activity_timeline_by_ip(self)
| Display Azure activity timeline by IP address.

az_activity_timeline_by_operation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

| az_activity_timeline_by_operation(self)
| Display Azure activity timeline by operation.

az_activity_timeline_by_provider
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

| az_activity_timeline_by_provider(self)
| Display Azure activity timeline by provider.

browse_accounts
^^^^^^^^^^^^^^^

| browse_accounts(self) -> msticpy.nbtools.nbwidgets.SelectItem
| Return the accounts browser/viewer.

browse_alerts
^^^^^^^^^^^^^

| browse_alerts(self) -> msticpy.nbtools.nbwidgets.SelectAlert
| Return alert browser/viewer.

browse_bookmarks
^^^^^^^^^^^^^^^^

| browse_bookmarks(self) -> msticpy.nbtools.nbwidgets.SelectItem
| Return bookmark browser/viewer.

display_alert_timeline
^^^^^^^^^^^^^^^^^^^^^^

| display_alert_timeline(self)
| Display the alert timeline.

get_additional_data
^^^^^^^^^^^^^^^^^^^

| get_additional_data(self) -> pandas.core.frame.DataFrame
| Find additional data for the selected account.

get_geoip_map
^^^^^^^^^^^^^

| get_geoip_map(self)
| Return Folium map of IP activity.

host_logon_timeline
^^^^^^^^^^^^^^^^^^^

| host_logon_timeline(self)
| Display IP address summary.

run
^^^

| run(self, value: Any = None, data: Union[pandas.core.frame.DataFrame,
  NoneType] = None, timespan: Union[msticpy.common.timespan.TimeSpan,
  NoneType] = None, options: Union[Iterable[str], NoneType] = None,
  \**kwargs) ->
  msticnb.nb.azsent.account.account_summary.AccountSummaryResult
| Return account activity summary.

show_ip_summary
^^^^^^^^^^^^^^^

| show_ip_summary(self)
| Display Azure activity timeline by operation.

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

Return account activity summary.


Parameters
~~~~~~~~~~


value : str
    Account name to search for.

data : Optional[pd.DataFrame], optional
    Not used.

timespan : TimeSpan
    Timespan for queries

options : Optional[Iterable[str]], optional
    List of options to use, by default None.
    A value of None means use default options.
    Options prefixed with "+" will be added to the default options.
    To see the list of available options type `help(cls)` where
    "cls" is the notebooklet class or an instance of this class.

account_types : Iterable[AccountType], Optional
    A list of account types to search for, by default
    all types.


Returns
~~~~~~~


AccountSummaryResult
    Result object with attributes for each result type.


Raises
~~~~~~


MsticnbMissingParameterError
    If required parameters are missing



Default Options
~~~~~~~~~~~~~~~

- get_alerts: Retrieve alerts and display timeline for the account.
- get_bookmarks: Retrieve investigation bookmarks for the account


Other Options
~~~~~~~~~~~~~


None