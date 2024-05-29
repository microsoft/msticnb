# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklet base classes."""
import inspect
import re
import warnings
from abc import ABC, abstractmethod
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

import pandas as pd
from IPython.core.getipython import get_ipython
from IPython.display import HTML, display
from msticpy.common.timespan import TimeSpan
from tqdm.auto import tqdm

from ._version import VERSION
from .common import MsticnbDataProviderError, MsticnbError
from .data_providers import DataProviders
from .nb_metadata import NBMetadata, read_mod_metadata
from .notebooklet_result import NotebookletResult
from .options import get_opt, set_opt

__version__ = VERSION
__author__ = "Ian Hellen"


# pylint: disable=too-many-public-methods
class Notebooklet(ABC):
    """Base class for Notebooklets."""

    metadata: NBMetadata = NBMetadata(
        name="Notebooklet", description="Base class", default_options=[]
    )
    module_path: Union[str, Path] = ""

    def __init__(self, data_providers: Optional[DataProviders] = None, **kwargs):
        """
        Initialize a new instance of the notebooklet class.

        Parameters
        ----------
        data_providers : DataProviders, Optional
            Optional DataProviders instance to query data.
            Most classes require this.

        Raises
        ------
        MsticnbDataProviderError
            If DataProviders has not been initialized.
            If required providers are specified by the notebooklet
            but are not available.

        """
        self._kwargs = kwargs
        self.options: List[str] = self.default_options()
        self._set_tqdm_notebook(get_opt("verbose"))
        self._last_result: Any = None
        self.timespan = TimeSpan(period="1d")
        self._inst_default_silent: Optional[bool] = kwargs.get("silent")
        self._current_run_silent: Optional[bool] = None
        set_opt("temp_silent", self.silent)

        # update "run" function documentation on first run
        self._add_run_doc_options()

        # Check required data providers are loaded.
        # pylint: disable=no-member
        self.data_providers = data_providers or DataProviders.current()  # type: ignore
        # pylint: enable=no-member
        self._check_nb_providers(**kwargs)

    def _check_nb_providers(self, **kwargs):
        """Check that providers required for notebooklet are available."""
        if not self.data_providers:
            raise MsticnbDataProviderError(
                "No current DataProviders instance was found.",
                "Please create an instance of msticnb.",
            )
        self.query_provider = self.data_providers.query_provider
        missing_provs, unknown_provs = self.data_providers.has_required_providers(
            self.metadata.req_providers
        )
        prov_add_errs: List[Exception] = []
        if missing_provs:
            # Try to add any providers that the notebooklet needs.
            add_providers = missing_provs.copy()
            for missing_prov in add_providers:
                try:
                    self.data_providers.add_provider(provider=missing_prov, **kwargs)
                    missing_provs.remove(missing_prov)
                    if missing_prov in unknown_provs:
                        unknown_provs.remove(missing_prov)
                except MsticnbDataProviderError as err:
                    prov_add_errs.append(err)

        if missing_provs:
            missing_mssg = [prov.replace("|", " or ") for prov in missing_provs]
            raise MsticnbDataProviderError(
                f"Required data provider(s) {', '.join(missing_mssg)} not loaded.",
                f"Class {self.__class__.__name__}",
                *prov_add_errs,
            )
        if unknown_provs:
            warnings.warn(
                f"Unknown provider(s) {', '.join(unknown_provs)} in req_providers list."
                + f"Class {self.__class__.__name__}"
            )

    def _add_run_doc_options(self):
        """Add options documentation to run function."""
        if "Default Options" in self.__class__.run.__doc__:
            return
        options_doc = (f"    {line}" for line in self.metadata.options_doc.split("\n"))
        self.__class__.run.__doc__ = (self.__class__.run.__doc__ or "") + "\n".join(
            options_doc
        )

    @abstractmethod
    def run(
        self,
        value: Any = None,
        data: Optional[pd.DataFrame] = None,
        timespan: Optional[TimeSpan] = None,
        options: Optional[Iterable[str]] = None,
        **kwargs,
    ) -> NotebookletResult:
        """
        Notebooklet abstract base class.

        Parameters
        ----------
        value : Any, optional
            value to process, by default None
        data : Optional[pd.DataFrame], optional
            Input data to process, by default None
        timespan : Optional[TimeSpan, Any], optional
            Timespan over which operations such as queries will be
            performed, by default None.
            This can be a TimeStamp object or another object that
            has valid `start`, `end`, or `period` attributes.
        options :Optional[Iterable[str]], optional
            List of options to use, by default None
            A value of None means use default options.
            Options prefixed with "+" will be added to the default options.
            Options prefixed with "-" will be removed from the default options.
            To see the list of available options type `help(cls)` where
            "cls" is the notebooklet class or an instance of this class.

        Other Parameters
        ----------------
        start : Union[datetime, datelike-string]
            Alternative to specifying timespan parameter.
        end : Union[datetime, datelike-string]
            Alternative to specifying timespan parameter.

        Returns
        -------
        NotebookletResult
            Result class from the notebooklet

        See Also
        --------
            TimeSpan

        """
        self._current_run_silent = kwargs.get("silent")
        set_opt("temp_silent", self.silent)
        if not options:
            self.options = self.default_options()
        else:
            def_options = self.default_options()
            add_options = {opt[1:] for opt in options if opt.startswith("+")}
            sub_options = {opt[1:] for opt in options if opt.startswith("-")}
            std_options = {opt for opt in options if opt[0] not in ("+", "-")}
            if std_options and (add_options or sub_options):
                raise MsticnbError(
                    "Option list must be either a list of options to use",
                    "or options to add/remove from the default set.",
                    "You cannot mix these.",
                )
            invalid_opts = (sub_options | add_options | std_options) - set(
                self.all_options()
            )
            if invalid_opts:
                print(f"Invalid options {list(invalid_opts)} ignored.")
            if sub_options:
                self.options = list(set(def_options) - sub_options)
            if add_options:
                self.options = list(set(def_options) | add_options)
            if not (add_options or sub_options):
                self.options = list(options)
        self._set_tqdm_notebook(get_opt("verbose"))
        if timespan:
            self.timespan = TimeSpan(timespan=timespan)
        elif "start" in kwargs and "end" in kwargs:
            self.timespan = TimeSpan(start=kwargs.get("start"), end=kwargs.get("end"))
        return NotebookletResult(notebooklet=self)

    def get_pivot_run(self, get_timespan: Callable[[], TimeSpan]):
        """Return Pivot-wrappable run function."""

        @wraps
        def pivot_run(*args, **kwargs):
            result = self.run(*args, timespan=get_timespan(), **kwargs)
            setattr(result, "notebooklet", self)
            return result

        return pivot_run

    def get_provider(self, provider_name: str):
        """
        Return data provider for the specified name.

        Parameters
        ----------
        provider_name : str
            Name of the provider

        Returns
        -------
        Any
            Provider instance.

        Raises
        ------
        MsticnbDataProviderError
            If provider is not found.

        """
        if provider_name not in self.data_providers.providers:
            raise MsticnbDataProviderError(
                f"Data provider {provider_name} not found.",
                "Please check that you have specified the required providers",
            )
        return self.data_providers.providers.get(provider_name)

    @property
    def silent(self) -> Optional[bool]:
        """
        Get the current instance setting for silent running.

        Returns
        -------
        Optional[bool]
            Silent running is enabled.

        """
        if self._current_run_silent is not None:
            return self._current_run_silent
        if self._inst_default_silent is not None:
            return self._inst_default_silent
        return None

    @silent.setter
    def silent(self, value: bool):
        """
        Set the current instance setting for silent running.

        Parameters
        ----------
        value : bool
            True to enable silent, False to disable.

        """
        self._inst_default_silent = value

    @property
    def result(self) -> Optional[NotebookletResult]:
        """
        Return result of the most recent notebooklet run.

        Returns
        -------
        Optional[NotebookletResult]
            Notebooklet result class or None if nothing has
            been run.

        """
        return self._last_result

    @classmethod
    def name(cls) -> str:
        """
        Return name of the Notebooklet.

        Returns
        -------
        str
            Name

        """
        return cls.metadata.name

    @classmethod
    def description(cls) -> str:
        """
        Return description of the Notebooklet.

        Returns
        -------
        str
            Description

        """
        return cls.metadata.description

    @classmethod
    def all_options(cls) -> List[str]:
        """
        Return supported options for Notebooklet run function.

        Returns
        -------
        List[str]
            Supported options.

        """
        opts = cls.metadata.get_options("all")
        return [opt[0] for opt in opts]

    @classmethod
    def default_options(cls) -> List[str]:
        """
        Return default options for Notebooklet run function.

        Returns
        -------
        List[str]
            Supported options.

        """
        opts = cls.metadata.get_options("default")
        return [opt[0] for opt in opts]

    @classmethod
    def list_options(cls) -> str:
        """
        Return options document for Notebooklet run function.

        Returns
        -------
        List[str]
            Supported options.

        """
        return cls.metadata.options_doc

    @classmethod
    def print_options(cls):
        """Print options for Notebooklet run function."""
        print(cls.metadata.options_doc)

    @classmethod
    def keywords(cls) -> List[str]:
        """
        Return search keywords for Notebooklet.

        Returns
        -------
        List[str]
            Keywords

        """
        return cls.metadata.keywords

    @classmethod
    def entity_types(cls) -> List[str]:
        """
        Entity types supported by the notebooklet.

        Returns
        -------
        List[str]
            Entity names

        """
        return cls.metadata.entity_types

    @classmethod
    def get_settings(cls, print_settings=True) -> Optional[str]:
        """
        Print or return metadata for class.

        Parameters
        ----------
        print_settings : bool, optional
            Print to standard, by default True
            or return the str formatted content.

        Returns
        -------
        Optional[str]
            If `print_settings` is True, returns None.
            If False, returns LF-delimited string of metadata settings.

        Notes
        -----
            Use `metadata` attribute to retrieve the metadata directly.

        """
        if print_settings:
            print(cls.metadata)
            return None
        return str(cls.metadata)

    @classmethod
    def match_terms(cls, search_terms: str) -> Tuple[bool, int]:
        """
        Search class definition for `search_terms`.

        Parameters
        ----------
        search_terms : str
            One or more search terms, separated by spaces
            or commas.
            Terms can be simple strings or regular expressions.

        Returns
        -------
        Tuple[bool, int]
            Returns a tuple of bool (True if all terms match)
            and int (count of matched terms)

        """
        search_text = " ".join(cls.metadata.search_terms)
        search_text += cls.__doc__ or ""
        terms = [
            subterm for term in search_terms.split(",") for subterm in term.split()
        ]
        match_count = sum(
            1 for term in terms if re.search(term, search_text, re.IGNORECASE)
        )

        return match_count == len(terms), match_count

    @staticmethod
    def _set_tqdm_notebook(verbose=False):
        if verbose:
            tqdm.pandas()

    def _get_timespan(self, timespan=None, **kwargs):
        if timespan:
            if isinstance(timespan, TimeSpan):
                self.timespan = timespan
            else:
                self.timespan = TimeSpan(timespan=timespan)
        elif "start" in kwargs and "end" in kwargs:
            self.timespan = TimeSpan(start=kwargs["start"], end=kwargs["end"])

    @classmethod
    def import_cell(cls):
        """Import the text of this module into a new cell."""
        if cls.module_path:
            with open(cls.module_path, "r", encoding="utf-8") as mod_file:
                mod_text = mod_file.read()
            if mod_text:
                # replace relative references with absolute paths
                mod_text = cls._update_mod_for_import(cls.module_path, mod_text)
                shell = get_ipython()
                shell.set_next_input(mod_text)

    @classmethod
    def _update_mod_for_import(cls, module_path, mod_text):
        mod_text = re.sub(r"\.{3,}", "msticnb.", mod_text)
        metadata, docs = read_mod_metadata(module_path, cls.__module__)
        metadata_repr = repr(metadata)
        metadata_repr = metadata_repr.replace("NBMetadata", "nb_metadata.NBMetadata")
        repl_text = (
            "_CLS_METADATA, _CELL_DOCS = "
            + "nb_metadata.read_mod_metadata(__file__, __name__)"
        )
        inline_text = f"_CELL_DOCS = {str(docs)}\n"
        inline_text = f"{inline_text}\n_CLS_METADATA = {metadata_repr}"
        return mod_text.replace(repl_text, inline_text)

    @classmethod
    def show_help(cls):
        """Display Documentation for class."""
        display(HTML(cls.get_help()))

    @classmethod
    def get_help(cls, fmt="html") -> str:
        """Return HTML document for class."""
        return cls._get_doc(fmt=fmt)

    @classmethod
    def _get_doc(cls, fmt):
        """Return documentation func. placeholder."""
        del fmt
        return "No documentation available."

    def check_valid_result_data(
        self, attrib: Optional[str] = None, silent: bool = False
    ) -> bool:
        """
        Check that the result is valid and `attrib` contains data.

        Parameters
        ----------
        attrib : str
            Name of the attribute to check, if None this function
            only checks for a valid _last_result.
        silent : bool
            If True, suppress output.

        Returns
        -------
        bool
            Returns True if valid data is available, else False.

        """
        if self._last_result is None:
            if not silent:
                print(
                    "No current result."
                    "Please use 'run()' to fetch the data before using this method."
                )
            return False
        if not attrib:
            return True
        data_obj = getattr(self._last_result, attrib)
        if data_obj is None or isinstance(data_obj, pd.DataFrame) and data_obj.empty:
            if not silent:
                print(f"No data is available for last_result.{attrib}.")
            return False
        return True

    def check_table_exists(self, table: str) -> bool:
        """
        Check to see if the table exists in the provider.

        Parameters
        ----------
        table : str
            Table name

        Returns
        -------
        bool
            True if the table exists, otherwise False.

        """
        if not self.query_provider:
            print(f"No query provider for table {table} is available.")
            return False
        if table not in self.query_provider.schema_tables:
            print(f"table {table} is not available.")
            return False
        return True

    def get_methods(self) -> Dict[str, Callable[[Any], Any]]:
        """Return methods available for this class."""
        meths = inspect.getmembers(self, inspect.ismethod)
        cls_selector = (
            f"bound method {self.__class__.__name__.rsplit('.', maxsplit=1)[0]}"
        )
        return {
            meth[0]: meth[1]
            for meth in meths
            if cls_selector in str(meth[1]) and not meth[0].startswith("_")
        }

    def list_methods(self) -> List[str]:
        """Return list of methods with descriptions."""
        methods = self.get_methods()
        method_desc: List[str] = []
        for name, method in methods.items():
            f_doc = inspect.getdoc(method)
            desc = f_doc.split("\n", maxsplit=1)[0] if f_doc else ""
            method_desc.append(f"{name} - '{desc}'")
        return method_desc
