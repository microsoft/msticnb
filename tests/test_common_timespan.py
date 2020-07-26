# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""common test class."""
from datetime import datetime, timedelta
import unittest

from msticnb.common import TimeSpan, MsticnbMissingParameterError


class TestCommon(unittest.TestCase):
    """Unit test class."""

    def _validate_timespan(self, timespan, start=None, end=None, period=None):
        if start is not None:
            self.assertEqual(start, timespan.start)
        if end is not None:
            self.assertEqual(end, timespan.end)
        if period is not None:
            self.assertEqual(period, timespan.period)

    def test_timespan_parms(self):
        """Test standard parameters."""
        end = datetime.utcnow()
        period = timedelta(days=1)
        start = end - period
        tspan = TimeSpan(start=start, end=end)
        self._validate_timespan(tspan, start, end)

        tspan = TimeSpan(end=end, period=period)
        self._validate_timespan(tspan, start, end)

        tspan = TimeSpan(end=end, period="1D")
        self._validate_timespan(tspan, start, end)

        tspan = TimeSpan(end=str(end), period="1D")
        self._validate_timespan(tspan, start, end)

        tspan = TimeSpan(start=str(start), end=str(end))
        self._validate_timespan(tspan, start, end)

        tspan = TimeSpan(start=str(start), period="1D")
        self._validate_timespan(tspan, start, end)

        # end is set to utcnow()
        tspan = TimeSpan(start=start)
        self._validate_timespan(tspan, start)

        # end is set to utcnow()
        tspan = TimeSpan(period=period)
        self._validate_timespan(tspan, period=period)

    def test_timespan_eq(self):
        """Test creating Timespan from another Timespan."""
        period = timedelta(days=1)
        tspan = TimeSpan(period=period)

        # Timespan object as a parameter
        tspan2 = TimeSpan(timespan=tspan)
        self.assertEqual(tspan2, tspan)
        self.assertEqual(hash(tspan2), hash(tspan))

        tspan2 = TimeSpan(timespan=(tspan.start, tspan.end))
        self.assertEqual(tspan2, tspan)
        tspan2 = TimeSpan(timespan=(str(tspan.start), str(tspan.end)))
        self.assertEqual(tspan2, tspan)

    def test_timespan_timeselector(self):
        """Test timespan with a time selector object."""
        end = datetime.utcnow()
        period = timedelta(days=1)
        start = end - period
        tspan = TimeSpan(period=period)

        # pylint: disable=too-few-public-methods
        class _TestTime:
            """Class to emulate QueryTimes widget. etc."""

            start = None
            end = None
            period = None

        test_t = _TestTime()
        test_t.start = start
        test_t.end = str(end)
        test_t.period = "1D"

        tspan = TimeSpan(timespan=test_t)
        self._validate_timespan(tspan, start, end)

    def test_timespan_invalid_params(self):
        """Test error handling for invalid params."""
        period = timedelta(days=1)
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
