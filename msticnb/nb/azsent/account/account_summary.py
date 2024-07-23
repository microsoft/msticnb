# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklet for Account Summary."""
from enum import Flag, auto
from typing import Any, Callable, Dict, Iterable, Optional, Union

import pandas as pd
from bokeh.models import LayoutDOM
from IPython.display import HTML
from msticpy.common.timespan import TimeSpan
from msticpy.common.utility import enum_parse
from msticpy.datamodel import entities

try:
    from msticpy import nbwidgets
    from msticpy.vis.timeline import display_timeline
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.nbtools import nbwidgets
    from msticpy.nbtools.nbdisplay import display_timeline

from .... import nb_metadata
from ...._version import VERSION
from ....common import (
    MsticnbMissingParameterError,
    df_has_data,
    nb_data_wait,
    nb_display,
    nb_markdown,
    set_text,
)
from ....nblib.azsent.alert import browse_alerts
from ....nblib.iptools import get_geoip_whois, map_ips
from ....notebooklet import NBMetadata, Notebooklet, NotebookletResult

__version__ = VERSION
__author__ = "Ian Hellen"

# pylint: disable=too-many-lines
# Read module metadata from YAML
_CLS_METADATA: NBMetadata
_CELL_DOCS: Dict[str, Any]
_CLS_METADATA, _CELL_DOCS = nb_metadata.read_mod_metadata(__file__, __name__)


# pylint: disable=invalid-name
class AccountType(Flag):
    """Account types."""

    AzureActiveDirectory = auto()
    AzureActivity = auto()
    Office365 = auto()
    Windows = auto()
    Linux = auto()
    # pylint:disable=unsupported-binary-operation
    Azure = AzureActiveDirectory | AzureActivity | Office365
    All = Azure | Windows | Linux  # pylint:disable=unsupported-binary-operation

    def in_list(self, acct_types: Iterable[Union["AccountType", str]]):
        """Is the current value in the `acct_types` list."""
        for acct_type in acct_types:
            if isinstance(acct_type, str):
                acct_type = AccountType[acct_type]
            if self & acct_type:
                return True
        return False

    @classmethod
    def parse(cls, name: str):
        """Try to parse string to valid account type."""
        return enum_parse(cls, name)


# pylint: enable=invalid-name

# pylint: disable=no-member


# pylint: disable=too-few-public-methods, too-many-instance-attributes
class AccountSummaryResult(NotebookletResult):
    """
    Account Summary Result.

    Attributes
    ----------
    account_activity : pd.DataFrame
        DataFrame of most recent activity.
    account_selector : msticpy.nbtools.nbwidgets.SelectString
        Selection widget for accounts.
    related_alerts : pd.DataFrame
        Alerts related to the account.
    alert_timeline : LayoutDOM
        Timeline of alerts.
    related_bookmarks : pd.DataFrame
        Investigation bookmarks related to the account.
    host_logons : pd.DataFrame
        Host logon attemtps for selected account.
    host_logon_summary : pd.DataFrame
        Host logon summary for selected account.
    azure_activity : pd.DataFrame
        Azure Account activity for selected account.
    account_activity_summary : pd.DataFrame
        Azure activity summary.
    azure_timeline_by_provider : LayoutDOM
        Azure activity timeline grouped by provider
    account_timeline_by_ip : LayoutDOM
        Host or Azure activity timeline by IP Address.
    azure_timeline_by_operation : LayoutDOM
        Azure activity timeline grouped by operation
    ip_address_summary : pd.DataFrame
        Summary of IP address properties and usage for
        the current activity.
    ip_all_data : pd.DataFrame
        Full details of operations with IP WhoIs and GeoIP
        data.

    """

    def __init__(
        self,
        description: Optional[str] = None,
        timespan: Optional[TimeSpan] = None,
        notebooklet: Optional["Notebooklet"] = None,
    ):
        """
        Create new Notebooklet result instance.

        Parameters
        ----------
        description : Optional[str], optional
            Result description, by default None
        timespan : Optional[TimeSpan], optional
            TimeSpan for the results, by default None
        notebooklet : Optional[, optional
            Originating notebooklet, by default None

        """
        super().__init__(description, timespan, notebooklet)
        self.description: str = "Account Activity Summary"
        self.account_entity: entities.Account = None
        self.account_activity: Optional[pd.DataFrame] = None
        self.account_selector: Optional[nbwidgets.SelectItem] = None
        self.related_alerts: Optional[pd.DataFrame] = None
        self.alert_timeline: Optional[LayoutDOM] = None
        self.related_bookmarks: Optional[pd.DataFrame] = None
        self.host_logons: Optional[pd.DataFrame] = None
        self.host_logon_summary: Optional[pd.DataFrame] = None
        self.azure_activity: Optional[pd.DataFrame] = None
        self.azure_activity_summary: Optional[pd.DataFrame] = None
        self.azure_timeline_by_provider: Optional[LayoutDOM] = None
        self.account_timeline_by_ip: Optional[LayoutDOM] = None
        self.azure_timeline_by_operation: Optional[LayoutDOM] = None
        self.ip_summary: Optional[pd.DataFrame] = None
        self.ip_all_data: Optional[pd.DataFrame] = None


# pylint: enable=too-few-public-methods


class AccountSummary(Notebooklet):
    """
    Retrieves account summary for the selected account.

    Main operations:

    - Searches for matches for the account name in Active Directory,
      Windows and Linux host logs.
    - If one or more matches are found it will return a selection
      widget that you can use to pick the account.
    - Selecting the account displays a summary of recent activity and
      retrieves any alerts and hunting bookmarks related to the account
    - The alerts and bookmarks are browseable using the `browse_alerts`
      and `browse_bookmarks` methods
    - You can call the `get_additional_data` method to retrieve and
      display more detailed activity information for the account.

    All of the returned data items are stored in the results class
    as entities, pandas DataFrames or Bokeh visualizations.
    Run help(nblt) on the notebooklet class to see usage.
    Run help(result) on the result class to see documentation of its
    properties.
    Run the print_options() method on either the notebooklet or
    results class to see information about the `options` parameter
    for the run() method.

    """

    # assign metadata from YAML to class variable
    metadata = _CLS_METADATA
    __doc__ = nb_metadata.update_class_doc(__doc__, metadata)
    _cell_docs = _CELL_DOCS

    ACCOUNT_TYPE = AccountType

    def __init__(self, *args, **kwargs):
        """Initialize the Account Summary notebooklet."""
        super().__init__(*args, **kwargs)
        self._geo_lookup = None

    # pylint: disable=too-many-branches

    @set_text(docs=_CELL_DOCS, key="run")
    def run(
        self,
        value: Any = None,
        data: Optional[pd.DataFrame] = None,
        timespan: Optional[TimeSpan] = None,
        options: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> AccountSummaryResult:
        """
        Return account activity summary.

        Parameters
        ----------
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
        -------
        AccountSummaryResult
            Result object with attributes for each result type.

        Raises
        ------
        MsticnbMissingParameterError
            If required parameters are missing

        """
        # This line use logic in the superclass to populate options
        # (including default options) into this class.
        super().run(
            value=value, data=data, timespan=timespan, options=options, **kwargs
        )

        if not value:
            raise MsticnbMissingParameterError("value")
        if not timespan:
            raise MsticnbMissingParameterError("timespan.")

        # Create a result class
        result = AccountSummaryResult(
            notebooklet=self, description=self.metadata.description, timespan=timespan
        )
        self.timespan = timespan
        acc_types = kwargs.get("account_types")
        if acc_types is None:
            acc_types = AccountType.__members__

        # Search for events for specified account types
        all_acct_dfs = _get_matching_accounts(
            self.query_provider,
            account=value,
            timespan=timespan,
            account_types=acc_types,
        )

        self._geo_lookup = self.get_provider("geolitelookup") or self.get_provider(
            "ipstacklookup"
        )

        acct_index_df = _create_account_index(all_acct_dfs)
        if acct_index_df.empty:
            nb_markdown("No accounts matching that name.")
        else:
            result.account_selector = _get_account_selector(
                qry_prov=self.query_provider,
                all_acct_dfs=all_acct_dfs,
                result=result,
                timespan=timespan,
                options=self.options,
                geoip=self._geo_lookup,
            )
        if len(acct_index_df) == 1:
            # If a single account - just display directly.
            disp_func = _create_display_callback(
                qry_prov=self.query_provider,
                all_acct_dfs=all_acct_dfs,
                result=result,
                timespan=timespan,
                options=self.options,
                geoip=self._geo_lookup,
            )
            acct_row = acct_index_df.iloc[0]
            outputs = disp_func(f"{acct_row.AccountName} {acct_row.Source}")
            for output in outputs:
                nb_display(output)
            if not self.silent:
                self.display_alert_timeline()
        elif len(acct_index_df) > 1:
            # if multiple, create a selector
            nb_markdown("<hr>")
            nb_markdown(
                "Multiple matching accounts found, select one to see details.", "large"
            )
            nb_display(result.account_selector)

        if not acct_index_df.empty:
            nb_markdown("<hr>")
            nb_markdown(
                "<h3>Use <i>result.notebooklet.get_additional_data()</i>"
                + " to retrieve more data."
            )
            nb_markdown(
                f"Additional methods for this class:<br>{'<br>'.join(self.list_methods())}"
            )
        # Assign the result to the _last_result attribute
        # so that you can get to it without having to re-run the operation
        self._last_result = result  # pylint: disable=attribute-defined-outside-init

        return self._last_result

    # pylint: enable=too-many-branches

    def display_alert_timeline(self):
        """Display the alert timeline."""
        if self.check_valid_result_data("related_alerts"):
            if len(self._last_result.related_alerts) > 1:
                return _get_alerts_timeline(
                    self._last_result.related_alerts, silent=False
                )
            print("Cannot plot timeline with 0 or 1 event.")
        return None

    def browse_accounts(self) -> nbwidgets.SelectItem:
        """Return the accounts browser/viewer."""
        if self.check_valid_result_data("account_selector"):
            return self._last_result.account_selector
        return None

    def browse_alerts(self) -> nbwidgets.SelectAlert:
        """Return alert browser/viewer."""
        if self.check_valid_result_data("related_alerts"):
            return browse_alerts(self._last_result)
        return None

    def browse_bookmarks(self) -> nbwidgets.SelectItem:
        """Return bookmark browser/viewer."""
        if self.check_valid_result_data("related_bookmarks"):
            return _get_bookmark_select(self._last_result.related_bookmarks)
        return None

    def az_activity_timeline_by_provider(self):
        """Display Azure activity timeline by provider."""
        if self.check_valid_result_data("azure_activity"):
            return _plot_timeline_by_provider(self._last_result.azure_activity)
        return None

    def az_activity_timeline_by_ip(self):
        """Display Azure activity timeline by IP address."""
        if self.check_valid_result_data("azure_activity"):
            return _plot_timeline_by_ip(self._last_result.azure_activity)
        return None

    def az_activity_timeline_by_operation(self):
        """Display Azure activity timeline by operation."""
        if self.check_valid_result_data("azure_activity"):
            return _plot_timeline_by_operation(self._last_result.azure_activity)
        return None

    def show_ip_summary(self):
        """Display Azure activity timeline by operation."""
        if self.check_valid_result_data("ip_summary"):
            nb_display(self._last_result.ip_summary)

    def host_logon_timeline(self):
        """Display IP address summary."""
        if self.check_valid_result_data("host_logons"):
            _, source = self._get_selected_account()
            ip_col = (
                "SourceIP"
                if AccountType.parse(source) == AccountType.Linux
                else "IpAddress"
            )
            return _create_host_timeline(
                self._last_result.host_logons, ip_col=ip_col, silent=False
            )
        return None

    def get_geoip_map(self):
        """Return Folium map of IP activity."""
        if self.check_valid_result_data("azure_activity", silent=True):
            return map_ips(
                data=self._last_result.azure_activity,
                ip_col="IPAddress",
                summary_cols=["SourceSystem", "Operation"],
                geo_lookup=self._geo_lookup,
            )
        if self.check_valid_result_data("host_logons", silent=True):
            ip_col = (
                "SourceIP"
                if "SourceIP" in self._last_result.host_logons.columns
                else "IpAddress"
            )
            return map_ips(
                data=self._last_result.host_logons,
                ip_col=ip_col,
                summary_cols=["Source", "Computer", "Operation"],
                geo_lookup=self._geo_lookup,
            )

        print(
            "Please ensure that you have run the 'run()'",
            "and 'get_additional_data()' methods before calling this.",
        )
        return None

    @set_text(docs=_CELL_DOCS, key="find_additional_data")
    def get_additional_data(self):
        """Find additional data for the selected account."""
        if not self.check_valid_result_data():
            return None
        acct, source = self._get_selected_account()
        if not acct or not source:
            print("Please use select an account before using this method.")
            return None
        self._last_result.host_logons = None
        self._last_result.host_logon_summary = None
        self._last_result.account_timeline_by_ip = None
        self._last_result.azure_activity = None
        self._last_result.azure_timeline_by_provider = None
        self._last_result.account_timeline_by_ip = None
        self._last_result.azure_timeline_by_operation = None
        self._last_result.azure_activity_summary = None
        self._last_result.ip_summary = None

        acct_type = AccountType.parse(source)
        if acct_type == AccountType.Linux:
            self._last_result.host_logons = _get_linux_add_activity(
                self.query_provider, acct, self.timespan
            )
            self._last_result.host_logon_summary = _summarize_host_activity(
                self._last_result.host_logons, ip_col="SourceIP"
            )
            self._last_result.account_timeline_by_ip = _create_host_timeline(
                self._last_result.host_logons, ip_col="SourceIP", silent=self.silent
            )
            (
                self._last_result.ip_summary,
                self._last_result.ip_all_data,
            ) = _create_ip_summary(
                self._last_result.host_logons,
                ip_col="SourceIP",
                geoip=self._geo_lookup,
            )
            nb_display(self._last_result.ip_summary)
            return None
        if acct_type == AccountType.Windows:
            self._last_result.host_logons = _get_windows_add_activity(
                self.query_provider, acct, self.timespan
            )
            self._last_result.host_logon_summary = _summarize_host_activity(
                self._last_result.host_logons, ip_col="IpAddress"
            )
            self._last_result.account_timeline_by_ip = _create_host_timeline(
                self._last_result.host_logons, ip_col="IpAddress", silent=self.silent
            )
            (
                self._last_result.ip_summary,
                self._last_result.ip_all_data,
            ) = _create_ip_summary(
                self._last_result.host_logons,
                ip_col="IpAddress",
                geoip=self._geo_lookup,
            )
            nb_display(self._last_result.ip_summary)
            return None
        if acct_type in [
            AccountType.AzureActiveDirectory,
            AccountType.AzureActivity,
            AccountType.Office365,
        ]:
            az_activity = _get_azure_add_activity(
                self.query_provider, acct, self.timespan
            )
            self._last_result.azure_activity = az_activity
            timelines = _create_azure_timelines(az_activity, self.silent)
            self._last_result.azure_timeline_by_provider = timelines[0]
            self._last_result.account_timeline_by_ip = timelines[1]
            self._last_result.azure_timeline_by_operation = timelines[2]
            self._last_result.azure_activity_summary = _summarize_azure_activity(
                az_activity
            )
            (
                self._last_result.ip_summary,
                self._last_result.ip_all_data,
            ) = _create_ip_summary(
                self._last_result.azure_activity,
                ip_col="IPAddress",
                geoip=self._geo_lookup,
            )
            nb_display(self._last_result.ip_summary)
            return None
        return None

    def _get_selected_account(self):
        if (
            self._last_result is not None
            and self._last_result.account_selector is not None
        ):
            return self._last_result.account_selector.value.split(" ")
        return "", ""


# pylint: disable=no-member


# %%
# Account Query functions
def _df_clean(dataframe):
    """Clean empty aggregate rows because of arg_max."""
    if isinstance(dataframe, pd.DataFrame):
        return dataframe[dataframe["TimeGenerated"].notna()]
    return pd.DataFrame()


@set_text(docs=_CELL_DOCS, key="get_matching_accounts")
def _get_matching_accounts(qry_prov, timespan, account, account_types):
    """Get Account Activity for `account` in `timespan`."""
    account_dfs = {}
    rec_count = 0
    if AccountType.AzureActiveDirectory.in_list(account_types):
        nb_data_wait("AADSignin")
        summarize_clause = f"""
        | summarize arg_max(TimeGenerated, *)
        | extend AccountName = UserPrincipalName,
          Source = '{AccountType.AzureActiveDirectory.name}'
        """

        aad_signin_df = qry_prov.Azure.list_aad_signins_for_account(
            timespan, account_name=account, add_query_items=summarize_clause
        )
        aad_signin_df = _df_clean(aad_signin_df)
        rec_count += len(aad_signin_df)
        nb_markdown(f"  {len(aad_signin_df)} records in AAD")
        account_dfs[AccountType.AzureActiveDirectory] = aad_signin_df

    if AccountType.Office365.in_list(account_types):
        nb_data_wait("Office365Activity")
        # Office Activity
        summarize_clause = f"""
        | extend UserId = tolower(UserId)
        | summarize arg_max(TimeGenerated, *)
        | extend IPAddress = case(
            isnotempty(Client_IPAddress), Client_IPAddress,
            isnotempty(ClientIP), ClientIP,
            isnotempty(ClientIP_), ClientIP_,
            Client_IPAddress
        )
        | extend AccountName = UserId,
          UserPrincipalName = UserId,
          Source = '{AccountType.Office365.name}'
        """

        o365_activity_df = qry_prov.Office365.list_activity_for_account(
            timespan, account_name=account, add_query_items=summarize_clause
        )
        o365_activity_df = _df_clean(o365_activity_df)
        rec_count += len(o365_activity_df)
        nb_markdown(f"  {len(o365_activity_df)} records in Office Activity")
        account_dfs[AccountType.Office365] = o365_activity_df

    if AccountType.Windows.in_list(account_types):
        nb_data_wait("Windows Logon activity")
        # Windows Host
        summarize_clause = f"""
        | extend LogonStatus = iff(EventID == 4624, "success", "failed")
        | summarize arg_max(TimeGenerated, *)
        | extend AccountName = TargetUserName,
          Source = '{AccountType.Windows.name}'
        """

        win_logon_df = qry_prov.WindowsSecurity.list_logon_attempts_by_account(
            timespan, account_name=account, add_query_items=summarize_clause
        )
        win_logon_df = _df_clean(win_logon_df)
        rec_count += len(win_logon_df)
        nb_markdown(f"  {len(win_logon_df)} records in Windows logon data")
        account_dfs[AccountType.Windows] = win_logon_df

    if AccountType.Linux.in_list(account_types):
        nb_data_wait("Linux logon activity")
        # Linux host
        summarize_clause = f"""
        | summarize arg_max(TimeGenerated, *)
        | extend Source = '{AccountType.Linux.name}'
        """

        linux_logon_df = qry_prov.LinuxSyslog.list_logons_for_account(
            timespan, account_name=account, add_query_items=summarize_clause
        )
        linux_logon_df = _df_clean(linux_logon_df)
        rec_count += len(linux_logon_df)
        nb_markdown(f"  {len(linux_logon_df)} records in Linux logon data")
        account_dfs[AccountType.Linux] = linux_logon_df

    nb_markdown(f"Found {rec_count} total records.")

    return account_dfs


# %%
# Account selector functions
def _display_acct_activity(
    selected_item: str, acct_activity_df: pd.DataFrame
) -> Iterable[Any]:
    """Return list of display objects for Select list display."""
    acct, source = selected_item.split(" ")
    outputs = []
    title = HTML(f"<b>{acct} (source: {source})</b>")
    outputs.append(title)
    outputs.append(acct_activity_df.sort_values("TimeGenerated", ascending=True))
    return outputs


def _get_select_acct_dict(acct_index_df: pd.DataFrame) -> Dict[str, str]:
    """Return dictionary of account entries for Select list."""

    def format_tuple(row):
        return (
            row.AccountName
            + "   "
            + row.Source
            + " (Last activity: "
            + str(row.TimeGenerated)
            + ")",
            row.AccountName + " " + row.Source,
        )

    return {item[0]: item[1] for item in acct_index_df.apply(format_tuple, axis=1)}


def _create_account_index(all_acct_dfs):
    acct_activity_df = pd.concat(all_acct_dfs.values())
    if acct_activity_df.empty:
        return acct_activity_df[["AccountName", "Source", "TimeGenerated"]]
    return (
        acct_activity_df[["AccountName", "Source", "TimeGenerated"]]
        .groupby(["AccountName", "Source"])
        .max()
        .reset_index()
        .dropna()
    )


def _get_account_selector(
    qry_prov, all_acct_dfs: pd.DataFrame, result, timespan, options, geoip
):
    """Build and return the Account Select list."""
    action_func = _create_display_callback(
        qry_prov=qry_prov,
        all_acct_dfs=all_acct_dfs,
        result=result,
        timespan=timespan,
        options=options,
        geoip=geoip,
    )

    acct_index_df = _create_account_index(all_acct_dfs)
    accts_dict = _get_select_acct_dict(acct_index_df)
    return nbwidgets.SelectItem(
        item_dict=accts_dict,
        description="Select an account to explore",
        action=action_func,
        height="200px",
        width="100%",
    )


def _create_display_callback(
    qry_prov, all_acct_dfs, result, timespan, options, geoip
) -> Callable[[str], Iterable[Any]]:
    """Create closure for display_acct callback."""

    def display_account(selected_item: str):
        account_name, source = selected_item.split(" ")
        acct_type = AccountType.parse(source)
        outputs = []

        # Create entity
        acct_entity = _create_account_entity(
            account_name, acct_type, all_acct_dfs, geoip
        )
        outputs.append(HTML("<h3>Account Entity</h3>"))
        result.account_entity = acct_entity
        outputs.append(acct_entity)
        # Add account activity
        outputs.append(HTML("<h3>Account last activity</h3>"))
        outputs.extend(_display_acct_activity(selected_item, all_acct_dfs[acct_type]))
        result.account_activity = all_acct_dfs[acct_type]

        # Optional alerts and bookmarks
        if "get_alerts" in options:
            related_alerts = _get_related_alerts(qry_prov, account_name, timespan)
            result.related_alerts = related_alerts
            outputs.append(_get_related_alerts_summary(related_alerts))
            if df_has_data(related_alerts):
                result.alert_timeline = _get_alerts_timeline(related_alerts)
        if "get_bookmarks" in options:
            related_bkmarks = _get_related_bookmarks(qry_prov, account_name, timespan)
            result.related_bookmarks = related_bkmarks
            outputs.append(_get_related_bkmks_summary(related_bkmarks))
        return outputs

    return display_account


# %%
# Account entity from data
def _create_account_entity(
    account_name, acct_type, acct_activity_dfs, geoip
) -> entities.Account:
    if acct_type == AccountType.Windows:
        acct_activity_df = acct_activity_dfs[AccountType.Windows]
        return _create_win_account_entity(account_name, acct_activity_df, geoip)

    if acct_type == AccountType.Linux:
        acct_activity_df = acct_activity_dfs[AccountType.Linux]
        return _create_lx_account_entity(account_name, acct_activity_df, geoip)

    if acct_type == AccountType.AzureActiveDirectory:
        acct_activity_df = acct_activity_dfs[AccountType.AzureActiveDirectory]
        return _create_aad_account_entity(account_name, acct_activity_df, geoip)

    if acct_type == AccountType.Office365:
        acct_activity_df = acct_activity_dfs[AccountType.Office365]
        return _create_o365_account_entity(account_name, acct_activity_df, geoip)

    acc_entity = entities.Account()
    acc_entity.Name = account_name
    return acc_entity


def _create_win_account_entity(
    account_name: str, acct_activity_df: pd.DataFrame, geoip
) -> entities.Account:
    account_events = acct_activity_df[acct_activity_df["AccountName"] == account_name]
    account_event = account_events.iloc[0]
    acc_entity = entities.Account(src_event=account_event)
    acc_entity.LogonType = account_event["LogonTypeName"]
    acc_entity.AadTenantId = account_event["TenantId"]

    host_grp = _create_host_ip_group(
        account_events, host_column="Computer", ip_column="IpAddress"
    )
    acc_hosts = list(_create_host_entities(host_grp, geoip))
    if len(acc_hosts) == 1:
        acc_entity.Host = acc_hosts[0]
    else:
        acc_entity.Hosts = acc_hosts
    return acc_entity


def _create_lx_account_entity(
    account_name: str, acct_activity_df: pd.DataFrame, geoip
) -> entities.Account:
    acc_entity = entities.Account()
    account_events = acct_activity_df[acct_activity_df["AccountName"] == account_name]
    account_event = account_events.iloc[0]
    acc_entity.Name = account_event["AccountName"]
    acc_entity.LogonType = account_event["LogonType"]
    acc_entity.Sid = account_event["UID"]
    acc_entity.AadTenantId = account_event["TenantId"]
    host_grp = _create_host_ip_group(
        account_events, host_column="Computer", ip_column="SourceIP"
    )
    acc_hosts = list(_create_host_entities(host_grp, geoip))
    if len(acc_hosts) == 1:
        acc_entity.Host = acc_hosts[0]
    else:
        acc_entity.Hosts = acc_hosts
    return acc_entity


def _create_host_ip_group(data, host_column, ip_column):
    """Group data by Host."""
    return data.groupby([host_column, ip_column]).agg(
        FirstSeen=pd.NamedAgg(column="TimeGenerated", aggfunc="min"),
        LastSeen=pd.NamedAgg(column="TimeGenerated", aggfunc="max"),
    )


# pylint: disable=too-many-branches
def _create_host_entities(data, geoip):
    """Create Host and IP Entities with GeoIP info."""
    for row in data.itertuples():
        host, ip_addr = row.Index
        if not host:
            continue
        host_ent = entities.Host(HostName=host)
        if not ip_addr:
            yield host_ent
            continue
        # If we have an IP address - get the IpAddress entity(ies)
        _, ip_entities = geoip.lookup_ip(ip_addr) if geoip else (None, [])
        if not ip_entities:
            host_ent.IpAddress = entities.IpAddress(Address=ip_addr)
            host_ent.IpAddress.FirstSeen = row.FirstSeen
            host_ent.IpAddress.LastSeen = row.LastSeen
        elif len(ip_entities) == 1:
            host_ent.IpAddress = ip_entities[0]
            host_ent.IpAddress.FirstSeen = row.FirstSeen
            host_ent.IpAddress.LastSeen = row.LastSeen
        else:
            host_ent.IpAddresses = []
            for ip_ent in ip_entities:
                ip_ent.FirstSeen = row.FirstSeen
                ip_ent.LastSeen = row.LastSeen
                host_ent.IpAddresses.append(ip_ent)

        yield host_ent


# pylint: enable=too-many-branches


def _create_aad_account_entity(
    account_name: str, acct_activity_df: pd.DataFrame, geoip
) -> entities.Account:
    acc_entity = entities.Account()
    account_events = acct_activity_df[
        (acct_activity_df["AccountName"] == account_name)
        & (acct_activity_df["Source"] == AccountType.AzureActiveDirectory.name)
    ]
    account_event = account_events.iloc[0]
    acc_entity.Name = account_event["UserPrincipalName"]
    if "@" in account_event["UserPrincipalName"]:
        acc_entity.UPNSuffix = account_event["UserPrincipalName"].split("@")[1]
    acc_entity.AadTenantId = account_event["AADTenantId"]
    acc_entity.AadUserId = account_event["UserId"]
    acc_entity.DisplayName = account_event["UserDisplayName"]
    acc_entity.DeviceDetail = account_event["DeviceDetail"]
    acc_entity.Location = account_event["LocationDetails"]
    acc_entity.UserAgent = account_event["UserAgent"]

    ip_grp = _create_ip_group(account_events, "IPAddress")
    ip_addrs = list(_create_ip_entities(ip_grp, geoip))
    if len(ip_addrs) == 1:
        acc_entity.IpAddress = ip_addrs[0]
    else:
        acc_entity.IpAddresses = ip_addrs
    return acc_entity


def _create_o365_account_entity(account_name, acct_activity_df, geoip):
    acc_entity = entities.Account()
    o365_events = acct_activity_df[
        (acct_activity_df["AccountName"] == account_name)
        & (acct_activity_df["Source"] == AccountType.Office365.name)
    ]
    account_event = o365_events.iloc[0]
    acc_entity.Name = account_event["UserId"]
    if "@" in account_event["UserId"]:
        acc_entity.UPNSuffix = account_event["UserId"].split("@")[1]
    acc_entity.AadTenantId = account_event["TenantId"]
    acc_entity.OrganizationId = account_event["OrganizationId"]

    ip_grp = _create_ip_group(o365_events, "IPAddress")
    ip_addrs = list(_create_ip_entities(ip_grp, geoip))
    if len(ip_addrs) == 1:
        acc_entity.IpAddress = ip_addrs[0]
    else:
        acc_entity.IpAddresses = ip_addrs

    return acc_entity


def _create_ip_group(data, ip_column):
    """Group data by IP Address."""
    return data.groupby(ip_column).agg(
        FirstSeen=pd.NamedAgg(column="TimeGenerated", aggfunc="min"),
        LastSeen=pd.NamedAgg(column="TimeGenerated", aggfunc="max"),
    )


def _create_ip_entities(data, geoip):
    """Create IP Entities with GeoIP info."""
    for row in data.itertuples():
        if row.Index:
            if not geoip:
                ip_ent = entities.IpAddress(Address=row.Index)
                ip_ent.FirstSeen = row.FirstSeen
                ip_ent.LastSeen = row.LastSeen
                yield ip_ent
            else:
                _, ip_entities = geoip.lookup_ip(row.Index)
                for ip_ent in ip_entities:
                    ip_ent.FirstSeen = row.FirstSeen
                    ip_ent.LastSeen = row.LastSeen
                    yield ip_ent


# %%
# Alert and bookmark details
def _get_related_alerts(
    qry_prov, account_name: str, timespan: TimeSpan
) -> pd.DataFrame:
    nb_data_wait("Alerts")
    return qry_prov.SecurityAlert.list_related_alerts(
        timespan, account_name=account_name
    )


def _get_alerts_timeline(related_alerts: pd.DataFrame, silent=True) -> LayoutDOM:
    """Return alert timeline."""
    return display_timeline(
        data=related_alerts,
        title="Alerts",
        source_columns=["AlertName"],
        height=300,
        hide=silent,
    )


def _get_related_alerts_summary(related_alerts: pd.DataFrame):
    if related_alerts.empty:
        return HTML("<br><b>No alerts for this account</b>")
    alert_items = (
        related_alerts[["AlertName", "TimeGenerated"]]
        .groupby("AlertName")
        .TimeGenerated.agg("count")
        .to_dict()
    )
    output = [
        "<h3>Related alerts</h3>",
        f"<b>Found {len(alert_items)} different alert types "
        f"related to this account</b>",
    ]

    total_alerts = 0
    for name, count in alert_items.items():
        output.append(f"- {name}, # Alerts: {count}")
        total_alerts += count

    if total_alerts > 1:
        output.append(
            "<br>To show the alert timeline call the <b>display_alert_timeline()</b> method."
        )
    output.append("To browse the alerts call the <b>browse_alerts()</b> method.")
    return HTML("<br>".join(output))


def _get_related_bookmarks(
    qry_prov, account_name: str, timespan: TimeSpan
) -> pd.DataFrame:
    nb_data_wait("Bookmarks")
    return qry_prov.AzureSentinel.list_bookmarks_for_entity(
        timespan, entity_id=account_name
    )


def _get_related_bkmks_summary(related_bookmarks: pd.DataFrame):
    if related_bookmarks.empty:
        return HTML("<br><b>No bookmarks for this account</b>")
    bookmarks = list(
        related_bookmarks.apply(
            lambda x: (
                f"{x.BookmarkName} [{x.Tags}]  {x.TimeGenerated}"
                + ", BookmarkId:{x.BookmarkId}"
            ),
            axis=1,
        )
    )
    output = [
        "<h3>Related bookmarks</h3>",
        f"<b>Found {len(bookmarks)} different bookmarks " "related to this account</b>",
        *bookmarks,
        "<br>To browse the bookmarks call the <b>browse_bookmarks()</b> method.",
    ]

    return HTML("<br>".join(output))


def _get_bookmark_select(bookmarks_df):
    """Create and return Selector for bookmarks."""
    opts = dict(
        bookmarks_df.apply(
            lambda x: (
                f"{x.BookmarkName} - LastUpdated {x.LastUpdatedTime}",
                x.BookmarkId,
            ),
            axis=1,
        ).values
    )

    def display_bookmark(bookmark_id):
        return pd.DataFrame(
            data=bookmarks_df[bookmarks_df["BookmarkId"] == bookmark_id].iloc[0].T
        ).rename(columns={0: "value"})

    return nbwidgets.SelectItem(
        item_dict=opts, action=display_bookmark, height="200px", width="100%"
    )


# %%
# Get Linux logon activity
def _get_linux_add_activity(qry_prov, acct, timespan):
    nb_data_wait("LinuxSyslog")
    ext_logon_result = "| extend Operation = strcat('Logon-', LogonResult)"
    return qry_prov.LinuxSyslog.list_logons_for_account(
        timespan, account_name=acct, add_query_items=ext_logon_result
    )


@set_text(docs=_CELL_DOCS, key="summarize_host_activity")
def _summarize_host_activity(all_logons: pd.DataFrame, ip_col="SourceIP"):
    """Summarize logon activity on win or linux host."""
    summary = all_logons.groupby("Computer").agg(
        TotalLogons=pd.NamedAgg(column="Computer", aggfunc="count"),
        FailedLogons=pd.NamedAgg(
            column="LogonResult", aggfunc=lambda x: x.value_counts().to_dict()
        ),
        IpAddresses=pd.NamedAgg(column=ip_col, aggfunc=lambda x: x.unique().tolist()),
        LogonTypeCount=pd.NamedAgg(
            column="LogonType", aggfunc=lambda x: x.value_counts().to_dict()
        ),
        FirstLogon=pd.NamedAgg(column="TimeGenerated", aggfunc="min"),
        LastLogon=pd.NamedAgg(column="TimeGenerated", aggfunc="max"),
    )
    nb_display(summary)
    return summary


@set_text(docs=_CELL_DOCS, key="create_host_timeline")
def _create_host_timeline(
    all_logons: pd.DataFrame, ip_col="SourceIP", silent: bool = False
):
    return display_timeline(
        data=all_logons,
        group_by=ip_col,
        source_columns=["Computer", "LogonResult", "LogonType"],
        title="Timeline of Logons by source IP address",
        hide=silent,
    )


# %%
# Get Windows logon activity
def _get_windows_add_activity(qry_prov, acct, timespan):
    nb_data_wait("WindowsSecurity")
    ext_logon_result = """
        | extend LogonResult = iff(EventID == 4624, 'Success', 'Failed')
        | extend Operation = strcat("Logon-", LogonResult)
    """
    return qry_prov.WindowsSecurity.list_logon_attempts_by_account(
        timespan, account_name=acct, add_query_items=ext_logon_result
    )


# %%
# Get Azure/AAD/Office activity
def _get_azure_add_activity(qry_prov, acct, timespan):
    """Get Azure additional data for account."""
    nb_data_wait("AADSignin")
    aad_sum_qry = f"""
        | extend UserPrincipalName=tolower(UserPrincipalName)
        | extend Source = '{AccountType.AzureActiveDirectory.name}'
        | project-rename Operation=OperationName, AppResourceProvider=AppDisplayName
    """
    aad_logons = qry_prov.Azure.list_aad_signins_for_account(
        timespan, account_name=acct, add_query_items=aad_sum_qry
    )

    nb_data_wait("AzureActivity")
    az_sum_qry = f"""
        | extend UserPrincipalName=tolower(Caller)
        | extend Source = '{AccountType.AzureActivity.name}'
        | project-rename IPAddress=CallerIpAddress, Operation=OperationName,
        AppResourceProvider=ResourceProvider
    """
    az_activity = qry_prov.Azure.list_azure_activity_for_account(
        timespan, account_name=acct, add_query_items=az_sum_qry
    )

    nb_data_wait("Office365Activity")
    o365_sum_qry = f"""
        | extend UserPrincipalName=tolower(UserId)
        | extend Source = '{AccountType.Office365.name}'
        | extend IPAddress = case(
            isnotempty(Client_IPAddress), Client_IPAddress,
            isnotempty(ClientIP), ClientIP,
            isnotempty(ClientIP_), ClientIP_,
            Client_IPAddress
        )
        | project-rename ResourceId=OfficeObjectId, AppResourceProvider=OfficeWorkload
    """
    o365_activity = qry_prov.Office365.list_activity_for_account(
        timespan, account_name=acct, add_query_items=o365_sum_qry
    )

    return pd.concat(
        [aad_logons, az_activity, o365_activity], ignore_index=True, sort=False
    ).sort_values("TimeGenerated")


@set_text(docs=_CELL_DOCS, key="create_az_timelines")
def _create_azure_timelines(az_all_data: pd.DataFrame, silent: bool = False):
    return (
        _plot_timeline_by_provider(az_all_data, silent),
        _plot_timeline_by_ip(az_all_data, silent),
        _plot_timeline_by_operation(az_all_data, silent),
    )


def _plot_timeline_by_provider(az_all_data, silent=False):
    return display_timeline(
        data=az_all_data,
        group_by="AppResourceProvider",
        source_columns=["Operation", "IPAddress", "AppResourceProvider"],
        title="Azure account activity by Provider",
        hide=silent,
    )


def _plot_timeline_by_ip(az_all_data, silent=False):
    return display_timeline(
        data=az_all_data,
        group_by="IPAddress",
        source_columns=[
            "AppResourceProvider",
            "Operation",
            "IPAddress",
            "AppResourceProvider",
        ],
        title="Azure Operations by Source IP",
        hide=silent,
    )


def _plot_timeline_by_operation(az_all_data, silent=False):
    return display_timeline(
        data=az_all_data,
        group_by="Operation",
        source_columns=["AppResourceProvider", "Operation", "IPAddress"],
        title="Azure Operations by Operation",
        hide=silent,
    )


@set_text(docs=_CELL_DOCS, key="summarize_azure_activity")
def _summarize_azure_activity(az_all_data: pd.DataFrame):
    summary = az_all_data.groupby(
        ["UserPrincipalName", "Type", "IPAddress", "AppResourceProvider", "UserType"]
    ).agg(
        OperationCount=pd.NamedAgg(column="Type", aggfunc="count"),
        OperationTypes=pd.NamedAgg(
            column="Operation", aggfunc=lambda x: x.unique().tolist()
        ),
        Resources=pd.NamedAgg(column="ResourceId", aggfunc="nunique"),
        FirstOperation=pd.NamedAgg(column="TimeGenerated", aggfunc="min"),
        LastOperation=pd.NamedAgg(column="TimeGenerated", aggfunc="max"),
    )
    nb_display(summary)
    return summary


@set_text(docs=_CELL_DOCS, key="get_ip_summary")
def _create_ip_summary(data, ip_col, geoip):
    group_cols1 = ["Source", "Operation"]
    group_cols2 = ["IpAddress", "AsnDescription", "CountryCode"]
    if "UserAgent" in data.columns:
        group_cols1.append("UserAgent")
    group_cols = group_cols1 + group_cols2
    all_data = (
        data[[ip_col]]  # the property and the column we want
        .dropna()
        .drop_duplicates()  # drop duplicates
        .pipe(
            (get_geoip_whois, "data"), geo_lookup=geoip, ip_col=ip_col
        )  # get geoip and whois
        .drop(columns=["TimeGenerated", "Type"], errors="ignore")
        .merge(data, left_on="IpAddress", right_on=ip_col)
    )
    for col in group_cols:
        if col not in all_data.columns:
            group_cols.pop(group_cols.index(col))
    ip_summary = all_data.groupby(group_cols).agg(
        Count=pd.NamedAgg("Operation", "count"),
        FirstOperation=pd.NamedAgg("TimeGenerated", "min"),
        LastOperation=pd.NamedAgg("TimeGenerated", "max"),
    )

    return ip_summary, all_data
