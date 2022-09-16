# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
msticnb Notebooklets main package.

To start using notebooklets:

.. code:: python
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
from typing import Any, Dict, List, Optional, Union

from ._version import VERSION
from .data_providers import DataProviders, QueryProvider  # noqa:F401
from .data_providers import init as dp_init  # noqa:F401
from .nb_browser import NBBrowser  # noqa:F401
from .nb_pivot import add_pivot_funcs  # noqa:F401
from .options import get_opt, set_opt  # noqa:F401
from .read_modules import discover_modules, find, nb_index, nblts  # noqa:F401
from .template import create_template  # noqa:F401

__version__ = VERSION

# pylint: disable=invalid-name
browse = NBBrowser


def init(
    query_provider: Union[str, QueryProvider] = "MSSentinel",
    namespace: Optional[Dict[str, Any]] = None,
    providers: Optional[List[str]] = None,
    **kwargs,
):
    """
    Initialize notebooklets data providers and pivots.

    Parameters
    ----------
    query_provider : Union[str, QueryProvider], optional
        DataEnvironment name of the primary query provider,
        or an instance of an existing query provider,
        by default "MSSentinel"
    namespace : Optional[Dict[str, Any]], optional
        The global namespace - used to add pivot functions
    providers : Optional[List[str]], optional
        A list of other provider names to load

    Other Parameters
    ----------------
    kwargs :
        Optional keyword arguments to pass to DataProviders
        and Pivot initializers.

    Notes
    -----
    Use msticnb.DataProviders.list_providers() to get a list
    of accepted providers.

    """
    discover_modules()
    print(f"Notebooklets: {len(list(nblts.iter_classes()))} notebooklets loaded.")
    dp_init(query_provider=query_provider, providers=providers, **kwargs)
    if not namespace:
        # Try to get the globals namespace from top-level caller
        # pylint: disable=protected-access
        namespace = sys._getframe(1).f_globals
        # pylint: enable=protected-access
    add_pivot_funcs(namespace=namespace, **kwargs)
