# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""read_modules - handles reading notebooklets modules."""
from collections import namedtuple
from functools import partial
import importlib
import inspect
from operator import itemgetter
from pathlib import Path
from typing import Iterable, Tuple, Dict, List, Union
from warnings import warn

from . import nb
from .class_doc import get_class_doc
from .common import NBContainer, MsticnbError, print_debug
from .notebooklet import Notebooklet

from ._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"

nblts: NBContainer = NBContainer()
nb_index: Dict[str, Notebooklet] = {}


def discover_modules(
    data_provider: str = "azsent", nb_path: Union[str, Iterable[str]] = None
) -> NBContainer:
    """
    Discover notebooks modules.

    Parameters
    ----------
    nb_path : Union[str, Iterable[str]], optional
        Additional path to search for notebooklets, by default None

    Returns
    -------
    NBContainer
        Container of notebooklets. This is structured
        as a tree mirroring the source folder names.
    """
    del nb_path  # TODO enable arbitrary paths

    pkg_folder = Path(__file__).parent
    dp_pkg_folder = pkg_folder / "nb" / data_provider
    _import_from_folder(dp_pkg_folder, pkg_folder)

    common_pkg_folder = pkg_folder / "nb/common"
    _import_from_folder(common_pkg_folder, pkg_folder)

    # if not nb_path:
    #     return nblts
    # if isinstance(nb_path, str):
    #     _import_from_folder(Path(nb_path))
    # elif isinstance(nb_path, list):
    #     for path_item in nb_path:
    #         _import_from_folder(Path(path_item))
    return nblts


def _import_from_folder(nb_folder: Path, parent_folder: Path):
    if not nb_folder.is_dir():
        raise MsticnbError(f"Notebooklet folder {nb_folder} not found.")

    folders = [f for f in nb_folder.glob("./**") if f.is_dir() and not f == nb_folder]
    for folder in folders:
        rel_folder_parts = folder.relative_to(nb_folder).parts
        full_rel_path_paths = folder.relative_to(parent_folder).parts
        # skip hidden folder paths with . or _ prefix
        if any([f for f in rel_folder_parts if f.startswith(".") or f.startswith("_")]):
            continue

        nb_classes = _find_cls_modules(folder)
        if not nb_classes:
            continue
        cur_container = _get_container(rel_folder_parts)
        for cls_name, nb_class in nb_classes.items():
            setattr(cur_container, cls_name, nb_class)
            cls_index = ".".join(list(full_rel_path_paths) + [cls_name])
            nb_index[cls_index] = nb_class


def _find_cls_modules(folder):
    found_classes = {}
    for item in folder.glob("*.py"):
        if item.name.startswith("_"):
            continue
        if item.is_file():
            print_debug("module to import", item)
            mod_name = "." + ".".join(list(folder.parts[-2:]) + [item.stem])
            try:
                imp_module = importlib.import_module(mod_name, package=nb.__package__)
            except ImportError as err:
                warn(f"Import failed for {item}.\n" + str(err))
                print_debug("import failed", item, err)
                continue
            mod_classes = inspect.getmembers(imp_module, inspect.isclass)
            for cls_name, mod_class in mod_classes:
                if issubclass(mod_class, Notebooklet) and not mod_class == Notebooklet:
                    print_debug("imported", cls_name)
                    mod_class.module_path = item
                    # set the function to return documentation
                    setattr(
                        mod_class, "_get_doc", partial(get_class_doc, doc_cls=mod_class)
                    )
                    found_classes[cls_name] = mod_class
    return found_classes


def _get_container(path_parts: Tuple[str, ...]) -> NBContainer:
    cur_container = nblts
    for path_item in path_parts:
        child_item = getattr(cur_container, path_item, None)
        if not child_item:
            child_item = NBContainer()
            setattr(cur_container, path_item, child_item)
        cur_container = child_item
    return cur_container


FindResult = namedtuple("FindResult", "full_match match_count, name, nb_class")


def find(keywords: str, full_match=True) -> List[Tuple[str, Notebooklet]]:
    """
    Search for Notebooklets matching key words.

    Parameters
    ----------
    keywords : str
        Space or comma-separated words to search for.
        Terms can be regular expressions.

    Returns
    -------
    List[Tuple[str, Notebooklet]]
        List of matches sorted by closest match

    Notes
    -----
    Search terms are treated as regular expressions, so any regular
    expression reserved characters will be treated as part of the
    regex pattern.

    """
    matches = []
    for name, nb_class in nblts.iter_classes():
        all_match, match_count = nb_class.match_terms(keywords)
        if all_match or (match_count and not full_match):
            matches.append(FindResult(all_match, match_count, name, nb_class))

    # return list sorted by full_match, then match count, highest to lowest
    results = sorted(matches, key=itemgetter(0, 1), reverse=True)
    return [(result[2], result[3]) for result in results]
