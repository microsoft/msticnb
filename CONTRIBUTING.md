
Contributions of improvements, fixes and new features are welcomed.
We use a continuous integration pipeline that enforces unit tests and code style. We aim to keep
the code clear, testable and well-documented.

## Contributing
(Legal stuff)

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit <https://cla.microsoft.com>.

When you submit a pull request, a CLA-bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.


# Guidelines for code:

## Unit Tests
All new code should have unit tests with at least 80% code coverage. There are some exceptions to this: for example, code that accesses online data and requires authentication. We can work with you on getting this to work in our build.
We use pytest but most of the existing tests are also Python unittest compatible.

## Type hints
Use type annotations for parameters and return values in public methods, properties and functions.
[Python Type Hints documentation](https://docs.python.org/3/library/typing.html)

## Docstrings
Our documentation is automatically built for Readthedocs using Sphinx.
All public modules, functions, classes and methods should be documented using the numpy documenation standard.
[numpy docstring guide](https://numpydoc.readthedocs.io/en/latest/format.html)

## Code Formatting
We use black everywhere and enforce this in the build.
[Black - The Uncompromising Code Formatter](https://github.com/psf/black)

## Linters/Code Checkers
We use the following code checkers:
- pylint (with --disable=bad-continuation)
- mypy
- bandit (with -s B303,B404,B603,B607)
- flake8 (with --ignore=E501,W503)
- prospector (see prospector.yml in root of repo for config used). Prospector runs:
  - pycodestyle
  - pydocstyle
  - pep8
  - pyroma
  - pep257
 
