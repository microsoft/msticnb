# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklet for Host Summary."""
from typing import Any, Optional, Iterable, Dict

import pandas as pd
from msticpy.nbtools import entities

from msticpy.common.timespan import TimeSpan
from msticnb.common import nb_print, set_text
from msticnb.notebooklet import Notebooklet, NotebookletResult, NBMetadata
from msticnb import nb_metadata
from msticnb._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


_CLS_METADATA: NBMetadata
_CELL_DOCS: Dict[str, Any]
_CLS_METADATA, _CELL_DOCS = nb_metadata.read_mod_metadata(__file__, __name__)


# pylint: disable=too-few-public-methods
class TstSummaryResult(NotebookletResult):
    """Test Results."""

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
        self.host_entity: entities.Host = None
        self.related_alerts: pd.DataFrame = None
        self.related_bookmarks: pd.DataFrame = None
        self.default_property: pd.DataFrame = None
        self.optional_property: pd.DataFrame = None


# pylint: disable=too-few-public-methods
class TstNBSummary(Notebooklet):
    """Test Notebooklet class."""

    metadata = _CLS_METADATA
    __doc__ = nb_metadata.update_class_doc(__doc__, metadata)
    _cell_docs = _CELL_DOCS

    # pylint: disable=too-many-branches
    @set_text(docs=_CELL_DOCS, key="run")  # noqa MC0001
    def run(
        self,
        value: Any = None,
        data: Optional[pd.DataFrame] = None,
        timespan: Optional[TimeSpan] = None,
        options: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> TstSummaryResult:
        """Return host summary data."""
        super().run(
            value=value, data=data, timespan=timespan, options=options, **kwargs
        )

        # pylint: disable=attribute-defined-outside-init
        self._last_result = TstSummaryResult(
            notebooklet=self, description=self.metadata.description, timespan=timespan
        )

        host_entity = entities.Host(HostName="testhost")
        _test_inline_text(host_entity)
        _test_yaml_text(host_entity)
        self._last_result.host_entity = host_entity
        self._last_result.related_alerts = pd.DataFrame()
        self._last_result.related_bookmarks = pd.DataFrame()

        if "default_opt" in self.options:
            self._last_result.default_property = pd.DataFrame()
        if "optional_opt" in self.options:
            self._last_result.optional_property = pd.DataFrame()
        return self._last_result


# %%
# Get IP Information from Heartbeat
@set_text(
    title="Host Entity details",
    hd_level=3,
    text="""
These are the host entity details gathered from Heartbeat
and, if applicable, AzureNetworkAnalytics and Azure management
API.

The data shows OS information, IP Addresses assigned the
host and any Azure VM information available.
""",
    md=True,
)
def _test_inline_text(host_entity):
    nb_print("TestInline")
    nb_print(host_entity)


@set_text(docs=_CELL_DOCS, key="show_host_entity")
def _test_yaml_text(host_entity):
    nb_print("TestYaml")
    nb_print(host_entity)
