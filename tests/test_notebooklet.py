# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""common test class."""
# from contextlib import redirect_stdout
from contextlib import redirect_stdout
from io import StringIO

import pandas as pd
import pytest
import pytest_check as check
from lxml import etree  # nosec
from markdown import markdown
from msticpy.common.timespan import TimeSpan

from msticnb import data_providers, init, nblts
from msticnb.common import MsticnbDataProviderError
from msticnb.nb.azsent.host.host_summary import HostSummaryResult
from msticnb.read_modules import Notebooklet

from .nb_test import TstNBSummary
from .unit_test_lib import GeoIPLiteMock

# pylint: disable=c-extension-no-member, protected-access


def test_notebooklet_create(monkeypatch):
    """Test method."""
    # Should run because required providers are loaded
    init()
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    data_providers.init(
        query_provider="LocalData", providers=["tilookup", "geolitelookup"]
    )
    for _, nblt in nblts.iter_classes():
        new_nblt = nblt()
        check.is_instance(new_nblt, Notebooklet)
        check.is_none(new_nblt.result)

    # Should throw a warning because of unrecognized provider
    data_providers.init(query_provider="LocalData")
    with pytest.raises(MsticnbDataProviderError) as err:
        for _, nblt in nblts.iter_classes():
            curr_provs = nblt.metadata.req_providers
            bad_provs = [*curr_provs, "bad_provider"]
            try:
                nblt.metadata.req_providers = bad_provs
                new_nblt = nblt()
                check.is_instance(new_nblt, Notebooklet)
                check.is_none(new_nblt.result)
            except MsticnbDataProviderError:
                raise
            finally:
                nblt.metadata.req_providers = curr_provs
    check.is_in("bad_provider", err.value.args[0])
    test_nb = TstNBSummary()
    check.is_not_none(test_nb.get_provider("LocalData"))
    with pytest.raises(MsticnbDataProviderError):
        test_nb.get_provider("otherprovider")


def test_notebooklet_params(monkeypatch):
    """Test supplying timespan param."""
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    data_providers.init(
        query_provider="LocalData", providers=["tilookup", "geolitelookup"]
    )
    test_nb = TstNBSummary()

    tspan = TimeSpan(period="1D")
    test_nb.run(timespan=tspan)
    check.equal(tspan, test_nb.timespan)

    test_nb.run(start=tspan.start, end=tspan.end)
    check.equal(tspan, test_nb.timespan)


def test_notebooklet_options(monkeypatch):
    """Test option logic for notebooklet."""
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    data_providers.init(
        query_provider="LocalData", providers=["tilookup", "geolitelookup"]
    )
    nb_test = TstNBSummary()

    # default options
    nb_res = nb_test.run()
    check.is_not_none(nb_res.default_property)
    check.is_none(nb_res.optional_property)

    # add optional option
    nb_res = nb_test.run(options=["+optional_opt"])
    check.is_not_none(nb_res.default_property)
    check.is_not_none(nb_res.optional_property)

    # remove default option
    nb_res = nb_test.run(options=["-default_opt"])
    check.is_none(nb_res.default_property)
    check.is_none(nb_res.optional_property)

    # specific options
    nb_res = nb_test.run(options=["heartbest", "azure_net"])
    check.is_none(nb_res.default_property)
    check.is_none(nb_res.optional_property)

    # invalid option
    f_stream = StringIO()
    with redirect_stdout(f_stream):
        nb_test.run(options=["invalid_opt"])
    output = str(f_stream.getvalue())
    check.is_in("Invalid options ['invalid_opt']", output)


def test_class_doc():
    """Test class documentation."""
    for _, nblt in nblts.iter_classes():
        html_doc = nblt.get_help()
        check.not_equal(html_doc, "No documentation available.")
        check.greater(len(html_doc), 100)

        md_doc = nblt.get_help(fmt="md")
        html_doc2 = markdown(md_doc)
        check.equal(html_doc, html_doc2)

        _html_parser = etree.HTMLParser(recover=False)
        elem_tree = etree.parse(StringIO(html_doc), _html_parser)
        check.is_not_none(elem_tree)


def test_class_methods():
    """Test method."""
    for _, nblt in nblts.iter_classes():
        check.is_not_none(nblt.description())
        check.is_not_none(nblt.name())
        all_opts = len(nblt.all_options())
        check.greater_equal(all_opts, len(nblt.default_options()))
        check.greater(len(nblt.keywords()), 0)
        check.greater(len(nblt.entity_types()), 0)
        metadata = nblt.get_settings(print_settings=False)
        check.is_not_none(metadata)
        check.is_in("mod_name", metadata)
        check.is_in("default_options", metadata)
        check.is_in("keywords", metadata)


def test_nbresult():
    """Test method."""
    host_result = HostSummaryResult()
    host_result.host_entity = {"host_name": "myhost"}
    host_result.related_alerts = pd.DataFrame()
    host_result.related_bookmarks = pd.DataFrame()
    check.is_in("host_entity:", str(host_result))
    check.is_in("DataFrame:", str(host_result))
    check.is_in("host_entity", host_result.properties)

    html_doc = host_result._repr_html_()
    _html_parser = etree.HTMLParser(recover=False)
    elem_tree = etree.parse(StringIO(html_doc), _html_parser)
    check.is_not_none(elem_tree)
