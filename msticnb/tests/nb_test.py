# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklet for Host Summary."""
from typing import Any, Optional, Iterable, Dict

import attr
import pandas as pd
from msticpy.nbtools import entities

from ..common import TimeSpan, nb_print, set_text
from ..notebooklet import Notebooklet, NotebookletResult, NBMetaData
from .. import nb_metadata
from .._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


_CLS_METADATA: NBMetaData
_CELL_DOCS: Dict[str, Any]
_CLS_METADATA, _CELL_DOCS = nb_metadata.read_mod_metadata(__file__, __name__)


# pylint: disable=too-few-public-methods
@attr.s(auto_attribs=True)
class TstSummaryResult(NotebookletResult):
    """Test Results."""

    host_entity: entities.Host = None
    related_alerts: pd.DataFrame = None
    related_bookmarks: pd.DataFrame = None
    default_property: pd.DataFrame = None
    optional_property: pd.DataFrame = None


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
        self._last_result = TstSummaryResult()
        self._last_result.description = self.metadata.description
        self._last_result.timespan = timespan

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
