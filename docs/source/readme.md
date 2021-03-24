Creating Notebooklets
=====================

Most of the process of creating a notebook is documented in the
[nb_template](https://github.com/microsoft/msticnb/blob/master/msticnb/nb/template/nb_template.py)
module. You can use this as a starting point for creating a notebooklet.

Notebooklets have two components:

-   A python module containing the code that does all of the processing
    work that you\'d normally write directly into notebook cells.
-   A yaml file that contains configuration, documentation and text
    content that you want to display as part of your notebooklet\'s
    output.

Custom notebooklets must be in a package of their own (although you can
have multiple notebooklets in the same package) so also require an
`__init__.py` in the same folder.

Notebooklets are loaded by calling `nb.discover_modules()` function and
specifying the path to the notebooklets package with the `nb_path`
parameter. (see
:py`discover_modules<msticnb.read_modules.discover_modules>`{.interpreted-text
role="func"})

Notebooklet module
------------------

The notebooklet module has three main sections:

-   **Result class definition**: This defines the attributes and
    descriptions of the data that you want to return from the
    notebooklet.
-   **Notebooklet class definition**: This is the entry point for
    running the notebooklet. At minimum it should be a class derived
    from Notebooklet that implements a [run]{.title-ref} method and
    returns your result class.
-   **Functions**: These do most of the work of the notebooklet and
    usually the code that is copied from or adapted from the original
    notebook.

Having the latter section is optional. You can choose to implement this
functionality in instance methods of the notebooklet class.

However, there are advantages to keeping these as separate functions
outside the class. It means that all the data used in the functions has
to be passed around as parameters and return values. This can improve
the clarity of the code and reduce errors due to some dependency on some
mysterious global state.

If the user of your notebooklet wants to import the module\'s code into
a notebook to read and possibly adapt it, having standalone functions
will make it easier from them understand and work with the code.

### Results Class

This is derived from the
:py`NotebookletResult<msticnb.notebooklet.NotebookletResult>`{.interpreted-text
role="class"} It is also an [attrs class](https://www.attrs.org) so
needs to be decorated with the \@attr decorator.

``` {.python}
@attr.s(auto_attribs=True)
class TemplateResult(NotebookletResult):
    """
    Template Results.

    Attributes
    ----------
    all_events : pd.DataFrame
        DataFrame of all raw events retrieved.
    plot : bokeh.models.LayoutDOM
        Bokeh plot figure showing the account events on an
        interactive timeline.
    additional_info: dict
        Additional information for my notebooklet.

    """

    description: str = "Windows Host Security Events"

    # Add attributes as needed here.
    # Make sure they are documented in the Attributes section
    # above.
    all_events: pd.DataFrame = None
    plot: Figure = None
    additional_info: Optional[dict] = None
```

The class is just a collection of attributes containing results that you
want to return to the user. It is a good idea to add type hints that
define what data type each attribute contains. Adding documentation for
each attribute is important. This not only helps when reading the code
or using the Python help() function but it is also used to automatically
generate titles and descriptive text when you display the results class.

### The Notebooklet class

The notebooklet class is the main engine behind a notebooklet. It is
derived from
:py`Notebooklet<msticnb.notebooklet.Notebooklet>`{.interpreted-text
role="class"}

``` {.python}
class TemplateNB(Notebooklet):
    """
    Template Notebooklet class.

    Detailed description of things this notebooklet does:

    - Fetches all events from XYZ
    - Plots interesting stuff
    - Returns extended metadata about the thing

    Document the options that the Notebooklet takes, if any,
    Use these control which parts of the notebooklet get run.

    """
    # assign metadata from YAML to class variable
    metadata = _CLS_METADATA
    __doc__ = nb_metadata.update_class_doc(__doc__, metadata)
    _cell_docs = _CELL_DOCS
```

The first section of the the class definition contains the docstring.
This documentation is used by the notebooklet browser and the
show_help() function to provide extended user-friendly help.

The first three lines of code handle assiging metadata and documentation
data from the notebooklet yaml file (see below) so that the notebooklet
code can access it.

::: {.warning}
::: {.title}
Warning
:::

Do not change these lines unless you know what you are doing.
:::

#### The run method

:py`Notebooklet.run<msticnb.notebooklet.Notebooklet.run>`{.interpreted-text
role="func"}

The next section is the all-important `run` method. This method is the
main entry point to the notebooklet and controls the flow of most of the
logic. You can add other methods to do subsequent tasks but you should
always implement a run method.

``` {.python}
# @set_text decorator will display the title and text every time
# this method is run.
# The key value refers to an entry in the `output` section of
# the notebooklet yaml file.
@set_text(docs=_CELL_DOCS, key="run")
def run(
    self,
    value: Any = None,
    data: Optional[pd.DataFrame] = None,
    timespan: Optional[TimeSpan] = None,
    options: Optional[Iterable[str]] = None,
    **kwargs,
) -> TemplateResult:
    """
    Return XYZ summary.

    Parameters
    ----------
    value : str
        Host name - The key for searches - e.g. host, account, IPaddress
    data : Optional[pd.DataFrame], optional
        Alternatively use a DataFrame as input.
    timespan : TimeSpan
        Timespan for queries
    options : Optional[Iterable[str]], optional
        List of options to use, by default None.
        A value of None means use default options.
        Options prefixed with "+" will be added to the default options.
        To see the list of available options type `help(cls)` where
        "cls" is the notebooklet class or an instance of this class.

    Returns
    -------
    TemplateResult
        Result object with attributes for each result type.

    Raises
    ------
    MsticnbMissingParameterError
        If required parameters are missing

    """
```

Most of this is class documentation - again this is used in the browser
and user help so you should document this as shown. Usually you can just
copy and paste this example and edit the text to suit your needs - for
example, changing the description `value` if you are expecting an IP
address.

Do not rename or add to these explicit parameters since they are
referenced by the base class. If you want additional parameters you can
supply them as keyword arguments and extract them from kwargs. Be sure
to document any keyword arguments that you require.

#### The set_text decorator

The `@set_text` decorator requires some explanation. This decorator
gives you the ability to output display text every time `run()` is
called. It references the \_CELL_DOCS dictionary, which is read from the
yaml metadata file, and specifies a key which is used to look up the
exact section from the file to use.

You can optionally add explicit title and text as parameters to
`set_text` using the `title`, `text` and `hd_level` parameters. This is
documented here :py`set_text<msticnb.common.set_text>`{.interpreted-text
role="func"}

The set_text decorator does not display any text if you run the
notebooklet with `silent=True` parameter.

#### The run method body

``` {.python}
# This line use logic in the superclass to populate options
# (including default options) into this class.
super().run(
    value=value, data=data, timespan=timespan, options=options, **kwargs
)
```

Calling the base class `run` method from your implementation is
important. This does things like handle options and optionall convert
and normalize the timespan parameter.

The next section validates any input parameters that you require and
creates a results class to store your output data. Assigning the
description and the timespan being used to the results object is very
helpful when you need to refer back to the result or possibly make
additional ad hoc queries afterwards.

``` {.python}
if not value:
    raise MsticnbMissingParameterError("value")
if not timespan:
    raise MsticnbMissingParameterError("timespan.")

# Create a result class
result = TemplateResult()
result.description = self.metadata.description
result.timespan = timespan
```

The remainder of the run method is just about the logic of what you want
to execute and in what order.

::: {.note}
::: {.title}
Note
:::

be sure to assign your results class to `self._last_result`. This will
expose the result class as a `result` property of your notebooklet
instance and allow other methods in your class to reference it.
:::

``` {.python}
# You might want to always do some tasks irrespective of
# options sent
all_events_df = _get_all_events(
    self.query_provider, host_name=value, timespan=timespan
)
result.all_events = all_events_df

if "plot_events" in self.options:
    result.plot = _display_event_timeline(acct_event_data=all_events_df)

if "get_metadata" in self.options:
    result.additional_info = _get_metadata(host_name=value, timespan=timespan)

# Assign the result to the _last_result attribute
# so that you can get to it without having to re-run the operation
self._last_result = result  # pylint: disable=attribute-defined-outside-init

return self._last_result
```

You can call additional methods unconditionally or use the option logic
to allow users to add additional operations or skip ones that they are
not interested in. The available and default options for your
notebooklet are defined in the notebooklet yaml file.

If you call run() without specifying the options parameter, the defaults
will be used. You can specify a custom set of options as a list of
option names (strings).

`options=["opt1", "opt2", "opt4"]`

You can also specify an incremental list. For example:

-   `options=["+option_a"]` will add \"option_a\" to the list of default
    options.
-   `options=["+option_a", "-option_b"]` will add \"option_a\" and
    remove \"option_b\" from the defaults.

::: {.note}
::: {.title}
Note
:::

You cannot mix the explicit options with the incremental options syntax.
:::

Be sure to assign the output from the called functions to the relevant
attributes of your result and return the result at the end.

#### Additional notebooklet methods

Often you will not want to or not be able to execute additional
functionality within the run command. You may require the user to choose
an option before starting a second step or you may want to provide some
kind of data browsing capability that is interactive and needs to the
run method to have completed.

You can do this by adding methods to your notebooklet class. Any public
methods you create will be added to the auto-documentation of the
notebooklet.

This is an example method. Note that if you depend on the result being
populated, you should check this and issue a warning if it is not (as
shown).

``` {.python}
def run_additional_operation(
    self, event_ids: Optional[Union[int, Iterable[int]]] = None
) -> pd.DataFrame:
    """
    Addition method.

    Parameters
    ----------
    event_ids : Optional[Union[int, Iterable[int]]], optional
        Single or interable of event IDs (ints).

    Returns
    -------
    pd.DataFrame
        Results with expanded columns.

    """
    # Include this to check the "run()" has happened before this method
    # can be run
    if (
        not self._last_result or self._last_result.all_events is None
    ):  # type: ignore
        print(
            "Please use 'run()' to fetch the data before using this method.",
            "\nThen call 'expand_events()'",
        )
        return None
    # Print a status message - this will not be displayed if
    # the user has set the global "verbose" option to False.
    nb_print("We maybe about to wait some time")

    nb_markdown("Print some message that always displays", "blue, bold")
    return _do_additional_thing(
        evt_df=self._last_result.all_events,  # type: ignore
        event_ids=event_ids,
    )
    # Note you can also assign new items to the result class in
    # self._last_result and return the updated result class.
```

One thing to note here is the use of
:py`nb_markdown<msticnb.common.nb_markdown>`{.interpreted-text
role="func"} and
:py`nb_print<msticnb.common.nb_print>`{.interpreted-text role="func"}
(there is also an
:py`nb_display<msticnb.common.nb_display>`{.interpreted-text
role="func"} function). These are simple wrappers around
IPython.display.markdown(), Python print() and
IPython.display.display(). These functions honor the `silent` parameter.
This can be supplied to the notebooklet `__init__` method (when creating
an instance of the class) or the `run` method. If silent is True then
these functions do not display any output. You are free to use whatever
output functions you choose but the notebooklet may produce unexpected
output if the user has set the silent option to True.

::: {.note}
::: {.title}
Note
:::

You can access `self.silent` to query the current setting. You can also
set the silent option globally by using `nb.set_opt("silent", True)`
(see :py`set_opt<msticnb.options.set_opt>`{.interpreted-text
role="func"})
:::

### Worker Functions

To keep the notebooklet class simple, most of the work done by the
notebooklet is usually coded in separate module functions. These are
usually declares as private functions by prefixing with \"\_\"

This simple function executes a query and returns the results. The query
provider, hostname and timespan are supplied in the call from the
notebooklet run method.

``` {.python3}
def _get_all_events(qry_prov, host_name, timespan):
    # Tell the user that you're fetching data
    # (doesn't display if nb.set_opt("silent", True))
    nb_data_wait("SecurityEvent")
    return qry_prov.WindowsSecurity.list_host_events(
        timespan,
        host_name=host_name,
        add_query_items="| where EventID != 4688 and EventID != 4624",
    )
```

:py`nb_data_wait<msticnb.common.nb_data_wait>`{.interpreted-text
role="func"} just outputs a standard message telling the user that data
is being retrieved.

This is another example showing the use of the `@set_text` decorator.
The output from this will be displayed as the plot is shown. The plot
layout object is returned to the notebooklet class and added to the
results class (shown earlier).

``` {.python3}
@set_text(docs=_CELL_DOCS, key="display_event_timeline")
def _display_event_timeline(acct_event_data):
    # Plot events on a timeline

    # Note the nbdisplay function is a wrapper around IPython.display()
    # However, it honors the "silent" option (global or per-notebooklet)
    # which allows you to suppress output while running.
    return nbdisplay.display_timeline(
        data=acct_event_data,
        group_by="EventID",
        source_columns=["Activity", "Account"],
        legend="right",
    )
```

Notebook YAML file
------------------

The notebooklet yaml file should have the same name as the Python module
but with a \"yaml\" or \"yml\" extension.

There are two main sections: `metadata` and `output`.

``` {.YAML}
metadata:
    name: TemplateNB
    description: Template YAML for Notebooklet
    default_options:
        - all_events: Gets all events about blah
        - plot_events:
            Display and summary and timeline of events.
    other_options:
        - get_metadata: fetches additional metadata about the entity
    keywords:
        - host
        - computer
        - heartbeat
        - windows
        - account
    entity_types:
        - host
    req_providers:
        - AzureSentinel|LocalData
        - tilookup
```

The metadata section defines runtime parameters for the notebooklet.
These include:

-   the notebooklet display name
-   the notebooklet description
-   the default options (a list of key/value pairs of option name and
    description)
-   other options available
-   keywords (used in searching for the notebooklet
-   entity types - mainly informational so that a user can find all
    notebooklets that deal with hosts, IP addresses, etc.
-   req_providers - this is a list of data providers required for the
    notebooklet to run. You can provide alternates (as shown), which
    means that if one of the providers is available the notebooklet will
    load successfully.

``` {.YAML}
output:
    run:
        title: Title for the run method (main title)
        hd_level: 1
        text:
        Write your introductory text here

        Data and plots are stored in the result class returned by this function.

        If you use **markdown** syntax in this block add the following
        to use markdown processing.
        md: True
    display_event_timeline:
        title: Display the timeline.
        text: '
        This may take some time to complete for large numbers of events.

        It will do:
        - Item one
        - Item two

        Since some groups will be undefined these can show up as `NaN`.

        Note: use a quoted string if you want to include yaml reserved chars
        such as ":"
        '
        md: True
```

The output section defines the display text for the `@set_text`
decorator function used in the notebooklet module. The key for each
section under output must match the value for the `key` parameter in the
call to `set_text`.

Each section has the following sub-keys:

-   title: the title to display (by default as HTML h2 or Markdown
    \"\#\#\")
-   hd_level: (1-4) to override the default heading level
-   text: the body text to display. This will display as plain text by
    default
-   md: set to True to process the \"text\" value as Markdown.
