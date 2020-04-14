# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
msticnb Notebooklets main package.

To start using notebooklets:
>import msticnb as nb
>data_providers = nb.DataProviders()
># List notebooklet categories
>nb.nblt
"""

from .data_providers import DataProviders, init  # noqa:F401
from .read_modules import discover_modules, notebooklets, nb_index  # noqa:F401

from ._version import VERSION
__version__ = VERSION

discover_modules()
print(len(list(notebooklets.iter_classes())), "notebooklets loaded.")
