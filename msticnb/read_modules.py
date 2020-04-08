# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""read_modules - handles reading noebooklets modules."""
from collections import defaultdict
import importlib
import inspect
from pathlib import Path
from typing import Iterable, List, Set, Tuple

from msticpy.data.data_providers import AttribHolder

from . import nb
from .common import Notebooklet, NotebookletResult, NotebookletException


_nb_list: List[AttribHolder] = []
_nb_index: defaultdict = defaultdict(set)


def discover_modules():
    # iterate through folder
    nb_folder = Path(__file__).parent / "nb"
    folders = [
        f
        for f in nb_folder.glob("./**")
        if f.is_dir() and not str(f).startswith(".") and not f == nb_folder
    ]
    for folder in folders:
        rel_folder_parts = folder.relative_to(nb_folder).parts
        cur_container = _get_container(rel_folder_parts)
        for nb_class in _search_folder(folder):
            setattr(
                cur_container, nb_class.__name__,
            )


def _search_folder(folder):
    found_classes = {}
    for item in folder.glob("*.py"):
        if item.is_file():
            mod_name = "." + ".".join(list(folder.parts[-1:]) + [item.stem])
            try:
                imp_module = importlib.import_module(mod_name, package=nb.__package__)
            except ImportError:
                continue
            mod_classes = inspect.getmembers(imp_module, inspect.isclass)
            for cls_name, mod_class in mod_classes:
                if issubclass(mod_class, Notebooklet) and not mod_class == Notebooklet:
                    print("notebooklet subclass", mod_class.__name__)
                    found_classes[cls_name] = mod_class
                if (
                    issubclass(mod_class, NotebookletResult)
                    and not mod_class == NotebookletResult
                ):
                    print("notebooklet result subclass", mod_class.__name__)
                    found_classes[cls_name] = mod_class
        else:
            print("ignored", item)
    return found_classes


def _get_class_metadata(nb_class):
    cls_metadata = getattr(nb_class, "metadata", None)
    if not cls_metadata:
        raise NotebookletException(f"No metadata found for class {nb_class.__name__}")

    for term in cls_metadata.search_terms:
        _nb_index[term].add(nb_class)


def _get_container(path_parts: Tuple) -> AttribHolder:
    cur_container = _nb_list
    for path_item in path_parts:
        child_item = getattr(cur_container, path_item)
        if not child_item:
            child_item = AttribHolder()
            setattr(cur_container, path_item, child_item)
        cur_container = child_item
    return cur_container


def find_nbs(keywords: Iterable[str]):
    # search metadata
    # keep track of how many hits for each keyword
    # order results by hits
    matching_nbs: Set[Notebooklet] = set()
    for keyword in keywords:
        matching_nbs.update(_nb_index.get(keyword, []))

    return matching_nbs
