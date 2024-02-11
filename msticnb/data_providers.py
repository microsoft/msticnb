# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Data Providers class and init function."""
import inspect
import sys
from collections import namedtuple
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

from msticpy.common.exceptions import MsticpyAzureConfigError
from msticpy.common.wsconfig import WorkspaceConfig

try:
    from msticpy.context import GeoLiteLookup, IPStackLookup, TILookup
    from msticpy.context.azure.azure_data import AzureData
    from msticpy.data.core.data_providers import QueryProvider
    from msticpy.data.core.query_defns import DataEnvironment
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.data.azure.azure_data import AzureData
    from msticpy.data import QueryProvider
    from msticpy.data.query_defns import DataEnvironment
    from msticpy.sectools import GeoLiteLookup, IPStackLookup, TILookup

from ._version import VERSION
from .common import MsticnbDataProviderError, MsticnbError
from .options import get_opt

__version__ = VERSION
__author__ = "Ian Hellen"


class SingletonDecorator:
    """
    Singleton decorator class.

    Notes
    -----
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
        if (
            self.instance is None
            or getattr(self.instance, "kwargs", None) != kwargs
            or getattr(self.instance, "args", None) != args
        ):
            self.instance = self.wrapped_cls(*args, **kwargs)
            self.instance.kwargs = kwargs
            self.instance.args = args
        return self.instance

    def current(self):
        """Return the current instance of the wrapped class."""
        return self.instance

    def __getattr__(self, name):
        """Return the attribute `name` from the wrapped class."""
        if hasattr(self.wrapped_cls, name):
            return getattr(self.wrapped_cls, name)
        if self.instance is None:
            return None
        if name == "current":
            return self.instance
        return getattr(self.instance, name)


ProviderDefn = namedtuple("ProviderDefn", "prov_class, connect_reqd, get_config")


@SingletonDecorator
class DataProviders:
    """Notebooklet DataProviders class."""

    _DEFAULT_PROVIDERS = ["tilookup", "geolitelookup"]
    _OTHER_PROVIDERS = ["ipstacklookup"]

    def __init__(
        self,
        query_provider: Union[str, QueryProvider] = "MSSentinel",
        providers: Optional[List[str]] = None,
        **kwargs,
    ):
        """
        Instantiate an singleton instance of DataProviders.

        Parameters
        ----------
        query_provider : Union[str, QueryProvider], optional
            DataEnvironment name of the primary query provider,
            or an instance of an existing query provider,
            by default "MSSentinel"
        providers : Optional[List[str]], optional
            A list of provider names to load.
            You can add additional query providers by including them
            in the `providers` list.

        Other Parameters
        ----------------
        kwargs
            Pass parameters to individual providers using the following notation:
            `{provider_name}_{param_name}="param_value"
            Where `provider_name` is the name of the data provider,
            `param_name` is the parameter name expected by the
            provider and `param_value` is the value to assign to
            `param_name`. `param_value` can be any type.

            Depending on the provider, these parameters (with the prefix stripped)
            are sent to either the constructor or the `connect` method.

        Notes
        -----
        To see a list of current providers use `get_providers` class
        method.

        """
        self.provider_names: set = self._get_custom_providers(providers)
        self.provider_classes: Dict[str, ProviderDefn] = self._create_provider_defns()
        self.providers: Dict[str, Any] = {}

        self.query_provider = None
        parsed_provider = DataEnvironment.Unknown
        if isinstance(query_provider, str):
            parsed_provider = self._parse_provider_name(query_provider)
            self.provider_names.add(parsed_provider.name)
        elif isinstance(query_provider, QueryProvider):
            # If this is a query provider instance, just add it directly
            self.query_provider = query_provider
            parsed_provider = query_provider.environment
            self.providers[parsed_provider] = query_provider

        # Go through list of providers, instantiating and connecting them.
        for provider in sorted(self.provider_names):
            try:
                self.add_provider(provider, **kwargs)
            except MsticnbDataProviderError as err:
                print(f"Data provider {provider} could not be added.")
                print(err.args)
            else:
                if (
                    provider in self.providers
                    and not self.query_provider
                    and provider == parsed_provider.name
                ):
                    # This is the default query provider
                    setattr(self, "query_provider", self.providers[provider])

    def __getitem__(self, key: str):
        """Return provider matching `key`."""
        if key in self.providers:
            return self.providers[key]
        alt_key = DataEnvironment.parse(key)
        if alt_key in self.providers:
            return self.providers[alt_key]
        raise KeyError(key, "not found")

    def _create_provider_defns(self):
        """Definitions for provider construction."""
        defns = {
            "azuresentinel": ProviderDefn(QueryProvider, True, self._azsent_get_config),
            "queryprovider": ProviderDefn(QueryProvider, True, None),
            "azuredata": ProviderDefn(AzureData, True, None),
            "tilookup": ProviderDefn(TILookup, False, None),
            "geolitelookup": ProviderDefn(GeoLiteLookup, False, None),
            "ipstacklookup": ProviderDefn(IPStackLookup, False, None),
        }
        # Add loganalytics as an alias for azuresentinel
        defns["loganalytics"] = defns["azuresentinel"]
        return defns

    @staticmethod
    def _parse_provider_name(query_provider):
        parsed_provider = DataEnvironment.parse(query_provider)
        # If we weren't able to match the name to a known provider, raise exception.
        if parsed_provider == DataEnvironment.Unknown:
            known_providers = set(DataEnvironment.__members__.keys()) - {
                "Unknown",
                "Kusto",
                "AzureSecurityCenter",
            }
            raise MsticnbDataProviderError(
                f"Unknown query provider '{query_provider}",
                f"Available providers are {', '.join(known_providers)}",
            )
        return parsed_provider

    def _get_custom_providers(self, providers):
        requested_provs = set(self._DEFAULT_PROVIDERS)
        if not providers:
            return requested_provs

        providers = [prov.casefold() for prov in providers]
        add_provs = {opt[1:] for opt in providers if opt.startswith("+")}
        sub_provs = {opt[1:] for opt in providers if opt.startswith("-")}
        std_provs = {opt for opt in providers if opt[0] not in ("+", "-")}
        if std_provs and (add_provs or sub_provs):
            raise MsticnbError(
                "Provider list must be either a list of providers to use",
                "or providers to add/remove from the default set.",
                "You cannot mix these.",
            )
        if sub_provs:
            requested_provs = requested_provs - sub_provs
        if add_provs:
            requested_provs = requested_provs | add_provs
        if not add_provs and not sub_provs:
            requested_provs = set(providers)

        return requested_provs

    def add_provider(self, provider: str, **kwargs):
        """
        Add a provider to the current provider set.

        Parameters
        ----------
        provider : str
            Name of the provider.

        """
        if provider in self.providers:
            return
        provider_key = provider.casefold()
        new_provider = None
        if provider in DataEnvironment.__members__:
            # If this is a known query provider, pass to appropriate
            prov_def = self.provider_classes.get(
                provider_key, self.provider_classes["queryprovider"]
            )
            new_provider = self._query_prov(provider, prov_def, **kwargs)
        elif provider_key in self.provider_classes:
            # Else if this is a known data provider
            prov_def = self.provider_classes[provider_key]
            if prov_def.connect_reqd:
                new_provider = self._query_prov(provider, prov_def, **kwargs)
            else:
                new_provider = self._no_connect_prov(provider, prov_def, **kwargs)
        else:
            raise MsticnbDataProviderError(f"Provider {provider} not recognized.")

        if new_provider:
            setattr(self, provider, new_provider)
            self.providers[provider] = new_provider

    def has_required_providers(
        self, reqd_provs: Iterable[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Check the provider list against the list of loaded providers.

        Parameters
        ----------
        reqd_provs : Iterable[str]
            Required provider list.

        Returns
        -------
        Tuple[List[str], List[str]
            List of missing providers found
            List of unknown providers found

        """
        if not reqd_provs:
            return [], []
        r_prov_names = {prov for prov in reqd_provs if "|" not in prov}

        # remove matching items
        missing_provs = r_prov_names - set(self.providers)
        matched_provs = set()
        for req_prov in missing_provs:
            # See if the required provider is an alias of another query provider
            alt_name = DataEnvironment.parse(req_prov)
            if alt_name.name in missing_provs:
                matched_provs.add(req_prov)
                continue
            # If the required provider is a query provider
            # and the LocalData provider is loaded - assume this is
            # an intended replacement
            if alt_name != DataEnvironment.Unknown and "LocalData" in self.providers:
                matched_provs.add(req_prov)
        missing_provs = missing_provs - matched_provs

        # Process required providers where optional items are specified
        for r_prov in {prov for prov in reqd_provs if "|" in prov}:
            prov_opts = {prov.strip() for prov in r_prov.split("|")}
            # Add canonical name for any aliases
            alias_opts = {DataEnvironment.parse(prov).name for prov in prov_opts}
            prov_opts.update(alias_opts - {"Unknown"})
            # We only need to match one of these
            if any(m_prov for m_prov in prov_opts if m_prov in self.providers):
                continue
            missing_provs.add(r_prov)
        unknown_provs = missing_provs - set(self.list_providers())

        return list(missing_provs), list(unknown_provs)

    @classmethod
    def list_providers(cls) -> List[str]:
        """
        Return the list of all providers.

        Returns
        -------
        List[str]
            List of all providers.

        """
        providers = list(DataEnvironment.__members__.keys())
        providers.remove("Unknown")
        providers.extend(cls._DEFAULT_PROVIDERS)
        providers.extend(cls._OTHER_PROVIDERS)
        return providers

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
        return cls._DEFAULT_PROVIDERS

    def _query_prov(self, provider: str, provider_defn: ProviderDefn, **kwargs) -> Any:
        try:
            # Get any keys with the provider prefix and initialize the provider
            prov_kwargs_args = self._get_provider_kwargs(provider, **kwargs)

            # instantiate the provider class (sending all kwargs)
            created_provider = provider_defn.prov_class(provider, **prov_kwargs_args)
            if created_provider.connected:
                return created_provider
            # get the args required by connect function
            prov_connect_args = self._get_connect_args(
                created_provider.connect, **prov_kwargs_args
            )
            # if there is a function to get config settings
            if not prov_connect_args and provider_defn.get_config:
                prov_connect_args = provider_defn.get_config()
            # call the connect function
            try:
                created_provider.connect(**prov_connect_args)
            except Exception as err:  # pylint: disable=broad-except
                print(f"Connection attempt for {provider} failed.\n{err}")
            return created_provider
        except MsticpyAzureConfigError as mp_ex:
            if get_opt("verbose"):
                print("Warning:", mp_ex.args)
            return None

    def _no_connect_prov(
        self, provider: str, provider_defn: ProviderDefn, **kwargs
    ) -> Any:
        # Get the args passed to __init__ for this provider
        prov_args = self._get_provider_kwargs(provider, **kwargs)
        # If there are none and there's a config function, call that.
        if not prov_args and provider_defn.get_config:
            prov_args = provider_defn.get_config()
        # Instantiate the provider
        return provider_defn.prov_class(**prov_args)

    # Helper methods
    @staticmethod
    def _get_provider_kwargs(prefix: str, **kwargs) -> Dict[str, str]:
        """Return the kwargs prefixed with "prefix_"."""
        if prefix == "LogAnalytics" and any(
            key for key in kwargs if key.startswith("AzureSentinel")
        ):
            azsent_args = {
                key.replace("AzureSentinel", "LogAnalytics"): val
                for key, val in kwargs.items()
            }
            kwargs.update(azsent_args)

        return {
            name.replace(f"{prefix}_", ""): arg
            for name, arg in kwargs.items()
            if name.startswith(prefix)
        }

    @staticmethod
    def _get_connect_args(func: Callable, **kwargs) -> Dict[str, str]:
        """Get the arguments required by the `connect` function."""
        connect_params = inspect.signature(func).parameters
        return {
            name: arg_val for name, arg_val in kwargs.items() if name in connect_params
        }

    # Provider get_config functions
    @staticmethod
    def _azsent_get_config(**kwargs) -> Dict[str, str]:
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
            raise MsticnbDataProviderError(
                "Could not find valid MS Sentinel configuration.",
                "Please ensure configuration files are set correctly or supply",
                "azure_sentinel.workspace_id and azure_sentinel.tenant_id",
                "arguments to this class.",
            )
        return {"connection_str": ws_config.code_connect_str}


def init(
    query_provider: Union[str, QueryProvider] = "MSSentinel",
    providers: Optional[List[str]] = None,
    **kwargs,
):
    """
    Instantiate an instance of DataProviders.

    Parameters
    ----------
    query_provider : Union[str, QueryProvider], optional
        DataEnvironment name of the primary query provider,
        or an instance of an existing query provider,
        by default "MSSentinel"
        You can add additional query providers by including them
        in the `providers` list.
    providers : Optional[List[str]], optional
        A list of provider names, by default None

    Other Parameters
    ----------------
    kwargs
        You can pass parameters to individual providers using
        the following notation:
        `ProviderName_param_name="param_value"
        Where `ProviderName` is the name of the data provider,
        `param_name` is the parameter name expected by the
        provider and `param_value` is the value to assign to
        `param_name`. `param_value` can be any type.

        Depending on the provider, these parameters (with the
        prefix stripped) are sent to either the constructor or
        `connect` method.

    Notes
    -----
    To see a list of currently supported providers call:
    `DataProviders.list_providers()`

    """
    d_provs = DataProviders(query_provider, providers, **kwargs)
    print(f"Notebooklets: Loaded providers: {', '.join(d_provs.providers.keys())}")
    msticnb = sys.modules["msticnb"]
    setattr(msticnb, "data_providers", d_provs.providers)
