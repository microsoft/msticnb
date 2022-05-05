# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Jupyter Browser for Notebooklets."""

import inspect
import re
from datetime import datetime, timedelta

import ipywidgets as widgets
from IPython import get_ipython
from IPython.display import display
from markdown import markdown

from ._version import VERSION
from .common import MsticnbError
from .read_modules import nb_index, nblts

__version__ = VERSION
__author__ = "Ian Hellen"


# pylint: disable=too-few-public-methods
class NBBrowser:
    """Interactive browser/viewer for Notebooklets."""

    def __init__(self):
        """Initialize and Display Notebooklet Browser."""
        # Define Controls
        nb_list = list(nblts.iter_classes())

        if not nb_list:
            raise MsticnbError("No notebooklets are loaded.")
        self.selected = nb_list[0][1]
        self.nb_select = widgets.Select(options=nb_list)
        nb_doc_layout = widgets.Layout(
            width="60%",
            border="1px solid lightgray",
            margin="0px 0px 0px 10px",
        )
        self.nb_doc = widgets.HTML(layout=nb_doc_layout)
        nb_details_layout = widgets.Layout(width="100%")
        self.nb_code = widgets.HTML(layout=nb_details_layout)
        self.nb_details = widgets.HTML(layout=nb_details_layout)
        self.nb_run_doc = widgets.HTML(layout=nb_details_layout)

        self.nb_select.observe(self._update_nbdetails, names="value")

        btn_insert_class = widgets.Button(description="Insert code example")
        btn_insert_class.on_click(self._insert_code)

        # Accordian Group
        nb_det_accdn = widgets.Accordion(
            children=[self.nb_details, self.nb_run_doc, self.nb_code]
        )
        nb_det_accdn.set_title(0, "Full class details")
        nb_det_accdn.set_title(1, "run() method documentation")
        nb_det_accdn.set_title(2, "Sample code")
        nb_det_accdn.selected_index = None

        # Update display based on first item in the list
        self._update_nbdetails({"new": nb_list[0][1]})

        # Widget layout
        vbox = widgets.VBox([self.nb_select, btn_insert_class])
        top_hbox = widgets.HBox([vbox, self.nb_doc])
        self._all_controls = widgets.VBox([top_hbox, nb_det_accdn])
        display(self._all_controls)

    def display(self):
        """Display the widget."""
        display(self._all_controls)

    @staticmethod
    def _get_class_index(tgt_class):
        for name, val in nb_index.items():
            if tgt_class is val:
                return name
        return None

    @staticmethod
    def _pyvar_case(in_name):
        return "_".join(
            part.lower() for part in re.split(r"([A-Z][a-z]*)", in_name) if part
        )

    def _update_nbdetails(self, change):
        nb_cls = change["new"]
        self.selected = nb_cls
        nb_html = f"<h1>{nb_cls.__name__}</h1>"
        nb_html += markdown(inspect.cleandoc(nb_cls.__doc__))
        self.nb_doc.value = nb_html
        self._populate_docs(self.nb_select.value)

    def _populate_docs(self, nb_cls):
        nb_html = nb_cls.get_help()
        self.nb_details.value = nb_html
        nb_run_html = f"<h1>{nb_cls.__name__}.run()</h1>"
        nb_run_html += markdown(nb_cls.run.__doc__)
        self.nb_run_doc.value = nb_run_html
        self.nb_code.value = (
            f"<pre><code>{self._create_code_sample(nb_cls)}</code></pre>"
        )

    _CODE_TEMPLATE = """
    from msticpy.common.timespan import TimeSpan
    # Note you can populate TimeSpan with msticpy nbwidgets.QueryTime()
    # qt = QueryTime(autodisplay=True)
    # %% New cell
    # notebooklet.run(value="158.23.4.19", timespan=TimeSpan(qt))

    {nb_instance} = nb.{nb_cls}()
    timespan = TimeSpan(start="{start}")
    {nb_instance}_rslt = {nb_instance}.run(value="my_host", timespan=timespan)

    """

    def _create_code_sample(self, nb_cls):
        start = (datetime.utcnow() - timedelta(1)).strftime("%Y-%m-%d %H:%M")
        return self._CODE_TEMPLATE.format(
            nb_instance=self._pyvar_case(nb_cls.__name__),
            nb_cls=self._get_class_index(nb_cls),
            start=start,
        )

    def _insert_code(self, change):
        del change
        code = self._create_code_sample(self.nb_select.value)
        shell = get_ipython()
        if shell:
            shell.set_next_input(code)
