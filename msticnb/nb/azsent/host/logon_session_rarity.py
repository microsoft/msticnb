# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Logon sessions rarity analysis."""
from typing import Any, Dict, Iterable, Optional

import pandas as pd
from msticpy.analysis.eventcluster import char_ord_score, dbcluster_events, delim_count
from msticpy.common.timespan import TimeSpan

# pylint: disable=unused-import
from msticpy.init import mp_pandas_accessors  # noqa: F401

try:
    from msticpy import nbwidgets

    if not hasattr(nbwidgets, "SelectItem"):
        raise ImportError("Invalid nbwidgets")
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.nbtools import nbwidgets

from .... import nb_metadata
from ...._version import VERSION
from ....common import (
    MsticnbMissingParameterError,
    nb_display,
    nb_markdown,
    nb_print,
    set_text,
)
from ....notebooklet import NBMetadata, Notebooklet, NotebookletResult

__version__ = VERSION
__author__ = "Ian Hellen"


# Read module metadata from YAML
_CLS_METADATA: NBMetadata
_CELL_DOCS: Dict[str, Any]
_CLS_METADATA, _CELL_DOCS = nb_metadata.read_mod_metadata(__file__, __name__)


# pylint: disable=too-few-public-methods
# Rename this class
class LogonSessionsRarityResult(NotebookletResult):
    """
    Logon Sessions rarity.

    Attributes
    ----------
    process_clusters : pd.DataFrame
        Process clusters based on account, process, commandline and
        showing the an example process from each cluster
    processes_with_cluster : pd.DataFrame
        Merged data with rarity value assigned to each process event.
    session_rarity: pd.DataFrame
        List of sessions with averaged process rarity.

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
        self.description: str = "Windows Host Security Events"

        # Add attributes as needed here.
        # Make sure they are documented in the Attributes section
        # above.
        self.process_clusters: Optional[pd.DataFrame] = None
        self.processes_with_cluster: Optional[pd.DataFrame] = None
        self.session_rarity: Optional[pd.DataFrame] = None


# pylint: enable=too-few-public-methods


# Rename this class
class LogonSessionsRarity(Notebooklet):
    """
    Calculates the relative rarity of logon sessions.

    It clusters the data based on process, command line and account.
    Then calculates the rarity of the process pattern.
    Then returns a result containing a summary of the logon sessions by rarity.

    To see the methods available for the class and result class, run
    cls.list_methods()

    """

    # assign metadata from YAML to class variable
    metadata = _CLS_METADATA
    __doc__ = nb_metadata.update_class_doc(__doc__, metadata)
    _cell_docs = _CELL_DOCS

    def __init__(self, **kwargs):
        """Initialize instance of LogonSessionRarity."""
        super().__init__(**kwargs)
        self.column_map = {}
        self._event_browser = None

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
    ) -> LogonSessionsRarityResult:
        """
        Calculate Logon sessions ordered by process rarity summary.

        Parameters
        ----------
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
        -------
        LogonSessionsRarityResult
            LogonSessionsRarityResult.

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

        if data is None:
            raise MsticnbMissingParameterError("data")

        # Create a result class
        result = LogonSessionsRarityResult(
            notebooklet=self, description=self.metadata.description, timespan=timespan
        )

        self.column_map = _get_column_map(data)
        feat_data, cols = _add_session_features(data=data, column_map=self.column_map)
        result.process_clusters, labeled_events = _cluster_sessions(
            data=feat_data, columns=list(cols.keys())
        )

        (
            result.processes_with_cluster,
            result.session_rarity,
        ) = _merge_cluster_with_procs(
            data=labeled_events,
            clustered_data=result.process_clusters,
            column_map=self.column_map,
        )
        # save the result
        self._last_result = result

        if not self.silent:
            self.list_sessions_by_rarity()
            self.plot_sessions_by_rarity()

        self._event_browser = _create_session_browser(
            summ_data=result.session_rarity,
            data=result.processes_with_cluster,
            column_map=self.column_map,
        )

        nb_markdown("<h3>View the returned results object for more details.</h3>")
        nb_markdown(
            f"Additional methods for this class:<br>{'<br>'.join(self.list_methods())}"
        )
        return self._last_result

    def list_sessions_by_rarity(self):
        """Display sessions by process rarity."""
        if self.check_valid_result_data("session_rarity"):
            nb_display(
                self._last_result.session_rarity.sort_values(
                    "MeanRarity", ascending=False
                ).style.bar(subset=["MeanRarity"], color="#d65f5f")
            )

    def plot_sessions_by_rarity(self):
        """Display timeline plot of processes by rarity."""
        if self.check_valid_result_data("processes_with_cluster"):
            data = self._last_result.processes_with_cluster
            acct_col = self.column_map.get(COL_ACCT)
            data.mp_plot.timeline_values(
                title="Processes with relative rarity score grouped by Account",
                y="Rarity",
                group_by=acct_col,
                height=600,
                kind=["vbar", "circle"],
                source_columns=[self.column_map[COL_PROC], self.column_map[COL_CMD]],
            )

    def process_tree(
        self, account: Optional[str] = None, session: Optional[str] = None
    ):
        """
        View a process tree of current session.

        Parameters
        ----------
        account : Optional[str], optional
            The account name to view, by default None
        session : Optional[str], optional
            The logon session to view, by default None

        """
        if self.check_valid_result_data("processes_with_cluster"):
            if (not account and not session) or account == "all":
                self._last_result.processes_with_cluster.mp_plot.process_tree(
                    legend_col="Rarity"
                )
                return
            if account:
                acct_col = self.column_map.get(COL_ACCT)
                data = self._last_result.processes_with_cluster
                data = data[data[acct_col] == account]
                proc_tree_data = data.mp.build_process_tree()
                proc_tree_data["Rarity"] = pd.to_numeric(
                    proc_tree_data["Rarity"], errors="coerce"
                ).fillna(0)
                proc_tree_data.mp_plot.process_tree(legend_col="Rarity")
                return
            session = session or self._event_browser.value
            sess_col = self.column_map.get(COL_SESS)
            data = self._last_result.processes_with_cluster
            data = data[data[sess_col] == session]
            proc_tree_data = data.mp.build_process_tree()
            proc_tree_data["Rarity"] = pd.to_numeric(
                proc_tree_data["Rarity"], errors="coerce"
            ).fillna(0)
            proc_tree_data.mp_plot.process_tree(legend_col="Rarity")

    def browse_events(self):
        """Browse the events by logon session."""
        if self.check_valid_result_data("processes_with_cluster"):
            return self._event_browser
        return None


# %
# Get the column mapping for the data
COL_ACCT = "acct"
COL_TS = "timestamp"
COL_PROC = "process_name"
COL_CMD = "command"
COL_SESS = "sess"
COL_PID = "pid"


def _find_column(data, column_opts, default=None):
    for col in column_opts:
        if col in data.columns:
            return col
    return default


def _get_column_map(data):
    return {
        COL_ACCT: _find_column(data, ["Account", "SubjectLogonName", "acct", "uid"]),
        COL_TS: _find_column(data, ["TimeGenerated", "EventStartTime", "TimeStamp"]),
        COL_CMD: _find_column(data, ["CommandLine", "cmd"]),
        COL_PROC: _find_column(data, ["NewProcessName", "exe"]),
        COL_SESS: _find_column(data, ["SubjectLogonId", "ses"]),
        COL_PID: _find_column(data, ["NewProcessId", "pip"]),
    }


CMD_LINE_TOKS = "CommandlineTokensFull"
PATH_SCORE = "PathScore"
ACCT_NUM = "AccountNum"
SYS_SESS = "IsSystemSession"
CLUSTER_COLUMNS = [CMD_LINE_TOKS, PATH_SCORE, ACCT_NUM, SYS_SESS]


# %%
def _add_session_features(data, column_map: Dict[str, str]):
    """Create clustering features."""
    nb_markdown(f"Input data: {len(data)} events")
    nb_print("Extracting features...", end="")
    data = data.copy()

    cluster_cols = {}
    proc_name = column_map.get(COL_PROC)
    if proc_name:
        cluster_cols[PATH_SCORE] = proc_name
        data[PATH_SCORE] = data.apply(lambda x: char_ord_score(x[proc_name]), axis=1)
        nb_print(".", end="")
    cmd_line = column_map.get("command", "CommandLine")
    if cmd_line:
        cluster_cols[CMD_LINE_TOKS] = cmd_line
        data[CMD_LINE_TOKS] = data.apply(lambda x: delim_count(x[cmd_line]), axis=1)
        nb_print(".", end="")
    acct = column_map.get("account", "Account")
    if acct:
        cluster_cols[ACCT_NUM] = acct
        data[ACCT_NUM] = data.apply(lambda x: char_ord_score(x[acct]), axis=1)
        nb_print(".", end="")
    sess = column_map.get("logon_id", "SubjectLogonId")
    if sess:
        cluster_cols[SYS_SESS] = sess
        data[SYS_SESS] = data[sess].isin(["0x3e7", "-1"])
    nb_markdown("done.")
    return data, cluster_cols


def _cluster_sessions(data, columns=None):
    """Cluster data using DBSCAN."""
    # you might need to play around with the max_cluster_distance parameter.
    # decreasing this gives more clusters.
    columns = columns or CLUSTER_COLUMNS
    nb_markdown("Clustering...")
    (clus_events, db_cluster, _) = dbcluster_events(
        data=data,
        cluster_columns=columns,
        max_cluster_distance=0.0001,
    )
    labeled_events = data
    labeled_events["ClusterId"] = db_cluster.labels_
    nb_markdown("done")
    nb_markdown(f"Number of input events: {len(data)}")
    nb_markdown(
        f"Number of clusters: {len(clus_events[clus_events['ClusterId'] != -1])}"
    )
    nb_markdown(
        "Number of unique (unclustered) events: "
        f"{len(clus_events[clus_events['ClusterId'] == -1])}"
    )
    return clus_events, labeled_events


def _merge_cluster_with_procs(data, clustered_data, column_map):
    """Merge clustered data with original."""
    nb_markdown("Merging with source data and computing rarity...")

    # Join the clustered results back to the original process frame
    noise_points = data[data["ClusterId"] == -1].assign(ClusterId=-1, ClusterSize=1)
    clusters = data[data["ClusterId"] != -1].merge(
        clustered_data[["ClusterId", "ClusterSize"]],
        on="ClusterId",
    )
    procs_with_cluster = pd.concat([clusters, noise_points])
    # Compute Process pattern Rarity = inverse of cluster size
    procs_with_cluster["Rarity"] = 1 / procs_with_cluster["ClusterSize"]

    # count the number of processes for each logon ID
    sess = column_map.get(COL_SESS, "SubjectLogonId")
    acct = column_map.get(COL_ACCT, "Account")
    timestamp = column_map.get(COL_TS, "TimeGenerated")
    session_rarity = (
        procs_with_cluster.groupby([acct, sess])
        .agg(
            MeanRarity=pd.NamedAgg("Rarity", "mean"),
            MaxRarity=pd.NamedAgg("Rarity", "max"),
            ProcessCount=pd.NamedAgg(timestamp, "count"),
        )
        .reset_index()
    )

    nb_markdown("done")
    # Display the results
    nb_markdown("<br><hr>Sessions ordered by process rarity", "large, bold")
    nb_markdown("Higher score indicates higher number of unusual processes")

    return procs_with_cluster, session_rarity


def _create_session_browser(summ_data, data, column_map):
    browse_cols = [
        column_map[COL_ACCT],
        column_map[COL_TS],
        column_map[COL_SESS],
        column_map[COL_PID],
        column_map[COL_PROC],
        column_map[COL_CMD],
    ]
    if "ParentProcessName" in data:
        browse_cols.append("ParentProcessName")
    browse_cols.append("Rarity")

    item_dict = {
        f"{item[1]} - {item[0]}, mean rarity: {item[2]}": item[0]
        for item in summ_data[
            [column_map[COL_SESS], column_map[COL_ACCT], "MeanRarity"]
        ].values
    }

    def show_events(logon_id):
        return (
            data[browse_cols]
            .query(f"{column_map[COL_SESS]} == '{logon_id}'")
            .sort_values(column_map[COL_TS])
        )

    return nbwidgets.SelectItem(item_dict=item_dict, action=show_events)
