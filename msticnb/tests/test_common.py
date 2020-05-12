# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""common test class."""
from contextlib import redirect_stdout
from datetime import datetime, timedelta
import io
import unittest

from ..common import (
    TimeSpan,
    MsticnbMissingParameterError,
    add_result,
    print_data_wait,
    print_debug,
    print_status,
)
from .. import options
from ..options import get_opt, set_opt


class TestCommon(unittest.TestCase):
    """Unit test class."""

    def test_timespan(self):
        """Test method."""
        end = datetime.utcnow()
        period = timedelta(days=1)
        start = end - period
        tspan = TimeSpan(start=start, end=end)
        self.assertEqual(start, tspan.start)
        self.assertEqual(end, tspan.end)

        tspan = TimeSpan(end=end, period=period)
        self.assertEqual(start, tspan.start)
        self.assertEqual(end, tspan.end)

        tspan = TimeSpan(end=end, period="1D")
        self.assertEqual(start, tspan.start)
        self.assertEqual(end, tspan.end)

        tspan = TimeSpan(end=str(end), period="1D")
        self.assertEqual(start, tspan.start)
        self.assertEqual(end, tspan.end)

        tspan = TimeSpan(start=str(start), end=str(end))
        self.assertEqual(start, tspan.start)
        self.assertEqual(end, tspan.end)

        tspan = TimeSpan(start=str(start), period="1D")
        self.assertEqual(start, tspan.start)
        self.assertEqual(end, tspan.end)

        # end is set to utcnow()
        tspan = TimeSpan(start=start)
        self.assertEqual(start, tspan.start)

        # end is set to utcnow()
        tspan = TimeSpan(period=period)
        self.assertEqual(period, tspan.period)

        end_str = str(end)

        # pylint: disable=too-few-public-methods
        class _TestTime:
            start = None
            end = None
            period = None

        test_t = _TestTime()
        test_t.start = start
        test_t.end = end_str
        test_t.period = "1D"

        tspan = TimeSpan(time_selector=test_t)
        self.assertEqual(start, tspan.start)
        self.assertEqual(end, tspan.end)

        with self.assertRaises(MsticnbMissingParameterError):
            TimeSpan()
        with self.assertRaises(ValueError):
            TimeSpan(start="foo", period=period)
        with self.assertRaises(MsticnbMissingParameterError):
            TimeSpan(start=None, end=None)
        with self.assertRaises(ValueError):
            TimeSpan(period="some length")
        with self.assertRaises(ValueError):
            TimeSpan(period=1)

    def test_print_methods(self):
        """Test method."""
        set_opt("verbose", True)
        f_stream = io.StringIO()
        with redirect_stdout(f_stream):
            print_status("status")
            print_data_wait("table1")
        self.assertIn("status", str(f_stream.getvalue()))
        self.assertIn("Getting data from table1", str(f_stream.getvalue()))

        set_opt("verbose", False)
        f_stream = io.StringIO()
        with redirect_stdout(f_stream):
            print_status("status")
        self.assertNotIn("status", str(f_stream.getvalue()))
        self.assertNotIn("Getting data from table1", str(f_stream.getvalue()))

        set_opt("debug", True)
        f_stream = io.StringIO()
        with redirect_stdout(f_stream):
            print_debug("debug", "debugmssg", "val", 1, "result", True)
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
