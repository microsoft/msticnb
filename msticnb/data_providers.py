# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Common definitions and classes."""
import inspect
from typing import Optional, List, Dict, Any
import sys

from msticpy.data import QueryProvider
from msticpy.data.azure_data import AzureData, MsticpyAzureException
from msticpy.common.wsconfig import WorkspaceConfig
from msticpy.sectools import TILookup, GeoLiteLookup

from .common import MsticnbError
from .options import get_opt

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
        self.__doc__ = wrapped_cls.__doc__

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

    _default_providers = ["azure_sentinel", "azure_api", "ti_lookup", "geolite_lookup"]
    _other_providers: List[str] = []

    def __init__(self, providers: Optional[List[str]] = None, **kwargs):
        """
        Instantiate an singleton instance of DataProviders.

        Parameters
        ----------
        providers : Optional[List[str]], optional
            A list of provider names, by default "azure_sentinel"

        Other Parameters
        ----------------
        kwargs
            You can pass parameters to individual providers using
            the following notation:
            `provider_name.param_name="param_value"
            Where `provider_name` is the name of the data provider,
            `param_name` is the parameter name expected by the
            provider and `param_value` is the value to assign to
            `param_name`. `param_value` can be any type.

            Depending on the provider, these parameters (with the
            prefix stripped) are sent to either the constructor or
            `connect` method.

        Notes
        -----
        To see a list of current providers

        """
        self.provider_names = providers or self._default_providers
        self.providers: Dict[str, Any] = {}

        provider_dispatch = {
            "azure_sentinel": self._azure_sentinel_prov,
            "azure_api": self._azure_api_prov,
            "ti_lookup": self._ti_lookup_prov,
            "geolite_lookup": self._geolite_lookup_prov,
        }
        self.query_provider = None
        self.azure_api = None
        self.ti_lookup = None
        self.geolite_lookup = None

        for provider in self.provider_names:
            if provider in provider_dispatch:
                provider_dispatch[provider](provider, **kwargs)
                setattr(self, provider, self.providers.get(provider))

    @classmethod
    def get_providers(cls) -> List[str]:
        """
        Return the list of all providers.

        Returns
        -------
        List[str]
            List of all providers.

        """
        return cls._default_providers + cls._other_providers

    # Provider initializers

    @classmethod
    def get_def_providers(cls) -> List[str]:
        """
        Return the list of default providers.

        Returns
        -------
        List[str]
            List of default providers.

        """
        return cls._default_providers

    def _azure_sentinel_prov(self, provider, **kwargs):
        # Get any keys with the provider prefix and initialize the provider
        azsent_args = self._get_provider_kwargs(provider, **kwargs)
        self.query_provider = QueryProvider("LogAnalytics")
        self.providers[provider] = self.query_provider
        azsent_connect_args = self._get_azsent_connect_args(**azsent_args)

        # If we don't have connection args from kwargs, get them from config
        if not azsent_connect_args:
            # if no explict args, try to get them from config.
            workspace = azsent_args.get("workspace")
            config_file = azsent_args.get("config_file")
            azsent_connect_args["connection_str"] = WorkspaceConfig(
                workspace=workspace, config_file=config_file
            ).code_connect_str
        self.query_provider.connect(**azsent_connect_args)

    def _azure_api_prov(self, provider, **kwargs):
        az_data_args = self._get_provider_kwargs(provider, **kwargs)
        try:
            az_provider = AzureData()
            az_connect_args = self._get_connect_args(
                az_provider.connect, **az_data_args
            )
            az_provider.connect(**az_connect_args)
            self.providers[provider] = az_provider
        except MsticpyAzureException as mp_ex:
            if get_opt("verbose"):
                print("Warning:", mp_ex.args)

    def _ti_lookup_prov(self, provider, **kwargs):
        ti_lookup_args = self._get_provider_kwargs(provider, **kwargs)
        self.providers[provider] = TILookup(ti_lookup_args)

    def _geolite_lookup_prov(self, provider, **kwargs):
        geolite_lookup_args = self._get_provider_kwargs(provider, **kwargs)
        self.providers[provider] = GeoLiteLookup(geolite_lookup_args)

    # Helper methods
    @staticmethod
    def _get_provider_kwargs(prefix, **kwargs):
        return {
            name.replace(f"{prefix}.", ""): arg
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
            raise MsticnbError(
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

    Other Parameters
    ----------------
    kwargs
        You can pass parameters to individual providers using
        the following notation:
        `provider_name.param_name="param_value"
        Where `provider_name` is the name of the data provider,
        `param_name` is the parameter name expected by the
        provider and `param_value` is the value to assign to
        `param_name`. `param_value` can be any type.

        Depending on the provider, these parameters (with the
        prefix stripped) are sent to either the constructor or
        `connect` method.

    """
    d_provs = DataProviders(providers, **kwargs)
    print(f"Loaded providers: {', '.join(d_provs.providers.keys())}")
    msticnb = sys.modules["msticnb"]
    setattr(msticnb, "data_providers", d_provs.providers)
