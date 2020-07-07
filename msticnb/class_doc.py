# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Functions to create documentation from notebooklets classes."""
import inspect
from typing import List

from markdown import markdown

from .notebooklet import Notebooklet, NotebookletResult

from ._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


def get_class_doc(doc_cls: type, fmt: str = "html") -> str:
    """
    Create HTML documentation for the notebooklet class.

    Parameters
    ----------
    doc_cls : type
        The class to document
    fmt : str
        Format = "html" or "md", by default "html"

    Returns
    -------
    str
        HTML documentation for the class

    Raises
    ------
    TypeError
        If the class is not a subclass of Notebooklet.

    """
    if not issubclass(doc_cls, Notebooklet):
        raise TypeError("doc_cls must be a type of Notebooklet")
    if fmt == "html":
        return markdown(_get_main_class_doc_md(doc_cls))
    return _get_main_class_doc_md(doc_cls)


def _get_main_class_doc_md(doc_cls) -> str:
    """Return Markdown format of class documentation."""
    cls_doc_lines = []
    cls_doc_lines.append(f"# Notebooklet Class - {doc_cls.__name__}\n")
    cls_doc_str = inspect.getdoc(doc_cls)
    if cls_doc_str:
        fmt_doc_lines: List[str] = []
        for idx, doc_line in enumerate(inspect.cleandoc(cls_doc_str).split("\n")):
            if doc_line.strip().startswith("--") and idx > 0:
                # if this is a heading underline, bold the previous line
                fmt_doc_lines[idx - 1] = f"**{fmt_doc_lines[idx - 1]}**"
                fmt_doc_lines.append("")
            else:
                fmt_doc_lines.append(doc_line + "\n")
        cls_doc_lines.extend(fmt_doc_lines)
    cls_doc_lines.append("\n---\n")

    cls_doc_lines.append("# Display Sections")
    for _, func in inspect.getmembers(doc_cls, inspect.isfunction):
        cls_doc_lines.extend(_get_closure_vars(func, doc_cls))

    for _, func in inspect.getmembers(inspect.getmodule(doc_cls), inspect.isfunction):
        cls_doc_lines.extend(_get_closure_vars(func, doc_cls))

    cls_doc_lines.append("\n---\n")
    cls_doc_lines.append("# Results Class\n")
    for cls_name, cls in inspect.getmembers(
        inspect.getmodule(doc_cls), inspect.isclass
    ):
        if issubclass(cls, NotebookletResult) and cls is not NotebookletResult:
            cls_doc_lines.append(f"## {cls_name}\n")
            cls_doc_lines.append(_get_result_doc(cls))
            break
    cls_doc_lines.append("\n---\n")
    cls_doc_lines.append("# Methods")
    cls_doc_lines.append("## Instance Methods")
    cls_doc_lines.append(_get_class_methods_doc(doc_cls))
    cls_doc_lines.append("## Other Methods")
    cls_doc_lines.append(_get_class_func_doc(doc_cls))
    return "\n".join(cls_doc_lines)


def _get_closure_vars(func, doc_cls) -> List[str]:
    """Return title and text from function args."""
    cls_doc_lines = []
    closure_args = inspect.getclosurevars(func).nonlocals

    # If the function is using the metadata docs and key
    # try to fetch that from the class module
    docs = closure_args.get("docs")
    key = closure_args.get("key")
    other_items = None
    if docs and key and issubclass(doc_cls, Notebooklet):
        cell_docs = getattr(doc_cls, "_cell_docs", None)
        if cell_docs:
            title = cell_docs.get(key, {}).get("title")
            text = cell_docs.get(key, {}).get("text")
            hd_level = cell_docs.get(key, {}).get("hd_level", 2) + 1
            other_items = {
                hdr: str(text)
                for hdr, text in docs.get(key, {}).items()
                if hdr not in ("title", "text", "hd_level", "md")
            }
    else:
        # Otherwise use inline parameters
        title = closure_args.get("title")
        hd_level = closure_args.get("hd_level", 2) + 1
        text = closure_args.get("text")
    if title:
        cls_doc_lines.append(("#" * hd_level) + f" {title}\n")
        if text:
            cls_doc_lines.append(text)
    if other_items:
        for name, content in other_items.items():
            cls_doc_lines.append(f"**{name}**\n{content}")
    return cls_doc_lines


def _get_result_doc(cls) -> str:
    """Return Markdown documentation for Result class."""
    attr_section = False
    doc_lines = []
    cls_doc_str = inspect.getdoc(cls)
    if not cls_doc_str:
        return ""
    for line in inspect.cleandoc(cls_doc_str).split("\n"):
        if line.startswith("---"):
            attr_section = True

        elif attr_section:
            if not line.startswith(" "):
                line = "\n- " + line + "<br>"
            else:
                line = line.strip()
        doc_lines.append(line)
    return "\n".join(doc_lines)


def _get_class_methods_doc(doc_cls: type) -> str:
    """Get class instance methods."""
    doc_lines: List[str] = []
    for func_name, func in inspect.getmembers(doc_cls, inspect.isfunction):
        if not func_name.startswith("_"):
            doc_lines.extend(_format_func_doc(func_name, func, True))
    return "\n".join(doc_lines)


def _get_class_func_doc(doc_cls: type) -> str:
    """Get class functions (class methods and properties)."""
    doc_lines: List[str] = []
    prop_set = {
        f_name
        for f_name, _ in inspect.getmembers(doc_cls, lambda f: isinstance(f, property))
    }

    def member_crit(member):
        return inspect.ismethod(member) or isinstance(member, property)

    for func_name, func in inspect.getmembers(doc_cls, member_crit):
        if not func_name.startswith("_"):
            doc_lines.extend(_format_func_doc(func_name, func, False, prop_set))
    return "\n".join(doc_lines)


def _format_func_doc(func_name, func, full_doc=False, prop_set=None):
    """Format function signature."""
    doc_lines = []
    doc_lines.append(f"### {func_name}\n")
    if prop_set and func_name in prop_set:
        doc_lines.append(f"{func_name} [property]")
    else:
        doc_lines.append(f"{func_name}{inspect.signature(func)}")

    func_doc = inspect.getdoc(func)
    if func_doc:
        if not full_doc:
            # Get the first line of the doc string
            doc_lines.append(func_doc.split("\n")[0])
            return doc_lines

        func_doc = inspect.cleandoc(func_doc).split("\n")[0]
    if func_doc:
        refmt_headings = []
        for doc_line in func_doc.split("\n"):
            if doc_line.startswith("### "):
                refmt_headings.append(doc_line.replace("### ", "##### "))
            elif doc_line.startswith("## "):
                refmt_headings.append(doc_line.replace("## ", "#### "))
            else:
                refmt_headings.append(doc_line + "\n")
        doc_lines.extend(refmt_headings)
    return doc_lines
