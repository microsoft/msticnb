# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Notebooklet function class and decorator.

This allows custom functions to be added to a notebooklet

Examples
--------

Function defintions would look like the following examples.

A standard function that returns some data

.. code:: python

    from msticnb.nb.azsent.host.host_summary import HostSummary
    @nb_func(
        notebooklets=[HostSummary],  # Notebooklets to add func to
        name="get_logon_data",       # Name of the function
        func_type="run",             # The type of function
        options="logons",             # The options controlling if the func is run
        header="Header displayed when func is run",
        text="Descriptive text displayed.",
        result_attrib="host_logons"  # The attribute name to add to the result.
    )
    def fetch_host_logons(timerange, **kwargs):
        ...
        return xyz.get_stuff(timerange)


Most of the decorator parameters are optional. This defintion does not
attach the function to a notebooklet and uses the function name.
No options are specified so it will always run. No display text is
used.

.. code:: python

    from msticnb.nb.azsent.host.host_summary import HostSummary
    @nb_func(
        result_attrib="host_logons"  # The attribute name to add to the result.
    )
    def fetch_host_logons(timerange, **kwargs):
        ...
        return xyz.get_stuff(timerange)

Queries - built-in queries
~~~~~~~~~~~~~~~~~~~~~~~~~~
A query function using a built-in query. Note this function
should return either a query name or a tuple of the query name plus a dictionary to map
generic parameters to params expected by the query.

.. code:: python

    @nb_func(
        notebooklets=[HostSummary],
        name="get_logon_data",
        func_type="query",
        options="logons",
        header="Header displayed when func is run",
        text="Descriptive text displayed.",
        result_attrib="host_logons
    )
    def query_host_logons(qry_prov, timerange, value, **kwargs):
        return (
            "WindowsSecurity.get_host_logons",
            {"value": "host_name"}
        )

Queries - query strings
~~~~~~~~~~~~~~~~~~~~~~~

A query function using a built-in query. Note this function
should return a tuple of the query text plus a dictionary to map
generic parameters to params expected by the query.
The latter is optional if no mapping is needed.

Using raw query text
.. code:: python

    @nb_func(
        func_type="query",
        options="logons",
        result_attrib="host_logons
    )
    def query_host_logons(qry_prov, timerange, value, **kwargs):
        return (
            "SecurityEvent | where start = datetime({start}) "
            "| where Computer == '{value}'",
        )

.. code:: python

    @nb_func(
        func_type="query",
        options="logons",
        result_attrib="host_logons
    )
    def query_host_logons(qry_prov, timerange, value, **kwargs):
        return (
            "WindowsSecurity.list_host_logons",
            {"value": "host_name"},
        )

Each function will be invoked with a standard set of kwargs:

- qry_prov - the query provider
- timerange - timerange for the notebooklet operations. Note: this is
  passed to queries as 'start' and 'end'.
- options - the Notebooklet options arg
- silent - whether to display (this is handled by the NBFunc class)
- value - the `value` arg to the Notebooklet run
- data - the `data` arg to the Notebooklet run

"""

import contextlib
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Set, Union, get_args

from ._version import VERSION
from .common import set_text

__version__ = VERSION
__author__ = "Ian Hellen"

NBFuncType = Literal["run", "display", "query"]

_VALID_FUNC_TYPES = set(get_args(NBFuncType))


class NBFunc:
    """Notebooklet custom function."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        func: Callable[..., Any],
        name: Optional[str] = None,
        func_type: NBFuncType = "run",
        options: Optional[Union[str, List[str]]] = None,
        header: Optional[str] = None,
        text: Optional[str] = None,
        result_attrib: Optional[str] = None,
        **kwargs,
    ):
        """
        Create an instance of a notebooklet function.

        Parameters
        ----------
        func : Callable[..., Any]
            The function to run
        name : Optional[str], optional
            Optional name, by default this is the name of the
            original function
        func_type : NBFuncType, optional
            Either "run" - simple execution and return results or
            "query" - treat the contents of the function as a query
            definition to execute and return results from, by default "run"
        options : Optional[Union[str, List[str]]], optional
            If the function should be run only when a given notebooklet
            option is specified add the option as a string or list of
            string options, by default None
        header : Optional[str], optional
            The header to display when running the function, by default None
        text : Optional[str], optional
            The descriptive text to display when running the function, by default None
        result_attrib : Optional[str], optional
            The name of the notebooklet result attribute to assign the
            function return value to, by default None

        Raises
        ------
        ValueError
            If an invalid function type is specified.

        """
        self.name = name or func.__name__
        self.options = (
            options if isinstance(options, list) else [options] if options else []
        )
        self.header = header
        self.text = text
        self.result_attrib = result_attrib
        self.name_map = kwargs.pop("qry_param_map", {})
        self.doc = func.__doc__

        if func_type not in _VALID_FUNC_TYPES:
            raise ValueError(
                "Function type must be one of the following",
                ", ".join(f"'{func_type}'" for func_type in _VALID_FUNC_TYPES),
            )
        self.func_type = func_type
        self._run_func: Optional[Callable[..., Any]] = func

    def run(self, **kwargs):
        """Run method."""
        if not self._check_options(**kwargs):
            return None
        # Create a set_text wrapper to optionally display title/text
        text_wrapper = set_text(title=self.header, text=self.text)
        if self.func_type == "run" and callable(self._run_func):
            # wrap the function in the text display wrapper and run
            wrapped_func = text_wrapper(self._run_func)
            return self._set_result_attrib(wrapped_func(**kwargs))
        if self.func_type == "query" and isinstance(self._run_func, str):
            # wrap the function in the text display wrapper and run
            # Since this a query we handle a little differently
            wrapped_func = text_wrapper(self.run_query)
            return self._set_result_attrib(wrapped_func(self._run_func, **kwargs))
        warnings.warn(
            f"Notebooklet custom function {self.name} has an"
            f" invalid 'func_type': {self.func_type}"
        )
        return None

    def run_query(self, query, **kwargs):
        """Run a query."""
        qry_prov = kwargs.get("qry_prov")
        if not qry_prov:
            raise ValueError(
                f"No 'qry_prov' in parameters to query function {self.name}"
            )

        qry_kwargs = self._remap_names(self.name_map, kwargs)
        timespan = kwargs.get("timespan")
        if timespan:
            qry_kwargs["start"] = timespan.start
            qry_kwargs["end"] = timespan.end
        # the query could be a built-in query
        qry_suffix = f".{query}"
        builtin_query = next(
            iter(
                query for query in qry_prov.list_queries() if query.endswith(qry_suffix)
            )
        )

        if builtin_query:
            # The query could be fully-qualified or just a stem
            # if it's a dotted name, get the stem
            if "." in query:
                query = query.rsplit(".", maxsplit=1)[1]
            # and look for it in the all_queries container.
            query_func = getattr(qry_prov.all_queries, query)
            return self._set_result_attrib(query_func(**qry_kwargs))
        # If not, assume the query is a string.
        with contextlib.suppress(IndexError, KeyError):
            # and try to str.format it with kwargs - but ignore if this fails.
            query = query.format(**qry_kwargs)
        return self._set_result_attrib(qry_prov.exec_query(query))

    def _check_options(self, **kwargs) -> bool:
        """Return True if func options are in current options."""
        nb_options: Set[str] = set(kwargs.pop("options", []))
        if not self.options:
            return True
        return any(opt for opt in self.options if opt in nb_options)

    def _set_result_attrib(self, func_result, **kwargs):
        if not self.result_attrib:
            return func_result
        nb_result = kwargs.pop("result", None)
        setattr(nb_result, self.result_attrib, func_result)
        return func_result

    @staticmethod
    def _remap_names(
        name_map: Dict[str, str], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Return dictionary with mapped names."""
        return {name_map.get(name, name): val for name, val in kwargs.items()}


# pylint: disable=no-member
def _register_nb_function(nb_func_cls, reg_path):
    """Add the function to msticnb funcs dictionary."""
    msticnb = _get_msticnb()
    if not hasattr(msticnb, "funcs"):
        setattr(msticnb, "funcs", {})
    msticnb.funcs[reg_path] = nb_func_cls


# pylint: disable=no-member
def list_functions():
    """Return list of notebooklet functions."""
    msticnb = _get_msticnb()
    return list(msticnb.funcs) if hasattr(msticnb.funcs) else []


# pylint: disable=too-many-arguments
def nb_func(
    name: Optional[str] = None,
    func_type: NBFuncType = "run",
    reg_path: Optional[str] = None,
    notebooklets: Optional[Union[str, List[str]]] = None,
    options: Optional[str] = None,
    header: Optional[str] = None,
    text: Optional[str] = None,
    result_attrib: Optional[str] = None,
):
    """
    Register the function as a notebook function.

    Parameters
    ----------
    name : Optional[str], optional
        Optional name for the function, by default, the original
        function name is used.
    func_type : NBFuncType, optional
        Either "run" - simple execution and return results or
        "query" - treat the contents of the function as a query
        definition to execute and return results from, by default "run"
    options : Optional[str], optional
        If the function should be run only when a given notebooklet
        option is specified add the option as a string or list of
        string options, by default None
    header : Optional[str], optional
        The header to display when running the function, by default None
    text : Optional[str], optional
        The descriptive text to display when running the function, by default None
    result_attrib : Optional[str], optional
        The name of the notebooklet result attribute to assign the
        function return value to, by default None. If not specified, the results
        of the function execution will not be saved to the results
        object.
    reg_path : Optional[str], optional
        The dotted path name to register the function, by default this
        is derived from the relative path of the module that the function
        is defined in (e.g. sent.host.queries.my_host_queries)
    notebooklets : Optional[Union[str, List[str]]], optional
        A list of notebooklet classes to attach the function to, by default None

    Returns
    -------
    Callable
        The wrapped function.

    Notes
    -----
    The decorator does not alter the behavior of the function, it creates
    an NBFunc class that wraps the function and registers this function
    with the global notebooklets functions.

    Examples
    --------
    Function registration with several options specified.

    .. code:: python

    from msticnb.nb.azsent.host.host_summary import HostSummary
    @nb_func(
        notebooklets=[HostSummary],  # Notebooklets to add func to
        name="get_logon_data",       # Name of the function
        func_type="run",             # The type of function
        options="logons",             # The options controlling if the func is run
        header="Header displayed when func is run",
        text="Descriptive text displayed.",
        result_attrib="host_logons"  # The attribute name to add to the result.
    )
    def fetch_host_logons(timerange, **kwargs):
        ...
        return xyz.get_stuff(timerange)


    Same function with minimal options.

    .. code:: python

        from msticnb.nb.azsent.host.host_summary import HostSummary
        @nb_func(
            result_attrib="host_logons"  # The attribute name to add to the result.
        )
        def fetch_host_logons(timerange, **kwargs):
            ...
            return xyz.get_stuff(timerange)

    """

    def nb_func_wrapper(func):
        """Add the function to the set of classes."""
        qry_param_map = None
        if func_type == "query":
            # run the function to get the values specified in the body
            query_settings = func()
            if isinstance(query_settings, tuple):
                func, qry_param_map = query_settings
            else:
                func = query_settings, {}
        # create the NBFunc wrapper class.
        custom_func = NBFunc(
            func=func,
            name=name,
            func_type=func_type,
            options=options,
            header=header,
            text=text,
            result_attrib=result_attrib,
            qry_param_map=qry_param_map,
        )
        # Add it to any notebooklets defined.
        if notebooklets:
            for notebooklet in notebooklets:
                notebooklet.add_custom_func(custom_func)

        # register the NBFunc
        _register_nb_function(custom_func, reg_path or _get_default_func_path(func))
        return func

    return nb_func_wrapper


def _get_default_func_path(func) -> str:
    """Create function path from module path."""
    root_path = Path(_get_msticnb().__file__.replace("__init__.py", ""))
    func_path = Path(func.__module__.__file__)
    return ".".join(
        [*(func_path.resolve().relative_to(root_path).parts[:-1]), func_path.stem]
    )


def _get_msticnb():
    """Return root module, avoiding circular imports."""
    # pylint: disable=import-outside-toplevel, cyclic-import
    import msticnb

    return msticnb
