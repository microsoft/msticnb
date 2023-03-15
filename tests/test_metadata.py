# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""NB metadata test class."""
import pytest_check as check

from msticnb import data_providers, init, nblts
from msticnb.nb.azsent.host import host_summary
from msticnb.nb_metadata import NBMetadata, read_mod_metadata

from .unit_test_lib import GeoIPLiteMock


def test_read_metadata():
    """Tests reading metadata yaml file."""
    nb_md, docs = read_mod_metadata(host_summary.__file__, host_summary.__name__)
    check.is_instance(nb_md, NBMetadata)
    check.is_instance(docs, dict)

    opts = nb_md.get_options("all")
    check.is_in("heartbeat", [opt[0] for opt in opts])
    check.is_in("alerts", [opt[0] for opt in opts])

    for item in ("Default Options", "alerts", "azure_api"):
        check.is_in(item, nb_md.options_doc)

    for item in ("Default Options", "alerts", "azure_api"):
        check.is_in(item, nb_md.options_doc)


# pylint: disable=protected-access
def test_class_metadata(monkeypatch):
    """Test class correctly loads yaml metadata."""
    init()
    monkeypatch.setattr(data_providers, "GeoLiteLookup", GeoIPLiteMock)
    if "azuredata" in nblts.azsent.host.HostSummary.metadata.req_providers:
        nblts.azsent.host.HostSummary.metadata.req_providers.remove("azuredata")
    data_providers.init(
        query_provider="LocalData", providers=["tilookup", "geolitelookip"]
    )
    host_nb = host_summary.HostSummary()

    check.is_true(hasattr(host_summary, "_CLS_METADATA"))
    check.is_instance(host_summary._CLS_METADATA, NBMetadata)
    check.is_true(hasattr(host_summary, "_CELL_DOCS"))
    check.is_instance(host_summary._CELL_DOCS, dict)

    check.is_true(hasattr(host_nb, "metadata"))
    check.is_instance(host_nb.metadata, NBMetadata)
    check.equal(host_nb.metadata.mod_name, host_summary.__name__)
    check.equal(host_nb.description(), "Host summary")
    check.equal(host_nb.name(), "HostSummary")
    check.is_in("host", host_nb.entity_types())
    check.is_in("host", host_nb.keywords())

    check.is_in("heartbeat", host_nb.default_options())
    check.is_in("alerts", host_nb.default_options())

    check.is_in("alerts", host_nb.all_options())

    for item in ("Default Options", "alerts", "azure_api"):
        check.is_in(item, host_nb.list_options())
