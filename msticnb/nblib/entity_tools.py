# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Entity Helper functions."""
from typing import Dict, List, Union

import pandas as pd

from .._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


def extract_entities(
    data: pd.DataFrame, cols: Union[str, List[str]]
) -> Dict[str, List[str]]:
    """
    Extract items from a column (strings or lists).

    Parameters
    ----------
    data : pd.DataFrame
        DataFrame to parse
    cols : Union[str, List[str]]
        Columns to use for input

    Returns
    -------
    Dict[str, List[str]]
        Dictionary of (column: result_list)

    """
    if not isinstance(cols, list):
        cols = [cols]

    val_results = {}
    for col in cols:
        ent_vals = list(data[col].values)
        test_val = data[col].iloc[0]
        if isinstance(test_val, list):
            ent_vals = list({ent for ent_list in ent_vals for ent in ent_list})
        val_results[col] = ent_vals

    return val_results
