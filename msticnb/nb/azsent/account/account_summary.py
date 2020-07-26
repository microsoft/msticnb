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
    nb_display,
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


# pylint: disable=too-few-public-methods, too-many-instance-attributes
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

    """

    description: str = "Account Activity Summary"

    account_activity: pd.DataFrame = None
    account_selector: nbwidgets.SelectItem = None
    related_alerts: pd.DataFrame = None
    alert_timeline: LayoutDOM = None
    related_bookmarks: pd.DataFrame = None
    host_logons: pd.DataFrame = None
    host_logon_summary: pd.DataFrame = None
    azure_activity: pd.DataFrame = None
    azure_activity_summary: pd.DataFrame = None
    azure_timeline_by_provider: LayoutDOM = None
    account_timeline_by_ip: LayoutDOM = None
    azure_timeline_by_operation: LayoutDOM = None


# pylint: enable=too-few-public-methods


class AccountSummary(Notebooklet):
    """
    Retrieves account summary for the selected account.

    Searches for matches for the account name in Active Directory,
    Windows and Linux host logs.
    If one or more matches are found it will return a selection
    widget that you can use to pick the account

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
        result.account_selector = _get_account_selector(acct_activity_df, action_func)
        if acct_activity_df.empty:
            nb_markdown("No accounts matching that name.")
        elif len(acct_activity_df) == 1:
            acct_row = acct_activity_df.iloc[0]
            action_func(f"{acct_row.Account} {acct_row.Source}")
        else:
            nb_display(result.account_selector)

        # Assign the result to the _last_result attribute
        # so that you can get to it without having to re-run the operation
        self._last_result = result  # pylint: disable=attribute-defined-outside-init

        return self._last_result

    def browse_accounts(self) -> nbwidgets.SelectItem:
        """Return the accounts browser/viewer."""
        if (
            self._last_result is not None
            and self._last_result.account_activity is not None
            and not self._last_result.account_activity.empty
        ):
            return self._last_result.account_selector
        return None

    def browse_alerts(self) -> nbwidgets.SelectAlert:
        """Return alert browser/viewer."""
        if (
            self._last_result is not None
            and self._last_result.related_alerts is not None
            and not self._last_result.related_alerts.empty
        ):
            return nbwidgets.SelectAlert(
                alerts=self._last_result.related_alerts, action=nbdisplay.format_alert
            )
        return None

    def browse_bookmarks(self) -> nbwidgets.SelectItem:
        """Return bookmark browser/viewer."""
        if (
            self._last_result is not None
            and self._last_result.related_bookmarks is not None
            and not self._last_result.related_bookmarks.empty
        ):
            return _get_bookmark_select(self._last_result.related_bookmarks)
        return None

    @set_text(docs=_CELL_DOCS, key="find_additional_data")
    def find_additional_data(self) -> pd.DataFrame:
        """
        Find additional data for the selected account.

        Returns
        -------
        pd.DataFrame
            Results with expanded columns.

        """
        if self._last_result is None:
            print(
                "Please use 'run()' to fetch the data before using this method.",
                "\nThen select an account to examine and run 'find_additional_data()'",
            )
            return
        acct, source = self._get_selected_account()
        if not acct or not source:
            print("Please use select an account before using this method.")
            return

        if source == "LinuxHostLogon":
            self._last_result.host_logons = _get_linux_add_activity(
                self.query_provider, acct, self.timespan
            )
            self._last_result.host_logon_summary = _summarize_host_activity(
                self._last_result.host_logons
            )
            self._last_result.account_timeline_by_ip = _create_host_timeline(
                self._last_result.host_logons, self.silent
            )
        if source == "WindowsHostLogon":
            self._last_result.host_logons = _get_windows_add_activity(
                self.query_provider, acct, self.timespan
            )
            self._last_result.host_logon_summary = _summarize_host_activity(
                self._last_result.host_logons
            )
            self._last_result.account_timeline_by_ip = _create_host_timeline(
                self._last_result.host_logons, self.silent
            )
        if source in ["AADSignin", "AzureActivity", "O365Activity"]:
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

    def _get_selected_account(self):
        if (
            self._last_result is not None
            and self._last_result.account_selector is not None
        ):
            return self._last_result.account_selector.value.split(" ")
        return "", ""


# pylint: disable=no-member
# %%
@set_text(docs=_CELL_DOCS, key="get_matching_accounts")
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
        .assign(Source="AADSignin")
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
    acc_activity_df: pd.DataFrame, _acct_activity_action: Callable[[str], Iterable[Any]]
):
    """Build and return the Account Select list."""
    accts_dict = _get_select_acct_dict(acc_activity_df)
    return nbwidgets.SelectItem(
        item_dict=accts_dict,
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
            outputs.append(_get_related_bkmks_summary(related_bkmarks))

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
        data=related_alerts, title="Alerts", source_columns=["AlertName"], height=300
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
# Utility functions
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
        return bookmarks_df[bookmarks_df["BookmarkId"] == bookmark_id].iloc[0].T

    return nbwidgets.SelectItem(
        item_dict=opts, action=display_bookmark, height="200px", width="100%"
    )


# %%
# Get Linux logon activity
def _get_linux_add_activity(qry_prov, acct, timespan):
    nb_data_wait("LinuxSyslog")
    return qry_prov.LinuxSyslog.list_logons_for_account(timespan, account_name=acct)


@set_text(docs=_CELL_DOCS, key="summarize_host_activity")
def _summarize_host_activity(all_logons: pd.DataFrame):
    """Summarize logon activity on win or linux host."""
    summary = all_logons.groupby("Computer").agg(
        TotalLogons=pd.NamedAgg(column="Computer", aggfunc="count"),
        FailedLogons=pd.NamedAgg(
            column="LogonResult", aggfunc=lambda x: x.value_counts().to_dict()
        ),
        IPAddresses=pd.NamedAgg(
            column="SourceIP", aggfunc=lambda x: x.unique().tolist()
        ),
        LogonTypeCount=pd.NamedAgg(
            column="LogonType", aggfunc=lambda x: x.value_counts().to_dict()
        ),
        FirstLogon=pd.NamedAgg(column="TimeGenerated", aggfunc="min"),
        LastLogon=pd.NamedAgg(column="TimeGenerated", aggfunc="max"),
    )
    nb_display(summary)
    return summary


@set_text(docs=_CELL_DOCS, key="create_host_timeline")
def _create_host_timeline(all_logons: pd.DataFrame, silent: bool = False):
    return nbdisplay.display_timeline(
        data=all_logons,
        group_by="SourceIP",
        source_columns=["Computer", "LogonResult", "LogonType"],
        title="Timeline of Logons by source IP address",
        hide=silent,
    )


# %%
# Get Windows logon activity
def _get_windows_add_activity(qry_prov, acct, timespan):
    nb_data_wait("WindowsSecurity")
    ext_logon_result = (
        "| extend LogonResult = iff(EventID == 4624, 'Success', 'Failed')"
    )
    return qry_prov.WindowsSecurity.list_logon_attempts_by_account(
        timespan, account_name=acct, add_query_items=ext_logon_result
    )


# %%
# Get Azure/AAD/Office activity
def _get_azure_add_activity(qry_prov, acct, timespan):
    """Get Azure additional data for account."""
    nb_data_wait("AADSignin")
    aad_sum_qry = """
        | extend UserPrincipalName=tolower(UserPrincipalName)
        | project-rename Operation=OperationName, AppResourceProvider=AppDisplayName
    """
    aad_logons = qry_prov.Azure.list_aad_signins_for_account(
        timespan, account_name=acct, add_query_items=aad_sum_qry
    )

    nb_data_wait("AzureActivity")
    az_sum_qry = """
        | extend UserPrincipalName=tolower(Caller)
        | project-rename IPAddress=CallerIpAddress, Operation=OperationName,
        AppResourceProvider=ResourceProvider
    """
    az_activity = qry_prov.Azure.list_azure_activity_for_account(
        timespan, account_name=acct, add_query_items=az_sum_qry
    )

    nb_data_wait("Office365Activity")
    o365_sum_qry = """
        | extend UserPrincipalName=tolower(UserId)
        | project-rename IPAddress=ClientIP, ResourceId=OfficeObjectId,
        AppResourceProvider=OfficeWorkload
    """
    o365_activity = qry_prov.Office365.list_activity_for_account(
        timespan, account_name=acct, add_query_items=o365_sum_qry
    )

    return pd.concat([aad_logons, az_activity, o365_activity], sort=False)


@set_text(docs=_CELL_DOCS, key="create_az_timelines")
def _create_azure_timelines(az_all_data: pd.DataFrame, silent: bool = False):
    timeline_by_provider = nbdisplay.display_timeline(
        data=az_all_data,
        group_by="AppResourceProvider",
        source_columns=["Operation", "IPAddress", "AppResourceProvider"],
        title="Azure account activity by Provider",
        hide=silent,
    )
    timeline_by_ip = nbdisplay.display_timeline(
        data=az_all_data,
        group_by="IPAddress",
        source_columns=["Operation", "IPAddress", "AppResourceProvider"],
        title="Azure Operations by Source IP",
        hide=silent,
    )
    timeline_by_operation = nbdisplay.display_timeline(
        data=az_all_data,
        group_by="Operation",
        source_columns=["Operation", "IPAddress", "AppResourceProvider"],
        title="Azure Operations by Operation",
        hide=silent,
    )

    return (timeline_by_provider, timeline_by_ip, timeline_by_operation)


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
