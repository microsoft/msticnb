# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""read_modules - handles reading notebooklets modules."""
import importlib
import inspect
import sys
from collections import namedtuple
from functools import partial
from operator import itemgetter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Type, Union
from warnings import warn

from . import nb
from ._version import VERSION
from .class_doc import get_class_doc
from .common import MsticnbError, NBContainer, nb_debug
from .notebooklet import Notebooklet

__version__ = VERSION
__author__ = "Ian Hellen"

nblts: NBContainer = NBContainer()
nb_index: Dict[str, Type[Notebooklet]] = {}


def discover_modules(nb_path: Union[str, Iterable[str], None] = None) -> NBContainer:
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
    pkg_folder = Path(__file__).parent
    nb_folder = pkg_folder / "nb"
    _import_from_folder(nb_folder, pkg_folder)

    # Import from user-defined folders
    if not nb_path:
        return nblts
    if isinstance(nb_path, str):
        nb_path = [nb_path]
    if isinstance(nb_path, list):
        for path_item in nb_path:
            # For custom notebooklets, we need to add the path
            # to the source folder to sys.path so that import can
            # find and import them.
            cust_nb_path = Path(path_item).resolve()
            sys.path.append(str(cust_nb_path.parent))
            _import_from_folder(cust_nb_path, cust_nb_path)
    return nblts


def _import_from_folder(nb_folder: Path, pkg_folder: Path):
    """Search folder and import any notebooklets found."""
    if not nb_folder.is_dir():
        raise MsticnbError(f"Notebooklet folder {nb_folder} not found.")

    # if we are importing notebooklets from outside this package, we
    # specify customer_container to put them in their own subtree.
    custom_container = pkg_folder.stem if pkg_folder.stem != __package__ else ""

    # Iterate through folder and all subfolders
    folders = [
        nb_folder,
        *(f for f in nb_folder.glob("./**") if f.is_dir() and f != nb_folder),
    ]
    for folder in folders:
        rel_folder_parts = folder.relative_to(nb_folder).parts
        # skip hidden folder paths with . or _ prefix
        if any(f for f in rel_folder_parts if f.startswith(".") or f.startswith("_")):
            continue

        # Get any notebooklets from the files in the folder
        nb_classes = _find_cls_modules(folder, pkg_folder)
        if not nb_classes:
            continue
        # Get the container to add these classes to the container
        # tree
        cur_container = _get_container(custom_container, rel_folder_parts)
        for cls_name, nb_class in nb_classes.items():
            setattr(cur_container, cls_name, nb_class)
            cls_index = "nblts." + ".".join(list(rel_folder_parts) + [cls_name])
            nb_index[cls_index] = nb_class


def _find_cls_modules(folder: Path, pkg_folder: Path) -> Dict[str, Type[Notebooklet]]:
    """
    Import .py files in `folder` and return any Notebooklet classes found.

    Parameters
    ----------
    folder : Path
        The folder to search
    pkg_folder : Path
        The root path for the package

    Returns
    -------
    Dict[str, type(Notebooklet)]
        Notebooklets classes (name, class)

    """
    found_classes = {}
    pkg_root = pkg_folder.resolve().parent
    try:
        relative_path = folder.relative_to(pkg_root)
        # This may fail if environment messes around with package paths
        # - this happens in Spark/Synapse
    except ValueError:
        relative_path = _get_pkg_relative_folder(folder)
    for item in folder.glob("*.py"):
        if item.name.startswith("_"):
            continue
        if item.is_file():
            # Create full package path for item
            mod_name = ".".join(list(relative_path.parts) + [item.stem])
            nb_debug("module to import", item, mod_name)
            # Try to import the module into this package
            try:
                imp_module = importlib.import_module(mod_name, package=nb.__package__)
            except ImportError as err:
                warn(f"Import failed for {item}.\n {err}")
                nb_debug("import failed", item, err)
                continue
            # extract the classes in the module and look for any classes
            # derived from Notebooklet
            mod_classes = inspect.getmembers(imp_module, inspect.isclass)
            for cls_name, mod_class in mod_classes:
                if issubclass(mod_class, Notebooklet) and mod_class != Notebooklet:
                    nb_debug("imported", cls_name)
                    # We need to store the path of the parent module in the class
                    # - this makes it easier to retrieve when we need it for
                    # reading metadata and generating the class docs.
                    mod_class.module_path = str(item)
                    # create a function (pointer) in the class that will
                    # build and return our extended class documentation
                    setattr(
                        mod_class, "_get_doc", partial(get_class_doc, doc_cls=mod_class)
                    )
                    found_classes[cls_name] = mod_class
    return found_classes


def _get_container(custom_cont: str, path_parts: Tuple[str, ...]) -> NBContainer:
    """
    Return container corresponding to path_parts.

    This will search through existing container tree for
    a match for path_parts (optionally prefixed with `custom_cont`).
    If the container (and any required parent containers) does not
    exist it will be created (any required parents to the container
    will also be created).

    Parameters
    ----------
    custom_cont : str
        An optional prefix element for the path to be
        searched
    path_parts : Tuple[str, ...]
        A tuple of path elements for the tree position

    Returns
    -------
    NBContainer
        The container item in the tree. New one created if it
        does not exist.

    """
    cur_container = nblts
    path_elems = list(path_parts)
    if custom_cont:
        path_elems = [custom_cont] + list(path_elems)
    for path_item in path_elems:
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
    full_match : bool
        If True only return full matches, default is True.
        If False it will return partial matches.

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


def _get_pkg_relative_folder(folder: Path):
    """Return relative path based on location of 'msticnb' in the folder path."""
    relative_parts: List[str] = []
    for folder_part in folder.parts:
        if folder_part == "msticnb" or relative_parts:
            relative_parts.append(folder_part)
    return Path(*relative_parts)
