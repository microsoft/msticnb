# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Setup script for msticnb."""

import re
import setuptools


INSTALL_REQUIRES = [
    "attrs>=18.2.0",
    "deprecated>=1.2.4",
    "ipython>=7.2.0",
    "ipywidgets>=7.4.2",
    "msticpy>=0.4.0",
    "numpy>=1.15.4",
    "pandas>=0.25.0",
    "pyyaml>=3.13",
    "requests>=2.21.1",
    "setuptools>=40.6.3",
    "typing>=3.6.6",
]


# pylint: disable=locally-disabled, invalid-name
with open("README.md", "r") as fh:
    long_description = fh.read()

with open("msticnb/_version.py", "r") as fd:
    v_match = re.search(r'^VERSION\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE)
    __version__ = v_match.group(1) if v_match else "no version"
# pylint: enable=locally-disabled, invalid-name

setuptools.setup(
    name="msticnb",
    version=__version__,
    author="Ian Hellen",
    author_email="ianhelle@microsoft.com",
    description="MSTIC Notebooklets",
    license="MIT License",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/microsoft/msticnb",
    project_urls={
        "Documentation": "https://msticpy.readthedocs.io",
        "Code": "https://github.com/microsoft/msticnb",
    },
    python_requires=">=3.6",
    packages=setuptools.find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
    ],
    install_requires=INSTALL_REQUIRES,
    keywords=[
        "security",
        "cybersecurity",
        "infosec",
        "jupyter",
        "notebook",
        "azure",
        "sentinel",
    ],
    zip_safe=False,
    include_package_data=True,
)
