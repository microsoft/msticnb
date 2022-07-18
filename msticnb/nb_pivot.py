# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Add notebooklets as pivot functions."""
from functools import wraps
from typing import Any, Callable, Dict

from msticpy.common.timespan import TimeSpan

try:
    from msticpy.init.pivot import Pivot, PivotRegistration
except ImportError:
    # Fall back to msticpy locations prior to v2.0.0
    from msticpy.datamodel.pivot import Pivot, PivotRegistration

from ._version import VERSION
from .notebooklet import Notebooklet
from .read_modules import nblts

__version__ = VERSION
__author__ = "Ian Hellen"


_ENTITY_MAP = {
    "host": {"Host": "HostName"},
    "account": {"Account": "Name"},
    "ip_address": {"IpAddress": "Address"},
    "alert": {"Alert": "AlertType"},
}


def _to_py_name(name: str) -> str:
    func_name = "".join(char if char.islower() else f"_{char.lower()}" for char in name)
    return func_name.strip("_")


def add_pivot_funcs(pivot: Pivot = None, **kwargs):
    """
    Add notebooklet run functions as pivot methods.

    Parameters
    ----------
    pivot : Pivot, optional
        Pivot instance.
    kwargs : Dict[str, Any]
        Optional keyword arguments to pass to Pivot init.

    """
    if not pivot:
        piv_kwargs = {
            key: arg for key, arg in kwargs.items() if key in ("namespace", "providers")
        }
        pivot = Pivot.current() or Pivot(**piv_kwargs)
    for nb_name, nb_class in nblts.iter_classes():
        if not issubclass(nb_class, Notebooklet) or nb_name == "TemplateNB":
            continue
        if "value" not in nb_class.metadata.inputs:
            # This doesn't take a "value" input so can't use as a pivot
            continue
        nb_obj = nb_class()
        run_func = getattr(nb_obj, "run")
        pivot_timespan = pivot.get_timespan

        wrp_func = _wrap_run_func(run_func, pivot_timespan)
        func_new_name = _to_py_name(nb_name)
        entity_map: Dict[str, str] = {}
        for entity in nb_class.metadata.entity_types:
            if entity not in _ENTITY_MAP:
                continue
            entity_map.update(_ENTITY_MAP[entity])

        if not entity_map:
            continue

        piv_reg = PivotRegistration(
            input_type="value",
            entity_map=entity_map,
            func_new_name=func_new_name,
            src_func_name="run",
            can_iterate=False,
            func_input_value_arg="value",
            return_raw_output=True,
        )
        Pivot.add_pivot_function(func=wrp_func, pivot_reg=piv_reg, container="nblt")


def _wrap_run_func(func: Callable[[Any], Any], get_time_span: Callable[[], TimeSpan]):
    """Wrap function to inject timespan."""

    @wraps(func)
    def _wrapped_func(*args, **kwargs):
        time_span = get_time_span()
        kwargs.update({"timespan": time_span})
        return func(*args, **kwargs)

    return _wrapped_func
