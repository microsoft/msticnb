# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
msticnb Notebooklets main package.

To start using notebooklets:
>>> import msticnb as nb
>>> # optionally give a query provider nb.init(query_provider=qry_prov)
>>> nb.init()
>>>
>>> # Auto-complete tree of notebooklets
>>> nb.nblts
>>>
>>> # List notebooklets
>>> nb.nb_index
>>>
>>> # Use a notebooklet
>>> host_summary = nb.nblts.azent.host.HostSummary()
>>> host_summary.run();
>>>
>>> # help
>>> help(host_summary)
>>> print("Options:", host_summary.all_options())
>>> print("Settings:", host_summary.get_settings())
>>>
>>> # find a notebooklet
>>> nb.find("host linux azure")
>>>
>>> # Interactive notebook browser
>>> nb.browse()

for more help see https://msticnb.readthedocs.org/

"""
import sys
from typing import Any, Dict, List, Optional

from .data_providers import DataProviders, init as dp_init  # noqa:F401
from .read_modules import discover_modules, nblts, nb_index, find  # noqa:F401
from .options import get_opt, set_opt  # noqa:F401
from .nb_browser import NBBrowser  # noqa:F401
from .nb_pivot import add_pivot_funcs  # noqa:F401

from ._version import VERSION

__version__ = VERSION

# pylint: disable=invalid-name
browse = NBBrowser
discover_modules()
print(f"Notebooklets: {len(list(nblts.iter_classes()))} notebooklets loaded.")


def init(
    query_provider: str,
    namespace: Optional[Dict[str, Any]] = None,
    providers: Optional[List[str]] = None,
    **kwargs,
):
    """
    Initialize notebooklets dataproviders and pivots.

    Parameters
    ----------
    query_provider : str
        The default query provider to use with notebooklets
    namespace : Optional[Dict[str, Any]], optional
        The global namespace - used to add pivot functions
    providers : Optional[List[str]], optional
        A list of other provider names to load

    Other parameters
    ----------------
    kwargs :
        Optional keyword arguments to pass to DataProviders
        and Pivot initializers.

    Notes
    -----
    Use msticnb.DataProviders.list_providers() to get a list
    of accepted providers.

    """
    dp_init(query_provider=query_provider, providers=providers, **kwargs)
    if not namespace:
        # Try to get the globals namespace from top-level caller
        # pylint: disable=protected-access
        namespace = sys._getframe(1).f_globals
        # pylint: enable=protected-access
    add_pivot_funcs(namespace=namespace, **kwargs)
