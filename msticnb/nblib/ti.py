# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Threat Intelligence notebooklet feature support."""
from typing import Any, Tuple, Optional

import numpy as np
import pandas as pd

from .._version import VERSION
from ..common import nb_markdown

__version__ = VERSION
__author__ = "Pete Bryan"


def get_ti_results(
    ti_lookup,
    data: pd.DataFrame,
    col: str,
) -> Tuple[Any, Optional[pd.DataFrame]]:
    """
    Lookup Threat Intel.

    Parameters
    ----------
    ti_lookup : TILookup
        TI Lookup provider
    data : pd.DataFrame
        Input data frame
    col : List
        Name of Ip address column

    Returns
    -------
    pd.DataFrame
        DataFrame with TI results for IPs

    """
    ti_merged_df = None
    iocs = data[col].dropna().unique()
    nb_markdown(f"Querying TI for {len(iocs)} indicators...")
    ti_results = ti_lookup.lookup_iocs(data=data, obs_col=col)
    if isinstance(ti_results, pd.DataFrame) and not ti_results.empty:
        ti_results = ti_results[ti_results["Severity"].isin(["warning", "high"])]
        ti_merged_df = data.merge(ti_results, how="inner", left_on=col, right_on="Ioc")
    return ti_results, ti_merged_df


def extract_iocs(
    data: pd.DataFrame, col: str, b64_extract: bool = False
) -> pd.DataFrame:
    """
    Extract IoCs from a dataframe.

    Parameters
    ----------
    data : pd.DataFrame
        The DataFrame to extract IoCs from
    col : str
        The column to extract IoCs from
    b64_extract : bool, optional
        wheter to attempt to B64 decode the column before extracting, by default False

    Returns
    -------
    pd.DataFrame
        DataFrame with extracted IoCs in the IoC column

    """
    if b64_extract:
        b64_extracted_data = data.mp_b64.extract(column=col)
        if not b64_extracted_data.empty:
            b64_extracted = pd.merge(
                data, b64_extracted_data[["decoded_string", col]], how="left", on=col
            )
            b64_extracted["decoded_string"] = b64_extracted["decoded_string"].astype(
                "str"
            )
            b64_iocs = b64_extracted.mp_ioc.extract(columns=["decoded_string"])
            b64_iocs["SourceIndex"] = pd.to_numeric(b64_iocs["SourceIndex"])
            data_b64_iocs = pd.merge(
                left=data,
                right=b64_iocs,
                how="outer",
                left_index=True,
                right_on="SourceIndex",
            )
        else:
            data_b64_iocs = data
    other_iocs = data_b64_iocs.mp_ioc.extract(columns=[col])
    all_data_w_iocs = pd.merge(
        left=data_b64_iocs,
        right=other_iocs,
        how="outer",
        left_index=True,
        right_on="SourceIndex",
    )
    if "Observable_x" in all_data_w_iocs.columns:
        all_data_w_iocs["IoC"] = np.where(
            all_data_w_iocs["Observable_x"].isna(),
            all_data_w_iocs["Observable_y"],
            all_data_w_iocs["Observable_x"],
        )
        all_data_w_iocs["IoCType"] = np.where(
            all_data_w_iocs["IoCType_x"].isna(),
            all_data_w_iocs["IoCType_y"],
            all_data_w_iocs["IoCType_x"],
        )
        all_data_w_iocs["IoC"] = all_data_w_iocs["IoC"].astype("str")
    else:
        all_data_w_iocs["IoC"] = all_data_w_iocs["Observable"].astype("str")
    all_data_w_iocs["IoCType"] = all_data_w_iocs["IoCType"].astype("str")
    return all_data_w_iocs
