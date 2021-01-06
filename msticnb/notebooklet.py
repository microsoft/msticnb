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
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import bokeh.io
import pandas as pd
from bokeh.models import LayoutDOM
from bokeh.plotting.figure import Figure
from IPython.core.getipython import get_ipython
from IPython.display import HTML, display
from tqdm import tqdm
from msticpy.common.timespan import TimeSpan

from ._version import VERSION
from .common import MsticnbDataProviderError, MsticnbError
from .data_providers import DataProviders
from .nb_metadata import NBMetadata, read_mod_metadata
from .options import get_opt, set_opt

__version__ = VERSION
__author__ = "Ian Hellen"


# pylint: disable=too-few-public-methods
class NotebookletResult:
    """Base result class."""

    def __init__(
        self,
        description: Optional[str] = None,
        timespan: Optional[TimeSpan] = None,
        notebooklet: Optional["Notebooklet"] = None,
    ):
        """
        Create new Notebooklet result instance.

        Parameters
        ----------
        description : Optional[str], optional
            Result description, by default None
        timespan : Optional[TimeSpan], optional
            TimeSpan for the results, by default None
        notebooklet : Optional[, optional
            Originating notebooklet, by default None
        """
        self.description = description or self.__class__.__qualname__
        self.timespan = timespan
        self.notebooklet = notebooklet
        self._attribute_desc: Dict[str, Tuple[str, str]] = {}

        # Populate the `_attribute_desc` dictionary on init.
        self._populate_attr_desc()

    def __str__(self):
        """Return string representation of object."""
        return "\n".join(
            f"{name}: {self._str_repr(val)}"
            for name, val in self.__dict__.items()
            if not name.startswith("_")
        )

    @staticmethod
    def _str_repr(obj):
        if isinstance(obj, pd.DataFrame):
            return f"DataFrame: {len(obj)} rows"
        if isinstance(obj, LayoutDOM):
            return "Bokeh plot"
        return str(obj)

    # pylint: disable=unsubscriptable-object, no-member
    def _repr_html_(self):
        """Display HTML represention for notebook."""
        attrib_lines = []
        for name, val in self.__dict__.items():
            if name.startswith("_"):
                continue
            attr_desc = ""
            attr_type, attr_text = self._attribute_desc.get(
                name, (None, None)
            )  # type: ignore
            if attr_type:
                attr_desc += f"[{attr_type}]<br>"
            if attr_text:
                attr_desc += f"{attr_text}<br>"
            attrib_lines.append(f"<h4>{name}</h4>{attr_desc}{self._html_repr(val)}")
        return "<br>".join(attrib_lines)

    # pylint: enable=unsubscriptable-object, no-member

    # pylint: disable=protected-access
    @staticmethod
    def _html_repr(obj):
        if isinstance(obj, pd.DataFrame):
            return obj.head(5)._repr_html_()
        if isinstance(obj, (LayoutDOM, Figure)):
            bokeh.io.show(obj)
        if hasattr(obj, "_repr_html_"):
            return obj._repr_html_()
        return str(obj).replace("\n", "<br>").replace(" ", "&nbsp;")

    # pylint: enable=protected-access

    def _populate_attr_desc(self):
        indent = " " * 4
        in_attribs = False
        attr_name = None
        attr_type = None
        attr_dict = {}
        attr_lines = []
        doc_str = inspect.cleandoc(self.__doc__)
        for line in doc_str.split("\n"):
            if line.strip() == "Attributes":
                in_attribs = True
                continue
            if (
                line.strip() == "-" * len("Attributes")
                or not in_attribs
                or not line.strip()
            ):
                continue
            if not line.startswith(indent):
                # if existing attribute, add to dict
                if attr_name:
                    attr_dict[attr_name] = attr_type, " ".join(attr_lines)
                attr_name, attr_type = [item.strip() for item in line.split(":")]
                attr_lines = []
            else:
                attr_lines.append(line.strip())
        attr_dict[attr_name] = attr_type, " ".join(attr_lines)
        if "timespan" not in attr_dict:
            attr_dict["timespan"] = (
                "TimeSpan",
                "Time span for the queried results data.",
            )
        # pylint: disable=no-member
        self._attribute_desc.update(attr_dict)  # type: ignore
        # pylint: enable=no-member

    @property
    def properties(self):
        """Return names of all properties."""
        return [
            name
            for name, val in self.__dict__.items()
            if val is not None and not name.startswith("_")
        ]

    def prop_doc(self, name) -> Tuple[str, str]:
        """Get the property documentation for the property."""
        # pylint: disable=unsupported-membership-test, unsubscriptable-object
        if name in self._attribute_desc:
            return self._attribute_desc[name]
        # pylint: enable=unsupported-membership-test, unsubscriptable-object
        raise KeyError(f"Unknown property {name}.")


class Notebooklet(ABC):
    """Base class for Notebooklets."""

    metadata: NBMetadata = NBMetadata(
        name="Notebooklet", description="Base class", default_options=[]
    )
    module_path = ""

    def __init__(self, data_providers: Optional[DataProviders] = None, **kwargs):
        """
        Intialize a new instance of the notebooklet class.

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

        # pylint: disable=no-member
        self.data_providers = data_providers or DataProviders.current()  # type: ignore
        # pylint: enable=no-member
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
            raise MsticnbDataProviderError(
                f"Required data provider(s) {', '.join(missing_provs)} not loaded.",
                f"Class {self.__class__.__name__}",
                *prov_add_errs,
            )
        if unknown_provs:
            warnings.warn(
                f"Unknown provider(s) {', '.join(unknown_provs)} in req_providers list."
                + f"Class {self.__class__.__name__}"
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
                self.options = list(set(self.options) | add_options)
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
        Return default options for Notebooklet run function.

        Returns
        -------
        List[str]
            Supported options.

        """
        return cls.metadata.options_doc

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

        return (bool(match_count == len(terms)), match_count)

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
            with open(cls.module_path, "r") as mod_file:
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
