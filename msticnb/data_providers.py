# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Common definitions and classes."""
import inspect
from typing import Optional, List, Dict, Any

from msticpy.data import QueryProvider
from msticpy.data.azure_data import AzureData
from msticpy.common.wsconfig import WorkspaceConfig

from .common import NotebookletException

from ._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


class SingletonDecorator:
    """
    Singleton decorator class.

    Notes
    -------
    Using this decorator on a class enforces the following
    behavior:
    - First instantiation of class will work as normal
    - Subsequent attempts with the same set/values of kwargs
      will just return the original class
    - Instantiation of the class with a different set of kwargs
      will instantiate a new class.
    - The class method `current()` will always return the
      last instance of the class.
    """

    def __init__(self, wrapped_cls):
        """Instantiate the class wrapper."""
        self.wrapped_cls = wrapped_cls
        self.instance = None

    def __call__(self, *args, **kwargs):
        """Overide the __call__ method for the wrapper class."""
        if self.instance is None or self.instance.kwargs != kwargs:
            self.instance = self.wrapped_cls(*args, **kwargs)
            self.instance.kwargs = kwargs
        return self.instance

    def current(self):
        """Return the current instance of the wrapped class."""
        return self.instance

    def __getattr__(self, name):
        """Return the attribute `name` from the wrapped class."""
        if self.instance is None:
            return None
        if name == "current":
            return self.instance
        return getattr(self.instance, name)


@SingletonDecorator
class DataProviders:
    """Notebooklet DataProviders class."""

    _default_providers = ["azure_sentinel"]

    def __init__(self, providers: Optional[List[str]] = None, **kwargs):
        """
        Instantiate an singleton instance of DataProviders.

        Parameters
        ----------
        providers : Optional[List[str]], optional
            A list of provider names, by default "azure_sentinel"

        """
        self.provider_names = providers or self._default_providers
        self.providers: Dict[str, Any] = {}

        if "azure_sentinel" in self.provider_names:
            azsent_args = self._get_provider_kwargs("azure_sentinel.", **kwargs)
            self.query_provider = QueryProvider("LogAnalytics")
            self.providers["azure_sentinel"] = self.query_provider
            azsent_connect_args = self._get_azsent_connect_args(**azsent_args)
            self.query_provider.connect(azsent_connect_args)

        if "azure_api" in self.provider_names:
            az_data_args = self._get_provider_kwargs("azure_api.", **kwargs)
            az_provider = AzureData()
            az_connect_args = self._get_connect_args(
                az_provider.connect, **az_data_args
            )
            az_provider.connect(**az_connect_args)
            self.providers["azure_api"] = az_provider

    @staticmethod
    def _get_provider_kwargs(prefix, **kwargs):
        return {
            name.replace(prefix, ""): arg
            for name, arg in kwargs.items()
            if name.startswith(prefix)
        }

    @staticmethod
    def _get_connect_args(func, **kwargs):
        connect_params = inspect.signature(func).parameters
        connect_args = {}
        for name, arg_val in kwargs.items():
            if name in connect_params:
                connect_args[name] = arg_val
        return connect_args

    @staticmethod
    def _get_azsent_connect_args(**kwargs):
        if "workspace" in kwargs:
            ws_config = WorkspaceConfig(workspace=kwargs["workspace"])
        elif "config_file" in kwargs:
            ws_config = WorkspaceConfig(config_file=kwargs["config_file"])
        elif (
            WorkspaceConfig.CONF_TENANT_ID_KEY in kwargs
            and WorkspaceConfig.CONF_WS_ID_KEY in kwargs
        ):
            ws_config = WorkspaceConfig()
            ws_config[WorkspaceConfig.CONF_TENANT_ID_KEY] = kwargs[
                WorkspaceConfig.CONF_TENANT_ID_KEY
            ]
            ws_config[WorkspaceConfig.CONF_WS_ID_KEY] = kwargs[
                WorkspaceConfig.CONF_WS_ID_KEY
            ]
        else:
            ws_config = WorkspaceConfig()

        if not ws_config.config_loaded:
            raise NotebookletException(
                "Could not find valid Azure Sentinel configuration.",
                "Please ensure configuration files are set correctly or supply",
                "azure_sentinel.workspace_id and azure_sentinel.tenant_id",
                "arguments to this class.",
            )
        return {"connection_str": ws_config.code_connect_str}


def init(providers: Optional[List[str]] = None, **kwargs):
    """
    Instantiate an instance of DataProviders.

    Parameters
    ----------
    providers : Optional[List[str]], optional
        A list of provider names, by default "azure_sentinel"

    """
    return DataProviders(providers, **kwargs)
