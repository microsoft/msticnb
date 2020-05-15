# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Azure Sentinel host logon summary test class."""
import os
import pandas as pd

import msticnb as nb

_test_data_folders = [
    d for d, _, _ in os.walk(os.getcwd()) if d.endswith("/tests/testdata")
]
if len(_test_data_folders) == 1:
    _TEST_DATA = _test_data_folders[0]
else:
    _TEST_DATA = "./tests/testdata"

# ToDo work out handling KQL load.
nb.init()

def test_logon_summary():
    test_nblt = nb.nblts.azsent.host.HostLogonsSummary()
    input_file = os.path.join(_TEST_DATA, "sample_logons.csv")
    test_data = pd.read_csv(input_file)
    output = test_nblt.run(data=test_data)
    assert isinstance(output.failed_success, pd.DataFrame)
    assert len(output.logon_sessions) == 95
    assert isinstance(output.plots, dict)
