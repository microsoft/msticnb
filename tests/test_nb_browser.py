# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""NB metadata test class."""
from msticnb import browse, init
from msticnb.notebooklet import Notebooklet


def test_nb_browse():
    """Test Notebooklet browser."""
    init()
    browser = browse()

    nb_list = browser.nb_select.options
    assert len(nb_list) > 6
    cls_name, cls_obj = nb_list[0]
    browser.nb_select.value = cls_obj

    selected_class = browser.selected
    assert cls_obj == selected_class
    assert browser.nb_doc.value is not None
    assert cls_obj.__name__ == cls_name
    assert cls_obj.__name__ in browser.nb_doc.value
    assert browser.nb_run_doc.value is not None
    assert browser.nb_code.value
    nb_doc = browser.nb_doc.value is not None
    nb_run_doc = browser.nb_run_doc.value
    nb_code = browser.nb_code.value

    # Select a new option
    cls_name, cls_obj = nb_list[1]
    browser.nb_select.value = cls_obj

    assert nb_list
    selected_class = browser.selected
    assert issubclass(selected_class, Notebooklet)
    assert browser.nb_doc.value is not None
    assert cls_obj.__name__ in browser.nb_doc.value
    assert browser.nb_run_doc.value is not None
    assert browser.nb_code.value is not None

    assert browser.nb_doc.value != nb_doc
    assert browser.nb_run_doc.value != nb_run_doc
    assert browser.nb_code.value != nb_code
