# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""common test class."""
import io
import warnings
from contextlib import redirect_stdout

import pytest
import pytest_check as check

from msticnb import init, options
from msticnb.common import add_result, nb_data_wait, nb_debug, nb_print
from msticnb.options import get_opt, set_opt

from .nb_test import TstNBSummary

# pylint: disable=too-many-statements


def test_print_methods():
    """Test method."""
    set_opt("verbose", True)
    f_stream = io.StringIO()
    with redirect_stdout(f_stream):
        nb_print("status")
        nb_data_wait("table1")
    check.is_in("status", str(f_stream.getvalue()))
    check.is_in("Getting data from table1", str(f_stream.getvalue()))

    set_opt("verbose", False)
    f_stream = io.StringIO()
    with redirect_stdout(f_stream):
        nb_print("status")
    check.is_not_in("status", str(f_stream.getvalue()))
    check.is_not_in("Getting data from table1", str(f_stream.getvalue()))

    set_opt("debug", True)
    f_stream = io.StringIO()
    with redirect_stdout(f_stream):
        nb_debug("debug", "debugmssg", "val", 1, "result", True)
    check.is_in("debug", str(f_stream.getvalue()))
    check.is_in("debugmssg", str(f_stream.getvalue()))
    check.is_in("val", str(f_stream.getvalue()))
    check.is_in("1", str(f_stream.getvalue()))
    check.is_in("result", str(f_stream.getvalue()))
    check.is_in("True", str(f_stream.getvalue()))


def test_add_result_decorator():
    """Test method."""

    # pylint: disable=too-few-public-methods
    class _TestClass:
        prop1 = None
        prop2 = None

    test_obj = _TestClass()

    @add_result(result=test_obj, attr_name=["prop1", "prop2"])
    def test_func():
        return "result1", 10

    test_func()
    check.equal("result1", test_obj.prop1)
    check.equal(10, test_obj.prop2)


def test_options():
    """Test method."""
    set_opt("verbose", True)
    f_stream = io.StringIO()
    with redirect_stdout(f_stream):
        options.current()
    check.is_in("verbose: True", str(f_stream.getvalue()))

    f_stream = io.StringIO()
    with redirect_stdout(f_stream):
        options.show()
    check.is_in(
        "verbose (default=True): Show progress messages.", str(f_stream.getvalue())
    )

    with pytest.raises(KeyError):
        get_opt("no_option")

    with pytest.raises(KeyError):
        set_opt("no_option", "value")

    # This will work since bool(10) == True
    set_opt("verbose", 10)


def _capture_nb_run_output(test_nb, **kwargs):
    f_stream = io.StringIO()
    with redirect_stdout(f_stream):
        test_nb.run(**kwargs)
    return str(f_stream.getvalue())


def test_silent_option():
    """Test operation of 'silent' option."""
    warnings.filterwarnings(action="ignore", category=UserWarning)
    init(query_provider="LocalData", providers=[])
    test_nb = TstNBSummary()

    output = _capture_nb_run_output(test_nb)
    check.is_true(output)

    # Silent option to run
    output = _capture_nb_run_output(test_nb, silent=True)
    check.is_false(output)
    check.is_true(get_opt("silent"))

    # Silent option to init
    test_nb = TstNBSummary(silent=True)
    check.is_true(test_nb.silent)
    output = _capture_nb_run_output(test_nb)
    check.is_false(output)

    # But overridable on run
    output = _capture_nb_run_output(test_nb, silent=False)
    check.is_true(output)
    check.is_false(get_opt("silent"))

    # Silent global option
    set_opt("silent", True)
    test_nb = TstNBSummary()
    output = _capture_nb_run_output(test_nb)
    check.is_false(output)

    # But overridable on run
    output = _capture_nb_run_output(test_nb, silent=False)
    check.is_true(output)
