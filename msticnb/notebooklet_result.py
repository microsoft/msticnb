# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklet Result base classes."""
import inspect
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from bokeh.models import LayoutDOM
from msticpy.common.timespan import TimeSpan

from ._version import VERSION
from .common import show_bokeh
from .data_viewers import DFViewer

__version__ = VERSION
__author__ = "Ian Hellen"


# pylint: disable=too-few-public-methods
class NotebookletResult(DFViewer):
    """Base result class."""

    _TITLE_STYLE = "color:black; background-color:lightgray; padding:5px;"

    def __init__(
        self,
        description: Optional[str] = None,
        timespan: Optional[TimeSpan] = None,
        notebooklet: Optional[Any] = None,  # type: ignore
    ):
        """
        Create new Notebooklet result instance.

        Parameters
        ----------
        description : Optional[str], optional
            Result description, by default None
        timespan : Optional[TimeSpan], optional
            TimeSpan for the results, by default None
        notebooklet : Optional[Notebooklet], optional
            Originating notebooklet, by default None

        """
        self.description = description or self.__class__.__qualname__
        self.timespan = timespan
        self.notebooklet = notebooklet
        self._attribute_desc: Dict[str, Tuple[str, str]] = {}

        # Populate the `_attribute_desc` dictionary on init.
        self._populate_attr_desc()

    def __str__(self):
        """Return string representation of object."""
        return "\n".join(
            f"{name}: {self._str_repr(val)}"
            for name, val in self.__dict__.items()
            if not name.startswith("_") and val is not None
        )

    @staticmethod
    def _str_repr(obj):
        if isinstance(obj, pd.DataFrame):
            return f"DataFrame: {len(obj)} rows"
        if isinstance(obj, LayoutDOM):
            return "Bokeh plot"
        return str(obj)

    # pylint: disable=unsubscriptable-object, no-member
    def _repr_html_(self):
        """Display HTML represention for notebook."""
        attrib_lines = []
        for name, val in self.__dict__.items():
            if name.startswith("_") or val is None:
                continue
            attr_desc = ""
            attr_type, attr_text = self._attribute_desc.get(
                name, (None, None)
            )  # type: ignore
            if attr_text:
                attr_desc += f"{attr_text}"
            if attr_type:
                attr_desc += f"&nbsp;Type: [{attr_type}]"
            attrib_lines.extend(
                [
                    f"<h3 style='{self._TITLE_STYLE}'>{name}</h3>",
                    f"{attr_desc}<br>{self._html_repr(val)}<hr>",
                ]
            )
        return "".join(attrib_lines)

    # pylint: enable=unsubscriptable-object, no-member

    # pylint: disable=protected-access
    @staticmethod
    def _html_repr(obj):
        if isinstance(obj, pd.DataFrame):
            suffix = f"<br>(showing top 5 of {len(obj)} rows)" if len(obj) > 5 else ""
            return obj.head(5)._repr_html_() + suffix
        if isinstance(obj, LayoutDOM):
            show_bokeh(obj)
        if hasattr(obj, "_repr_html_"):
            return obj._repr_html_()
        return str(obj).replace("\n", "<br>").replace(" ", "&nbsp;")

    # pylint: enable=protected-access

    def __getattr__(self, name):
        """Proxy attributes of the notebooklet member."""
        if self.notebooklet:
            return getattr(self.notebooklet, name)
        raise AttributeError(f"{self.__class__} has no attribute '{name}'")

    def _populate_attr_desc(self):
        indent = " " * 4
        in_attribs = False
        attr_name = None
        attr_type = None
        attr_dict = {}
        attr_lines = []
        doc_str = inspect.cleandoc(self.__doc__)
        for line in doc_str.split("\n"):
            if line.strip() == "Attributes":
                in_attribs = True
                continue
            if (
                line.strip() == "-" * len("Attributes")
                or not in_attribs
                or not line.strip()
            ):
                continue
            if not line.startswith(indent):
                # if existing attribute, add to dict
                if attr_name:
                    attr_dict[attr_name] = attr_type, " ".join(attr_lines)
                if ":" in line:
                    attr_name, attr_type = [item.strip() for item in line.split(":")]
                else:
                    attr_name = line.strip()
                    attr_type = "object"
                attr_lines = []
            else:
                attr_lines.append(line.strip())
        attr_dict[attr_name] = attr_type, " ".join(attr_lines)
        if "timespan" not in attr_dict:
            attr_dict["timespan"] = (
                "TimeSpan",
                "Time span for the queried results data.",
            )
        if "notebooklet" not in attr_dict:
            attr_dict["notebooklet"] = (
                "Notebooklet",
                "The notebooklet instance that created this result.",
            )
        # pylint: disable=no-member
        self._attribute_desc.update(attr_dict)  # type: ignore
        # pylint: enable=no-member

    @property
    def properties(self):
        """Return names of all properties."""
        return [
            name
            for name, val in self.__dict__.items()
            if val is not None and not name.startswith("_")
        ]

    def prop_doc(self, name) -> Tuple[str, str]:
        """Get the property documentation for the property."""
        # pylint: disable=unsupported-membership-test, unsubscriptable-object
        if name in self._attribute_desc:
            return self._attribute_desc[name]
        # pylint: enable=unsupported-membership-test, unsubscriptable-object
        raise KeyError(f"Unknown property {name}.")

    def data_properties(self, empty: bool = False) -> List[str]:
        """Return list of attributes with populated data."""
        return [
            attr
            for attr, val in vars(self).items()
            if isinstance(val, pd.DataFrame) and (empty or not val.empty)
        ]

    def vis_properties(self) -> List[str]:
        """Return list of properties with visualizations."""
        return [attr for attr, val in vars(self).items() if isinstance(val, LayoutDOM)]
