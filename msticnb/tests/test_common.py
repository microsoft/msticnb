# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""common test class."""
from contextlib import redirect_stdout
import io
import unittest
import warnings

from ..common import add_result, nb_data_wait, nb_debug, nb_print
from .. import options, init
from ..options import get_opt, set_opt
from .nb_test import TstNBSummary


# pylint: disable=too-many-statements


class TestCommon(unittest.TestCase):
    """Unit test class."""

    def test_print_methods(self):
        """Test method."""
        set_opt("verbose", True)
        f_stream = io.StringIO()
        with redirect_stdout(f_stream):
            nb_print("status")
            nb_data_wait("table1")
        self.assertIn("status", str(f_stream.getvalue()))
        self.assertIn("Getting data from table1", str(f_stream.getvalue()))

        set_opt("verbose", False)
        f_stream = io.StringIO()
        with redirect_stdout(f_stream):
            nb_print("status")
        self.assertNotIn("status", str(f_stream.getvalue()))
        self.assertNotIn("Getting data from table1", str(f_stream.getvalue()))

        set_opt("debug", True)
        f_stream = io.StringIO()
        with redirect_stdout(f_stream):
            nb_debug("debug", "debugmssg", "val", 1, "result", True)
        self.assertIn("debug", str(f_stream.getvalue()))
        self.assertIn("debugmssg", str(f_stream.getvalue()))
        self.assertIn("val", str(f_stream.getvalue()))
        self.assertIn("1", str(f_stream.getvalue()))
        self.assertIn("result", str(f_stream.getvalue()))
        self.assertIn("True", str(f_stream.getvalue()))

    def test_add_result_decorator(self):
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
        self.assertEqual("result1", test_obj.prop1)
        self.assertEqual(10, test_obj.prop2)

    def test_options(self):
        """Test method."""
        set_opt("verbose", True)
        f_stream = io.StringIO()
        with redirect_stdout(f_stream):
            options.current()
        self.assertIn("verbose: True", str(f_stream.getvalue()))

        f_stream = io.StringIO()
        with redirect_stdout(f_stream):
            options.show()
        self.assertIn(
            "verbose (default=True): Show progress messages.", str(f_stream.getvalue())
        )

        with self.assertRaises(KeyError):
            get_opt("no_option")

        with self.assertRaises(KeyError):
            set_opt("no_option", "value")

        # This will work since bool(10) == True
        set_opt("verbose", 10)

    @staticmethod
    def _capture_nb_run_output(test_nb, **kwargs):
        f_stream = io.StringIO()
        with redirect_stdout(f_stream):
            test_nb.run(**kwargs)
        return str(f_stream.getvalue())

    def test_silent_option(self):
        """Test operation of 'silent' option."""
        warnings.filterwarnings(action="ignore", category=UserWarning)
        init(query_provider="LocalData", providers=[])
        test_nb = TstNBSummary()

        output = self._capture_nb_run_output(test_nb)
        self.assertTrue(output)

        # Silent option to run
        output = self._capture_nb_run_output(test_nb, silent=True)
        self.assertFalse(output)
        self.assertTrue(get_opt("silent"))

        # Silent option to init
        test_nb = TstNBSummary(silent=True)
        self.assertTrue(test_nb.silent)
        output = self._capture_nb_run_output(test_nb)
        self.assertFalse(output)

        # But overridable on run
        output = self._capture_nb_run_output(test_nb, silent=False)
        self.assertTrue(output)
        self.assertFalse(get_opt("silent"))

        # Silent global option
        set_opt("silent", True)
        test_nb = TstNBSummary()
        output = self._capture_nb_run_output(test_nb)
        self.assertFalse(output)

        # But overridable on run
        output = self._capture_nb_run_output(test_nb, silent=False)
        self.assertTrue(output)
