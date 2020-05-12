
# Notebooklets

Notebooklets are reusable Jupyter notebook code patterns for InfoSec investigators
and hunters.

## Notebook Authoring issues

Notebook authors face several issues:

- Code in one notebook cannot easily be reused in other notebooks
- Code cannot easily be unit tested
- Updating notebooks that have already been distributed to users is hard.

## Notebooklets Goals

The goals for MSTIC notebooklets are:

- Enable re-use of common notebook patterns
- Allow unit testing of code blocks
- Speed up authoring of new notebooks
- Allow update of notebooklets code for fixes and enhancement
- Support multiple data platforms

# Installing

```bash
pip install msticnb
```

# Usage

### Import and initialize the notebooklets

```python
import msticnb as nb
nb.init()

```

### Run a Notebooklet

```python
from msticnb.common import TimeSpan
tm_span = TimeSpan(period="7d")  # end defaults to utcnow()
host_summary = nb.nblts.azsent.host.HostSummary()
host_summary_rslt = host_summary.run(value="myhost", timespan=tm_span)
```

### Get Help

```python
nb.nblts.azsent.host.HostSummary.show_help()
```

and of course, standard Python help also works as expected
```python
help(host_summary)
help(host_summary.run)
```

# Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
