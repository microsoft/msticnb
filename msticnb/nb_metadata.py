# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Notebooklet base classes."""
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import attr
import yaml
from attr import Factory

from ._version import VERSION

__version__ = VERSION
__author__ = "Ian Hellen"


@attr.s(auto_attribs=True)
class NBMetadata:
    """Notebooklet metadata class."""

    name: str = "Unnamed"
    mod_name: str = ""
    description: str = ""
    default_options: List[Union[str, Dict]] = Factory(list)
    other_options: List[Union[str, Dict]] = Factory(list)
    inputs: List[str] = ["value"]
    entity_types: List[str] = Factory(list)
    keywords: List[str] = Factory(list)
    req_providers: List[str] = Factory(list)

    # pylint: disable=not-an-iterable
    @property
    def search_terms(self) -> Set[str]:
        """Return set of search terms for the object."""
        return set(
            [self.name]
            + [obj.casefold() for obj in self.entity_types]  # type: ignore
            + [key.casefold() for key in self.keywords]  # type: ignore
            + [opt.casefold() for opt in self.all_options]  # type: ignore
        )

    def __str__(self):
        """Return string representation of object."""
        return "\n".join(f"{name}: {val}" for name, val in attr.asdict(self).items())

    @property
    def all_options(self) -> List[str]:
        """Return combination of default and other options."""
        opts = []
        if self.default_options:
            for opt in self.default_options:
                if isinstance(opt, str):
                    opts.append(opt)
                elif isinstance(opt, dict):
                    opts.append(next(iter(opt.keys())))
        if self.other_options:
            for opt in self.other_options:
                if isinstance(opt, str):
                    opts.append(opt)
                elif isinstance(opt, dict):
                    opts.append(next(iter(opt.keys())))
        return sorted(opts)

    def get_options(self, option_set: str = "all") -> List[Tuple[str, Optional[str]]]:
        """
        Return list of options and descriptions.

        Parameters
        ----------
        option_set : str, optional
            The subset of options to return, by default "all"
            Other values are "default" and "other"

        Returns
        -------
        List[Tuple[str, Optional[str]]]
            A list of tuples of option name and description.

        """
        opt_list: List[Tuple[str, Optional[str]]] = []
        if option_set.casefold() in ["all", "default"] and self.default_options:
            for opt in self.default_options:
                if isinstance(opt, str):
                    opt_list.append((opt, None))
                elif isinstance(opt, dict):
                    opt_list.extend(opt.items())
        if option_set.casefold() in ["all", "other"] and self.other_options:
            for opt in self.other_options:
                if isinstance(opt, str):
                    opt_list.append((opt, None))
                elif isinstance(opt, dict):
                    opt_list.extend(opt.items())
        return opt_list

    @property
    def options_doc(self) -> str:
        """Return list of options and documentation."""
        def_options = self.get_options("default")

        opt_list = [
            "",
            "    Default Options",
            "    ---------------",
        ]
        if def_options:
            opt_list.extend([f"    - {key}: {value}" for key, value in def_options])
        else:
            opt_list.append("    None")
        opt_list.extend(
            [
                "",
                "    Other Options",
                "    -------------",
            ]
        )

        if self.get_options("other"):
            opt_list.extend(
                [f"    - {key}: {value}" for key, value in self.get_options("other")]
            )
        else:
            opt_list.append("    None")
        # Add a blank line to the end
        opt_list.extend(["", ""])
        return "\n".join(opt_list)

    # pylint: enable=not-an-iterable


def read_mod_metadata(mod_path: str, module_name) -> Tuple[NBMetadata, Dict[str, Any]]:
    """
    Read notebooklet metadata from yaml file.

    Parameters
    ----------
    mod_path : str
        The fully-qualified (dotted) module name
    module_name : str
        The full module name.

    Returns
    -------
    Tuple[NBMetadata, Dict[str, Any]]
        A tuple of the metadata class
        and the documentation dictionary

    """
    md_dict = _read_metadata_file(mod_path)
    if not md_dict:
        return NBMetadata(), {}
    metadata_vals = md_dict.get("metadata", {})

    metadata_vals["mod_name"] = module_name
    metadata = NBMetadata(**metadata_vals)
    output = md_dict.get("output", {})
    return metadata, output


def _read_metadata_file(mod_path):
    md_path = Path(str(mod_path).replace(".py", ".yaml"))
    if not md_path.is_file():
        md_path = Path(str(mod_path).replace(".py", ".yml"))
    if md_path.is_file():
        with open(md_path, "r", encoding="utf-8") as _md_file:
            return yaml.safe_load(_md_file)
    return None


def update_class_doc(cls_doc: str, cls_metadata: NBMetadata):
    """Append the options documentation to the `cls_doc`."""
    options_doc = cls_metadata.options_doc
    if options_doc is not None:
        return cls_doc + options_doc
    return cls_doc
