# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Alert utility functions."""
try:
    from msticpy import nbwidgets
    from msticpy.vis import nbdisplay

    if not hasattr(nbwidgets, "SelectItem"):
        raise ImportError("Invalid nbwidgets")
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.nbtools import nbdisplay, nbwidgets

from ..._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


def browse_alerts(nb_result, alert_attr="related_alerts") -> nbwidgets.SelectAlert:
    """Return alert browser/viewer."""
    if nb_result is None or not hasattr(nb_result, alert_attr):
        return None
    rel_alerts = getattr(nb_result, alert_attr, None)
    if rel_alerts is None or rel_alerts.empty:
        return None

    if "CompromisedEntity" not in rel_alerts:
        rel_alerts["CompromisedEntity"] = "n/a"
    if "StartTimeUtc" not in rel_alerts:
        rel_alerts["StartTimeUtc"] = rel_alerts["TimeGenerated"]
    return nbwidgets.SelectAlert(alerts=rel_alerts, action=nbdisplay.format_alert)
