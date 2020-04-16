Host Logons Notebooklet
=======================

Description
-----------

This Notebooklet provides an overivew of logon events to a Windows or Linux Host in a certain timeframe.
You can provide the Notebooklet with either a hostname and time range to query data for, or you can 
provide a [Pandas DataFrame](https://pandas.pydata.org/) of pre-collected logon events. The Notebooklet will then return a set of 
summaries and visualizations of the logon in the data.

Avaliable Options
-----------------
This Notebooklet has three avaliable options that can be set:
    * map - this produces and returns a [Folium Map](https://github.com/python-visualization/folium) plot of all remote logon attempt locations, with sucessful 
        logons marked in green and failed logons in red.
    * timeline - this produces a timeline showing all failed and logon events in a chronological order.
    * charts - this returns various charts visizualizing key data points.
By default all these options are set, however if you have a large dataset it is reccomended that the map and 
timeline options are not set for performance reasons.

Output
------
* logon_sessions - this is a DataFrame of all failed and successful logons attempts observed.
* logon_matrix - this is a DataFrame showing a breakdown a logon attempts by user and process.
* [logon_map](https://msticpy.readthedocs.io/en/latest/visualization/FoliumMap.html) - this is a geographical map plotting the IP address location of remote logon attempts.
* [timeline](https://msticpy.readthedocs.io/en/latest/visualization/EventTimeline.html) - this is a Bokeh plot showing logon events in a chronological timeline.
* plots - this is a dictionary of various visualizations of the data. These include:
    * User Pie Chart: A chart showing the breakdown of user accounts observed.
    * Process Bar Chart: A chart showing the propotion of failed and successful logon attempts by process.

Plots
~~~~~
The Notebooklet returns a number of [Bokeh](https://bokeh.org/) based visualizations of the data. In order display these you
will need to use the Bokeh show() function.

.. code:: ipython3
    from bokeh.io import show
    show(plot)
