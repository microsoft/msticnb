# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklet for Account Summary."""
from enum import Flag, auto
from typing import Any, Callable, Dict, Iterable, Optional, Union

import attr
import pandas as pd
from bokeh.models import LayoutDOM
from IPython.display import HTML

from msticpy.nbtools import nbdisplay, nbwidgets

from .... import nb_metadata
from ...._version import VERSION
from ....common import (
    MsticnbMissingParameterError,
    TimeSpan,
    nb_data_wait,
    nb_markdown,
    set_text,
)
from ....notebooklet import NBMetadata, Notebooklet, NotebookletResult

__version__ = VERSION
__author__ = "Ian Hellen"


# Read module metadata from YAML
_CLS_METADATA: NBMetadata
_CELL_DOCS: Dict[str, Any]
_CLS_METADATA, _CELL_DOCS = nb_metadata.read_mod_metadata(__file__, __name__)


class AccountType(Flag):
    """Account types."""

    AzureActiveDirectory = auto()
    AzureActivity = auto()
    Office365 = auto()
    Windows = auto()
    Linux = auto()
    Azure = AzureActiveDirectory | AzureActivity | Office365

    def in_list(self, acct_types: Iterable[Union["AccountType", str]]):
        """Is the current value in the `acct_types` list."""
        for acct_type in acct_types:
            if isinstance(acct_type, str):
                acct_type = AccountType[acct_type]
            if self & acct_type:
                return True
        return False


# pylint: disable=too-few-public-methods
# Rename this class
@attr.s(auto_attribs=True)
class AccountSummaryResult(NotebookletResult):
    """
    Template Results.

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

    """

    description: str = "Account Activity Summary"

    account_activity: pd.DataFrame = None
    account_selector: nbwidgets.SelectItem = None
    related_alerts: pd.DataFrame = None
    alert_timeline: LayoutDOM = None
    related_bookmarks: pd.DataFrame = None


# pylint: enable=too-few-public-methods


# Rename this class
class AccountSummary(Notebooklet):
    """
    TODO.

    Detailed description of things this notebooklet does:

    - Fetches all events from XYZ
    - Plots interesting stuff
    - Returns extended metadata about the thing

    Document the options that the Notebooklet takes, if any,
    Use these control which parts of the notebooklet get run.

    """

    # assign metadata from YAML to class variable
    metadata = _CLS_METADATA
    __doc__ = nb_metadata.update_class_doc(__doc__, metadata)
    _cell_docs = _CELL_DOCS

    ACCOUNT_TYPE = AccountType

    # @set_text decorator will display the title and text every time
    # this method is run.
    # The key value refers to an entry in the `output` section of
    # the notebooklet yaml file.
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
        Return XYZ summary.

        Parameters
        ----------
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
        account_types : Iterable[AccountType], Optional
            A list of account types to search for, by default
            all types.

        Returns
        -------
        TemplateResult
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
        result = AccountSummaryResult()
        result.description = self.metadata.description
        result.timespan = timespan
        self.timespan = timespan
        acc_types = kwargs.get("account_types")
        if acc_types is None:
            acc_types = AccountType.__members__

        # Search for events for specified account types
        acct_found = _get_matching_accounts(
            self.query_provider,
            account=value,
            timespan=timespan,
            account_types=acc_types,
        )

        acct_activity_df = _combine_acct_dfs(acct_found)
        result.account_activity = acct_activity_df
        action_func = _create_display_callback(
            self.query_provider, result, acct_activity_df, timespan, options
        )
        result.account_selector = _get_account_selector(
            acct_activity_df, action_func, bool(self.silent)
        )

        # Assign the result to the _last_result attribute
        # so that you can get to it without having to re-run the operation
        self._last_result = result  # pylint: disable=attribute-defined-outside-init

        return self._last_result

    def _get_selected_account(self):
        if (
            self._last_result is not None
            and self._last_result.account_selector is not None
        ):
            return self._last_result.account_selector.value.split(" ")
        return "", ""

    def find_additional_data(self) -> pd.DataFrame:
        """
        Find additional data for the selected account.

        Returns
        -------
        pd.DataFrame
            Results with expanded columns.

        """
        acct, source = self._get_selected_account()
        if source == "LinuxHostLogon":
            _get_linux_add_activity(acct)
        if source == "WindowsHostLogon":
            _get_windows_add_activity(acct)
        if source in ["AADLogon", "AzureActivity", "O365Activity"]:
            _get_azure_add_activity(acct)


# pylint: disable=no-member
# %%
def _get_matching_accounts(qry_prov, timespan, account, account_types):
    """Get Account Activity for `account` in `timespan`."""
    account_dfs = {}
    rec_count = 0
    if AccountType.AzureActiveDirectory.in_list(account_types):
        nb_data_wait("AADSignin")
        summarize_clause = """
        | summarize arg_max(TimeGenerated, *) by UserPrincipalName, OperationName,
        Identity, IPAddress, tostring(LocationDetails)
        | project TimeGenerated, UserPrincipalName, Identity, IPAddress, LocationDetails
        """

        aad_signin_df = qry_prov.Azure.list_aad_signins_for_account(
            timespan, account_name=account, add_query_items=summarize_clause
        )
        rec_count += len(aad_signin_df)
        nb_markdown(f"  {len(aad_signin_df)} records in AAD")
        account_dfs[AccountType.AzureActiveDirectory] = aad_signin_df

    if AccountType.AzureActiveDirectory.in_list(account_types):
        nb_data_wait("AzureActivity")
        # Azure Activity
        summarize_clause = """
        | summarize arg_max(TimeGenerated, *) by Caller, OperationName,
        CallerIpAddress, ResourceId
        | project TimeGenerated, UserPrincipalName=Caller, IPAddress=CallerIpAddress"""

        azure_activity_df = qry_prov.Azure.list_azure_activity_for_account(
            timespan, account_name=account, add_query_items=summarize_clause
        )
        nb_markdown(f"  {len(azure_activity_df)} records in Azure Activity")
        account_dfs[AccountType.AzureActivity] = azure_activity_df

    if AccountType.Office365.in_list(account_types):
        nb_data_wait("Office365Activity")
        # Office Activity
        summarize_clause = """
        | project TimeGenerated, UserId = tolower(UserId), OfficeWorkload, Operation,
        ClientIP, UserType
        | summarize arg_max(TimeGenerated, *) by UserId, OfficeWorkload, ClientIP
        | order by TimeGenerated desc
        """

        o365_activity_df = qry_prov.Office365.list_activity_for_account(
            timespan, account_name=account, add_query_items=summarize_clause
        )
        rec_count += len(o365_activity_df)
        nb_markdown(f"  {len(o365_activity_df)} records in Office Activity")
        account_dfs[AccountType.Office365] = o365_activity_df

    if AccountType.Windows.in_list(account_types):
        nb_data_wait("Windows Logon activity")
        # Windows Host
        summarize_clause = """
        | extend LogonStatus = iff(EventID == 4624, "success", "failed")
        | project TimeGenerated, TargetUserName, TargetDomainName, Computer,
        LogonType, SubjectUserName, SubjectDomainName, TargetUserSid, EventID,
        IpAddress, LogonStatus
        | summarize arg_max(TimeGenerated, *) by
        TargetUserName, TargetDomainName, LogonType, Computer, LogonStatus
        """

        win_logon_df = qry_prov.WindowsSecurity.list_logon_attempts_by_account(
            timespan, account_name=account, add_query_items=summarize_clause
        )
        rec_count += len(win_logon_df)
        nb_markdown(f"  {len(win_logon_df)} records in Windows logon data")
        account_dfs[AccountType.Windows] = win_logon_df

    if AccountType.Linux.in_list(account_types):
        nb_data_wait("Linux logon activity")
        # Linux host
        summarize_clause = """
        | summarize arg_max(TimeGenerated, *) by LogonType, SourceIP, Computer,
          LogonResult
        """

        linux_logon_df = qry_prov.LinuxSyslog.list_logons_for_account(
            timespan, account_name=account, add_query_items=summarize_clause
        )
        rec_count += len(linux_logon_df)
        nb_markdown(f"  {len(linux_logon_df)} records in Linux logon data")
        account_dfs[AccountType.Linux] = linux_logon_df

    nb_markdown(f"Found {rec_count} total records...")

    return account_dfs


# pylint: disable=no-member


def _combine_acct_dfs(acct_dfs: Dict[AccountType, pd.DataFrame]):
    """Combine to single Dataframe for display."""
    lx_df = (
        acct_dfs[AccountType.Linux][["AccountName", "TimeGenerated"]]
        .groupby("AccountName")
        .max()
        .reset_index()
        .assign(Source="LinuxHostLogon")
    )

    win_df = (
        acct_dfs[AccountType.Windows][["TargetUserName", "TimeGenerated"]]
        .groupby("TargetUserName")
        .max()
        .reset_index()
        .rename(columns={"TargetUserName": "AccountName"})
        .assign(Source="WindowsHostLogon")
    )

    o365_df = (
        acct_dfs[AccountType.Office365][["UserId", "TimeGenerated"]]
        .groupby("UserId")
        .max()
        .reset_index()
        .rename(columns={"UserId": "AccountName"})
        .assign(Source="O365Activity")
    )

    aad_df = (
        acct_dfs[AccountType.AzureActiveDirectory][
            ["UserPrincipalName", "TimeGenerated"]
        ]
        .groupby("UserPrincipalName")
        .max()
        .reset_index()
        .rename(columns={"UserPrincipalName": "AccountName"})
        .assign(Source="AADLogon")
    )

    azure_df = (
        acct_dfs[AccountType.AzureActivity][["UserPrincipalName", "TimeGenerated"]]
        .groupby("UserPrincipalName")
        .max()
        .reset_index()
        .rename(columns={"UserPrincipalName": "AccountName"})
        .assign(Source="AzureActivity")
    )

    return pd.concat([lx_df, win_df, o365_df, aad_df, azure_df])


# %%
# Display account activity for selected account
def _display_acct_activity(
    selected_item: str, acct_activity_df: pd.DataFrame
) -> Iterable[Any]:
    """Return list of display objects for Select list display."""
    acct, source = selected_item.split(" ") if selected_item else "", ""
    outputs = []
    title = HTML(f"<b>{acct} (source: {source})</b>")
    outputs.append(title)

    outputs.append(
        acct_activity_df[
            (acct_activity_df["Source"] == source)
            & (acct_activity_df["AccountName"] == acct)
        ].sort_values("TimeGenerated", ascending=True)
    )
    return outputs


def _get_select_acct_dict(acc_activity_df: pd.DataFrame) -> Dict[str, str]:
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

    return {item[0]: item[1] for item in acc_activity_df.apply(format_tuple, axis=1)}


def _get_account_selector(
    acc_activity_df: pd.DataFrame,
    _acct_activity_action: Callable[[str], Iterable[Any]],
    silent: bool,
):
    """Build and return the Account Select list."""
    accts_dict = _get_select_acct_dict(acc_activity_df)
    return nbwidgets.SelectString(
        item_dict=accts_dict,
        auto_display=not silent,
        description="Select an account to explore",
        action=_acct_activity_action,
        height="200px",
        width="100%",
    )


def _create_display_callback(
    qry_prov, acct_activity_df, result, timespan, options
) -> Callable[[str], Iterable[Any]]:
    """Create closure for display_acct callback."""

    def display_account(selected_item: str):
        # Add default activity
        outputs = list(_display_acct_activity(selected_item, acct_activity_df))

        account_name, _ = selected_item.split(" ")
        if "get_alerts" in options:
            related_alerts = _get_related_alerts(qry_prov, account_name, timespan)
            result.related_alerts = related_alerts
            outputs.append(_get_related_alerts_summary(related_alerts))
            result.alert_timeline = _get_alerts_timeline(related_alerts)
            outputs.append(result.alert_timeline)
        if "get_bookmarks" in options:
            related_bkmarks = _get_related_bookmarks(qry_prov, account_name, timespan)
            result.related_bookmarks = related_bkmarks
            outputs.append(_get_related_alerts_summary(related_alerts))

    return display_account


# %%
# Display Alert Details
def _get_related_alerts(
    qry_prov, account_name: str, timespan: TimeSpan
) -> pd.DataFrame:
    nb_data_wait("Alerts")
    return qry_prov.SecurityAlert.list_related_alerts(
        timespan, account_name=account_name
    )


def _get_related_bookmarks(
    qry_prov, account_name: str, timespan: TimeSpan
) -> pd.DataFrame:
    nb_data_wait("Bookmarks")
    return qry_prov.AzureSentinel.list_bookmarks_for_entity(
        timespan, entity_id=account_name
    )


def _get_alerts_timeline(related_alerts: pd.DataFrame) -> LayoutDOM:
    """Return alert timeline."""
    return nbdisplay.display_timeline(
        data=related_alerts, title="Alerts", source_columns=["AlertName"], height=200
    )


def _get_related_alerts_summary(related_alerts: pd.DataFrame):
    alert_items = (
        related_alerts[["AlertName", "TimeGenerated"]]
        .groupby("AlertName")
        .TimeGenerated.agg("count")
        .to_dict()
    )
    output = []
    if alert_items:
        output.append(
            f"<b>Found {len(alert_items)} different alert types "
            f"related to this account</b>"
        )
        for (name, count) in alert_items.items():
            output.append(f"- {name}, # Alerts: {count}")
    else:
        output.append("<b>No alerts for this account</b>")
    return HTML("<br>".join(output))


def _get_related_bkmks_summary(related_bookmarks: pd.DataFrame):
    bookmarks = related_bookmarks.apply(
        lambda x: (f"{x.BookmarkName} {x.Tags}  {x.TimeGenerated}", x.BookmarkId),
        axis=1,
    ).tolist()
    output = []
    if bookmarks:
        output.append(
            f"<b>Found {len(bookmarks)} different bookmarks "
            f"related to this account</b>"
        )
        for (desc, bm_id) in bookmarks:
            output.append(f"- {desc}, BookmarkId: {bm_id}")
    else:
        output.append("No bookmarks for this account</b>")
    return HTML("<br>".join(output))


# %%
# Get Azure/AAD Details
def _get_linux_add_activity(acct):
    return acct


# %%
# Get Azure/AAD Details
def _get_windows_add_activity(acct):
    return acct


# %%
# Get Azure/AAD Details
def _get_azure_add_activity(acct):
    return acct
