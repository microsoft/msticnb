# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklet templates module."""
import os
from pathlib import Path
from typing import Optional, Union

from msticpy.common.utility import valid_pyname

from .nb.template import nb_template

_BLACK_IMPORTED = True
try:
    import black
except ImportError:
    _BLACK_IMPORTED = False


DELETE_LINES = [
    '# change the ".." to "...."',
    "from ..._version import VERSION",
    "# Note - when moved to the final location (e.g.",
    "# nb/environ/category/mynotebooklet.py)",
    '# you will need to change the "..." to "...." in these',
    "# imports because the relative path has changed.",
    '# change the "..." to "...."',
]

REPLACE_TEXT = {
    "from ... import nb_metadata": "from msticnb import nb_metadata",
    "from ...common import (": "from msticnb.common import (",
    "from ...notebooklet import": "from msticnb.notebooklet import",
    "__version__ = VERSION": '__version__ = "1.0"',
    '__author__ = "Your name"': '__author__ = "{author}"',
    "TemplateResult": "{nb_name}Result",
    "Template Results.": "{nb_name} Results.",
    "TemplateNB": "{nb_name}",
    "Template Notebooklet class": "{nb_name} Notebooklet class",
}


def create_template(
    nb_name: str = "MyNotebooklet",
    folder: Union[str, Path] = ".",
    author: Optional[str] = None,
    subfolder: bool = False,
    overwrite: bool = False,
):
    """
    Create a notebooklet template.

    Parameters
    ----------
    nb_name : str, optional
        The name of the notebooklet class, by default "MyNotebooklet"
    folder : Union[str, Path], optional
        The target folder for the notebooklet, by default "."
    author : str, optional
        Author name to put in the notebooklet Python module, by default None
    subfolder : bool, optional
        If True create a subfolder for the notebooklet, by default False
    overwrite : bool, optional
        If True overwrite existing files with the same name, by default False.

    """
    author = author or os.environ.get("USER") or os.environ.get("USERNAME") or "Author"
    nb_name = valid_pyname(nb_name)
    folder = Path(folder)
    output_template = _edit_template(nb_name, author)

    target_name = nb_name.casefold()
    # Create folder
    if not Path(folder).is_absolute():
        # If the folder is already the name of the notebooklet,
        folder = Path(".").joinpath(folder).resolve()

    if subfolder:
        folder = folder.joinpath(target_name)
    folder.mkdir(parents=True, exist_ok=True)

    # write files
    print(f"Creating files in {folder}: ")
    py_file = folder.joinpath(f"{target_name}.py")
    if not py_file.is_file() or overwrite:
        py_file.write_text(output_template, encoding="utf-8")
        print(py_file.name, end=", ")
    else:
        print(py_file.name, "not overwritten", end=", ")

    yaml_text = _edit_yaml(nb_name)
    yaml_file = folder.joinpath(f"{target_name}.yaml")
    if not yaml_file.is_file() or overwrite:
        yaml_file.write_text(yaml_text, encoding="utf-8")
        print(yaml_file.name, end=", ")
    else:
        print(yaml_file.name, "not overwritten", end=", ")
    init_file = folder.joinpath("__init__.py")
    if not init_file.is_file():
        init_file.write_text("", encoding="utf-8")
        print(init_file.name, end="")
    else:
        print(init_file.name, "exists - skipping", end="")
    print()


def _edit_template(nb_name: str, author: str) -> str:
    src_template = Path(nb_template.__file__).read_text(encoding="utf-8")

    output_template = "\n".join(
        line for line in src_template.split("\n") if line not in DELETE_LINES
    )

    for src, repl in REPLACE_TEXT.items():
        repl_text = repl.format(nb_name=nb_name, author=author)
        output_template = output_template.replace(src, repl_text)

    if _BLACK_IMPORTED:
        return black.format_str(output_template, mode=black.Mode())
    return output_template


def _edit_yaml(nb_name: str) -> str:
    yaml_text = (
        Path(nb_template.__file__).with_suffix(".yaml").read_text(encoding="utf-8")
    )
    yaml_text = yaml_text.replace("TemplateNB", nb_name).replace(
        "Template YAML for Notebooklet", f"YAML for {nb_name} Notebooklet"
    )
    return yaml_text
