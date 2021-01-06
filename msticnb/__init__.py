# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
msticnb Notebooklets main package.

To start using notebooklets:
>>> import msticnb as nb
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

from .data_providers import DataProviders, init  # noqa:F401
from .read_modules import discover_modules, nblts, nb_index, find  # noqa:F401
from .options import get_opt, set_opt  # noqa:F401
from .nb_browser import NBBrowser  # noqa:F401

from ._version import VERSION

__version__ = VERSION

# pylint: disable=invalid-name
browse = NBBrowser
discover_modules()
print(len(list(nblts.iter_classes())), "notebooklets loaded.")
