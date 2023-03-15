# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Data viewers mixin classes."""
from typing import List, Optional

import numpy as np
import pandas as pd

try:
    from msticpy.nbwidgets import SelectItem
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.nbtools.nbwidgets import SelectItem

from ._version import VERSION
from .common import MsticnbMissingParameterError

__version__ = VERSION
__author__ = "Ian Hellen"


class DFViewer:
    """Mixin class for NotebookletResult."""

    def view_events(
        self,
        summary_cols: Optional[List[str]] = None,
        attrib: Optional[str] = None,
        data: Optional[pd.DataFrame] = None,
        **kwargs,
    ) -> SelectItem:
        """
        Return simple data view for DataFrame/result attribute.

        Parameters
        ----------
        summary_cols : List[str], optional
            [description]
        attrib : Optional[str], optional
            [description], by default None
        data : Optional[pd.DataFrame], optional
            [description], by default None
        kwargs :
            Additional keyword arguments passed to the SelectItem
            widget.

        Returns
        -------
        SelectItem
            Browser for events in DataFrame.

        Raises
        ------
        AttributeError
            Attribute name not in results class.
        TypeError
            Input data or attribute is not a DataFrame
        MsticnbMissingParameterError
            One of `data` or `attrib` parameters must be supplied
        KeyError
            Summary column name specified that isn't in the DataFrame

        """
        if attrib:
            data = getattr(self, attrib, None)
            if data is None:
                raise AttributeError(f"Attribute '{attrib}' not found in this result.")
        if data is None:
            raise MsticnbMissingParameterError("'attrib' or 'data'")
        if not isinstance(data, pd.DataFrame):
            raise TypeError("The 'data' or 'attrib' must be a DataFrame.")
        summary_cols = summary_cols or list(data.columns)[:3]

        missing_cols = [col for col in summary_cols if col not in data.columns]
        if missing_cols:
            raise KeyError(
                f"Column(s) not found in the data: {', '.join(missing_cols)}"
            )
        if "TimeGenerated" in data.columns and "TimeGenerated" not in summary_cols:
            summary_cols = ["TimeGenerated", *summary_cols]

        pd.set_option("display.max_rows", 150)
        sel_item_params = {
            "item_dict": self._create_options(data, columns=summary_cols),
            "action": self._create_view_callback(data),
            "width": "70%",
            "height": "300px",
        }
        sel_item_params.update(kwargs)
        return SelectItem(**sel_item_params)

    @staticmethod
    def _create_view_callback(data):
        def _event_display(index):
            return pd.DataFrame(
                data.loc[index].replace(r"^\s*$", np.nan, regex=True).dropna().T
            )

        return _event_display

    @staticmethod
    def _create_options(data, columns):
        data_dict = data[columns].to_dict(orient="index")
        return {
            " - ".join(str(item) for item in data.values()): idx
            for idx, data in data_dict.items()
        }
