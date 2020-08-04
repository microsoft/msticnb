Jupyter Notebooklets Demo
=========================

[@ianhellen](https://twitter.com/ianhellen)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Principal Dev - MSTIC, Azure Security
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

What are notebooklets?
======================

Collections of notebook cells that implement some useful reusable
sequence

Rationale
---------

-  Notebook code can quickly become complex and length:

   -  Can obscure the information you are trying to display
   -  Can be intimidating to non-developers

-  Notebook code cells are not easily re-useable:

   -  You can copy and paste but how do you sync changes back to
      original notebook?
   -  Difficult to discover code snippets in notebooks

-  Notebook code is often fragile:

   -  Often not parameterized
   -  Code blocks are frequently dependent on global values assigned
      earlier
   -  Output data is not in any standard format
   -  Difficult to test

Characteristics of Notebooklets
-------------------------------

-  One or small number of entry points
-  Must be paramertizable (e.g. you can supply hostname, IP Address,
   time range, etc.)
-  Can query, process or visualize data (or any combination)
-  Typically return a result or package of results for use later in the
   notebook

--------------

Initializing the Notebook
=========================

Notebooklets depend on msticpy so we import/initialize this package.

.. code:: ipython3

    import sys
    import os
    from IPython.display import display, HTML, Markdown

    from msticpy.nbtools.nbinit import init_notebook
    init_notebook(namespace=globals());


.. parsed-literal::

    Processing imports....
    Checking configuration....
    Setting options....



.. raw:: html

    <h3>Notebook setup complete</h3>


--------------

Notebooklets in use
===================

Import the package
------------------

-  Discovers and imports notebooklet classes/modules

.. code:: ipython3

    # pip install git+https://github.com/microsoft/msticnb

.. code:: ipython3

    import msticnb as nb


.. parsed-literal::

    3 notebooklets loaded.


--------------

Calling init()
--------------

Before using any of the notebooklets you need to initialize the
providers.

Providers are the libraries that do the work of fetching data from
external sources that are then used by the notebooklet code.

init() does the following: - Loads required data providers -
Authenticates to providers if required at startup - Can supply list of
providers to load - Can pass parameters to each provider (settings
loaded from config by default)

.. code:: ipython3

    nb.init?



.. parsed-literal::

    [1;31mSignature:[0m
    [0mnb[0m[1;33m.[0m[0minit[0m[1;33m([0m[1;33m
    [0m    [0mquery_provider[0m[1;33m:[0m[0mstr[0m[1;33m=[0m[1;34m'LogAnalytics'[0m[1;33m,[0m[1;33m
    [0m    [0mproviders[0m[1;33m:[0m[0mUnion[0m[1;33m[[0m[0mList[0m[1;33m[[0m[0mstr[0m[1;33m][0m[1;33m,[0m [0mNoneType[0m[1;33m][0m[1;33m=[0m[1;32mNone[0m[1;33m,[0m[1;33m
    [0m    [1;33m**[0m[0mkwargs[0m[1;33m,[0m[1;33m
    [0m[1;33m)[0m[1;33m[0m[1;33m[0m[0m
    [1;31mDocstring:[0m
    Instantiate an instance of DataProviders.

    Parameters
    ----------
    query_provider : str, optional
        DataEnvironment name of the primary query provider.
        You can add addtional query providers by including them
        in the `providers` list.
    providers : Optional[List[str]], optional
        A list of provider names, by default "LogAnalytics"

    Other Parameters
    ----------------
    kwargs
        You can pass parameters to individual providers using
        the following notation:
        `ProviderName_param_name="param_value"
        Where `ProviderName` is the name of the data provider,
        `param_name` is the parameter name expected by the
        provider and `param_value` is the value to assign to
        `param_name`. `param_value` can be any type.

        Depending on the provider, these parameters (with the
        prefix stripped) are sent to either the constructor or
        `connect` method.

    Notes
    -----
    To see a list of currently supported providers call:
    `DataProviders.list_providers()`
    [1;31mFile:[0m      e:\src\msticnb\msticnb\data_providers.py
    [1;31mType:[0m      function



Available Providers
~~~~~~~~~~~~~~~~~~~

.. code:: ipython3

    nb.DataProviders.list_providers()




.. parsed-literal::

    ['LogAnalytics',
     'AzureSentinel',
     'Kusto',
     'AzureSecurityCenter',
     'SecurityGraph',
     'MDATP',
     'LocalData',
     'azuredata',
     'tilookup',
     'geolitelookup',
     'ipstacklookup']



Default Providers
~~~~~~~~~~~~~~~~~

.. code:: ipython3

    nb.DataProviders.get_def_providers()




.. parsed-literal::

    ['azuredata', 'tilookup', 'geolitelookup']



Running init, adding ipstacklookup to the default set of providers.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also prefix a provider name with “-” to remove it from the
default set.

You can also specify an explicit list of providers to override the
defaults entirely. E.g

::

   nb.init(query_provider="AzureSentinel", providers=["ipstacklookup", "tilookup"])

..

   **Note** you cannot mix the “+”/“-” with un-prefixed provider names.
   Doing this will cause an error to be thrown. e.g.
   ``nb.init(query_provider="AzureSentinel", providers=["+ipstacklookup", "tilookup"])``
   is illegal.

.. code:: ipython3

    nb.init(query_provider="AzureSentinel", providers=["-tilookup", "+ipstacklookup"])


.. parsed-literal::

    Please wait. Loading Kqlmagic extension...



.. parsed-literal::

    <IPython.core.display.Javascript object>



.. parsed-literal::

    <IPython.core.display.Javascript object>



.. parsed-literal::

    <IPython.core.display.Javascript object>



.. raw:: html

    <!DOCTYPE html>
                        <html><body>

                        <!-- h1 id="user_code_p"><b>ESH5TCBVW</b><br></h1-->

                        <input  id="kql_MagicCodeAuthInput" type="text" readonly style="font-weight: bold; border: none;" size = '9' value='ESH5TCBVW'>

                        <button id='kql_MagicCodeAuth_button', onclick="this.style.visibility='hidden';kql_MagicCodeAuthFunction()">Copy code to clipboard and authenticate</button>

                        <script>
                        var kql_MagicUserCodeAuthWindow = null
                        function kql_MagicCodeAuthFunction() {
                            /* Get the text field */
                            var copyText = document.getElementById("kql_MagicCodeAuthInput");

                            /* Select the text field */
                            copyText.select();

                            /* Copy the text inside the text field */
                            document.execCommand("copy");

                            /* Alert the copied text */
                            // alert("Copied the text: " + copyText.value);

                            var w = screen.width / 2;
                            var h = screen.height / 2;
                            params = 'width='+w+',height='+h
                            kql_MagicUserCodeAuthWindow = window.open('https://microsoft.com/devicelogin', 'kql_MagicUserCodeAuthWindow', params);

                            // TODO: save selected cell index, so that the clear will be done on the lince cell
                        }
                        </script>

                        </body></html>



.. raw:: html

    <!DOCTYPE html>
                        <html><body><script>

                            // close authentication window
                            if (kql_MagicUserCodeAuthWindow && kql_MagicUserCodeAuthWindow.opener != null && !kql_MagicUserCodeAuthWindow.closed) {
                                kql_MagicUserCodeAuthWindow.close()
                            }
                            // TODO: make sure, you clear the right cell. BTW, not sure it is a must to do any clearing

                            // clear output cell
                            Jupyter.notebook.clear_output(Jupyter.notebook.get_selected_index())

                            // TODO: if in run all mode, move to last cell, otherwise move to next cell
                            // move to next cell

                        </script></body></html>



.. raw:: html

    <!DOCTYPE html>
                <html><body>
                <div style=''>


                <button onclick="this.style.visibility='visible';kql_MagicLaunchWindowFunction('Kqlmagic_temp_files/_52b1ab41-869e-4138-9e40-2a4457f09bf0_at_loganalytics_schema.html','fullscreen=no,directories=no,location=no,menubar=no,resizable=yes,scrollbars=yes,status=no,titlebar=no,toolbar=no,','_52b1ab41_869e_4138_9e40_2a4457f09bf0_at_loganalytics_schema','')">popup schema 52b1ab41-869e-4138-9e40-2a4457f09bf0@loganalytics</button>

                </div>

                <script>

                function kql_MagicLaunchWindowFunction(file_path, window_params, window_name, notebooks_host) {
                    var url;
                    if (notebooks_host == 'text') {
                        url = ''
                    } else if (file_path.startsWith('http')) {
                        url = file_path;
                    } else {
                        var base_url = '';

                        // check if azure notebook
                        var azure_host = (notebooks_host == null || notebooks_host.length == 0) ? 'https://notebooks.azure.com' : notebooks_host;
                        var start = azure_host.search('//');
                        var azure_host_suffix = '.' + azure_host.substring(start+2);

                        var loc = String(window.location);
                        var end = loc.search(azure_host_suffix);
                        start = loc.search('//');
                        if (start > 0 && end > 0) {
                            var parts = loc.substring(start+2, end).split('-');
                            if (parts.length == 2) {
                                var library = parts[0];
                                var user = parts[1];
                                base_url = azure_host + '/api/user/' +user+ '/library/' +library+ '/html/';
                            }
                        }

                        // check if local jupyter lab
                        if (base_url.length == 0) {
                            var configDataScipt  = document.getElementById('jupyter-config-data');
                            if (configDataScipt != null) {
                                var jupyterConfigData = JSON.parse(configDataScipt.textContent);
                                if (jupyterConfigData['appName'] == 'JupyterLab' && jupyterConfigData['serverRoot'] != null &&  jupyterConfigData['treeUrl'] != null) {
                                    var basePath = 'e:/src/notebooks/tests' + '/';
                                    if (basePath.startsWith(jupyterConfigData['serverRoot'])) {
                                        base_url = '/files/' + basePath.substring(jupyterConfigData['serverRoot'].length+1);
                                    }
                                }
                            }
                        }

                        // assume local jupyter notebook
                        if (base_url.length == 0) {

                            var parts = loc.split('/');
                            parts.pop();
                            base_url = parts.join('/') + '/';
                        }
                        url = base_url + file_path;
                    }

                    window.focus();
                    var w = screen.width / 2;
                    var h = screen.height / 2;
                    params = 'width='+w+',height='+h;
                    kql_Magic__52b1ab41_869e_4138_9e40_2a4457f09bf0_at_loganalytics_schema = window.open(url, window_name, window_params + params);
                    if (url == '') {
                        var el = kql_Magic__52b1ab41_869e_4138_9e40_2a4457f09bf0_at_loganalytics_schema.document.createElement('p');
                        kql_Magic__52b1ab41_869e_4138_9e40_2a4457f09bf0_at_loganalytics_schema.document.body.overflow = 'auto';
                        el.style.top = 0;
                        el.style.left = 0;
                        el.innerHTML = file_path;
                        kql_Magic__52b1ab41_869e_4138_9e40_2a4457f09bf0_at_loganalytics_schema.document.body.appendChild(el);
                    }
                }
                </script>

                </body></html>


.. parsed-literal::

    Warning: ('No AzureCLI configuration found in configuration settings.',)



.. raw:: html


    This product includes GeoLite2 data created by MaxMind, available from
    <a href="https://www.maxmind.com">https://www.maxmind.com</a>.




.. raw:: html


    This library uses services provided by ipstack.
    <a href="https://ipstack.com">https://ipstack.com</a>


.. parsed-literal::

    Loaded providers: LogAnalytics, geolitelookup, ipstacklookup


--------------

Using LocalData Provider
------------------------

The LocalData provider allows you to substitue local files for queries
that you normally make to online data sources such as AzureSentinel.

When we call init() we use the “LocalData\_” prefix to pass the
“query_paths” and “data_paths” parameters to the underlying provider.

-  Specify a folder where data files are stored with
   ``LocalData_data_paths`` (list[str])
-  Specify a folder containing query definition files
   ``LocalData_query_paths`` (list[str])

In notebooklets queries are available as self.query_provider

.. code:: ipython3

    nb.init(
        "LocalData", providers=["-tilookup"],
        LocalData_data_paths=["e:\\src\\msticnb\\msticnb\\tests\\testdata"],
        LocalData_query_paths=["e:\\src\\msticnb\\msticnb\\tests\\testdata"],
    )


.. parsed-literal::

    Warning: ('No AzureCLI configuration found in configuration settings.',)
    Loaded providers: LocalData, geolitelookup


.. parsed-literal::

    e:\src\microsoft\msticpy\msticpy\data\query_store.py:172: UserWarning:

    e:\src\msticnb\msticnb\tests\testdata\msticpyconfig-test.yaml is not a valid query definition file.



.. code:: ipython3

    html_w = widgets.HTML
    qry_prov = nb.data_providers["LocalData"]

    qry_prov.WindowsSecurity.list_host_events().head()




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }

        .dataframe tbody tr th {
            vertical-align: top;
        }

        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>TenantId</th>
          <th>TimeGenerated</th>
          <th>SourceSystem</th>
          <th>Account</th>
          <th>AccountType</th>
          <th>Computer</th>
          <th>EventSourceName</th>
          <th>Channel</th>
          <th>Task</th>
          <th>Level</th>
          <th>EventData</th>
          <th>EventID</th>
          <th>Activity</th>
          <th>PartitionKey</th>
          <th>RowKey</th>
          <th>StorageAccount</th>
          <th>AzureDeploymentID</th>
          <th>AzureTableName</th>
          <th>AccessList</th>
          <th>AccessMask</th>
          <th>AccessReason</th>
          <th>AccountDomain</th>
          <th>AccountExpires</th>
          <th>AccountName</th>
          <th>AccountSessionIdentifier</th>
          <th>...</th>
          <th>TargetUserSid</th>
          <th>TemplateContent</th>
          <th>TemplateDSObjectFQDN</th>
          <th>TemplateInternalName</th>
          <th>TemplateOID</th>
          <th>TemplateSchemaVersion</th>
          <th>TemplateVersion</th>
          <th>TokenElevationType</th>
          <th>TransmittedServices</th>
          <th>UserAccountControl</th>
          <th>UserParameters</th>
          <th>UserPrincipalName</th>
          <th>UserWorkstations</th>
          <th>VirtualAccount</th>
          <th>VendorIds</th>
          <th>Workstation</th>
          <th>WorkstationName</th>
          <th>SourceComputerId</th>
          <th>EventOriginId</th>
          <th>MG</th>
          <th>TimeCollected</th>
          <th>ManagementGroupName</th>
          <th>Type</th>
          <th>_ResourceId</th>
          <th>EventProperties</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-11 08:40:22.537</td>
          <td>OpsManager</td>
          <td>WORKGROUP\MSTICAlertsWin1$</td>
          <td>Machine</td>
          <td>MSTICAlertsWin1</td>
          <td>Microsoft-Windows-Security-Auditing</td>
          <td>Security</td>
          <td>13826</td>
          <td>8</td>
          <td>&lt;EventData xmlns="http://schemas.microsoft.com/win/2004/08/events/event"&gt;\r\n  &lt;Data Name="Targe...</td>
          <td>4799</td>
          <td>4799 - A security-enabled local group membership was enumerated</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>...</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>263a788b-6526-4cdc-8ed9-d79402fe4aa0</td>
          <td>d0ec0118-9b6b-477e-ba9f-e4ead3665884</td>
          <td>00000000-0000-0000-0000-000000000001</td>
          <td>2019-02-11 08:40:40.387</td>
          <td>AOI-52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>SecurityEvent</td>
          <td>/subscriptions/40dcc8bf-0478-4f3b-b275-ed0a94f2c013/resourcegroups/asihuntomsworkspacerg/provide...</td>
          <td>{'TargetUserName': 'Remote Desktop Users', 'TargetDomainName': 'Builtin', 'TargetSid': 'S-1-5-32...</td>
        </tr>
        <tr>
          <th>1</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-11 08:40:24.827</td>
          <td>OpsManager</td>
          <td>WORKGROUP\MSTICAlertsWin1$</td>
          <td>Machine</td>
          <td>MSTICAlertsWin1</td>
          <td>Microsoft-Windows-Security-Auditing</td>
          <td>Security</td>
          <td>13826</td>
          <td>8</td>
          <td>&lt;EventData xmlns="http://schemas.microsoft.com/win/2004/08/events/event"&gt;\r\n  &lt;Data Name="Targe...</td>
          <td>4799</td>
          <td>4799 - A security-enabled local group membership was enumerated</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>...</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>263a788b-6526-4cdc-8ed9-d79402fe4aa0</td>
          <td>5365f041-1345-4cd0-8fbb-41ccbaa16a39</td>
          <td>00000000-0000-0000-0000-000000000001</td>
          <td>2019-02-11 08:40:40.387</td>
          <td>AOI-52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>SecurityEvent</td>
          <td>/subscriptions/40dcc8bf-0478-4f3b-b275-ed0a94f2c013/resourcegroups/asihuntomsworkspacerg/provide...</td>
          <td>{'TargetUserName': 'Administrators', 'TargetDomainName': 'Builtin', 'TargetSid': 'S-1-5-32-544',...</td>
        </tr>
        <tr>
          <th>2</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-11 08:40:24.827</td>
          <td>OpsManager</td>
          <td>WORKGROUP\MSTICAlertsWin1$</td>
          <td>Machine</td>
          <td>MSTICAlertsWin1</td>
          <td>Microsoft-Windows-Security-Auditing</td>
          <td>Security</td>
          <td>13824</td>
          <td>8</td>
          <td>&lt;EventData xmlns="http://schemas.microsoft.com/win/2004/08/events/event"&gt;\r\n  &lt;Data Name="Targe...</td>
          <td>4798</td>
          <td>4798 - A user's local group membership was enumerated.</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>...</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>263a788b-6526-4cdc-8ed9-d79402fe4aa0</td>
          <td>5333954d-9157-443c-9657-6ef390c73abb</td>
          <td>00000000-0000-0000-0000-000000000001</td>
          <td>2019-02-11 08:40:40.387</td>
          <td>AOI-52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>SecurityEvent</td>
          <td>/subscriptions/40dcc8bf-0478-4f3b-b275-ed0a94f2c013/resourcegroups/asihuntomsworkspacerg/provide...</td>
          <td>{'TargetUserName': 'MSTICAdmin', 'TargetDomainName': 'MSTICAlertsWin1', 'TargetSid': 'S-1-5-21-9...</td>
        </tr>
        <tr>
          <th>3</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-11 08:40:24.833</td>
          <td>OpsManager</td>
          <td>WORKGROUP\MSTICAlertsWin1$</td>
          <td>Machine</td>
          <td>MSTICAlertsWin1</td>
          <td>Microsoft-Windows-Security-Auditing</td>
          <td>Security</td>
          <td>13824</td>
          <td>8</td>
          <td>&lt;EventData xmlns="http://schemas.microsoft.com/win/2004/08/events/event"&gt;\r\n  &lt;Data Name="Targe...</td>
          <td>4798</td>
          <td>4798 - A user's local group membership was enumerated.</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>...</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>263a788b-6526-4cdc-8ed9-d79402fe4aa0</td>
          <td>d2fded8a-e507-4017-aedd-cb6da6a2b624</td>
          <td>00000000-0000-0000-0000-000000000001</td>
          <td>2019-02-11 08:40:40.387</td>
          <td>AOI-52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>SecurityEvent</td>
          <td>/subscriptions/40dcc8bf-0478-4f3b-b275-ed0a94f2c013/resourcegroups/asihuntomsworkspacerg/provide...</td>
          <td>{'TargetUserName': 'DefaultAccount', 'TargetDomainName': 'MSTICAlertsWin1', 'TargetSid': 'S-1-5-...</td>
        </tr>
        <tr>
          <th>4</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-11 08:40:24.833</td>
          <td>OpsManager</td>
          <td>WORKGROUP\MSTICAlertsWin1$</td>
          <td>Machine</td>
          <td>MSTICAlertsWin1</td>
          <td>Microsoft-Windows-Security-Auditing</td>
          <td>Security</td>
          <td>13824</td>
          <td>8</td>
          <td>&lt;EventData xmlns="http://schemas.microsoft.com/win/2004/08/events/event"&gt;\r\n  &lt;Data Name="Targe...</td>
          <td>4798</td>
          <td>4798 - A user's local group membership was enumerated.</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>...</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>263a788b-6526-4cdc-8ed9-d79402fe4aa0</td>
          <td>701504d1-e106-48ca-b424-d9ec20f17746</td>
          <td>00000000-0000-0000-0000-000000000001</td>
          <td>2019-02-11 08:40:40.387</td>
          <td>AOI-52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>SecurityEvent</td>
          <td>/subscriptions/40dcc8bf-0478-4f3b-b275-ed0a94f2c013/resourcegroups/asihuntomsworkspacerg/provide...</td>
          <td>{'TargetUserName': 'Guest', 'TargetDomainName': 'MSTICAlertsWin1', 'TargetSid': 'S-1-5-21-996632...</td>
        </tr>
      </tbody>
    </table>
    <p>5 rows × 226 columns</p>
    </div>



--------------

Notebooklet classes are discovered and imported at load time
------------------------------------------------------------

Although you can manually initiate a a run to read more notebooklets.

The ``nblts`` attribute exposes notebooklets (niblets?) in a tree structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  Useful for autocomplete when you more or less know what you’re
   looking for

The top level in the hierarchy is the data environment (e.g. azsent ==
AzureSentinel). Beneath these the notebooklets are grouped into various
categories such as host, network, etc.

.. code:: ipython3

    print(nb.nblts)


.. parsed-literal::

    azsent
      host
        HostSummary (Notebooklet)
        WinHostEvents (Notebooklet)
      network
        NetworkFlowSummary (Notebooklet)



Access an individual notebook using this path structure

.. code:: ipython3

    nb.nblts.azsent.host.HostSummary?



.. parsed-literal::

    [1;31mInit signature:[0m
    [0mnb[0m[1;33m.[0m[0mnblts[0m[1;33m.[0m[0mazsent[0m[1;33m.[0m[0mhost[0m[1;33m.[0m[0mHostSummary[0m[1;33m([0m[1;33m
    [0m    [0mdata_providers[0m[1;33m:[0m[0mUnion[0m[1;33m[[0m[1;33m<[0m[0mmsticnb[0m[1;33m.[0m[0mdata_providers[0m[1;33m.[0m[0mSingletonDecorator[0m [0mobject[0m [0mat[0m [1;36m0x000002535346E630[0m[1;33m>[0m[1;33m,[0m [0mNoneType[0m[1;33m][0m[1;33m=[0m[1;32mNone[0m[1;33m,[0m[1;33m
    [0m    [1;33m**[0m[0mkwargs[0m[1;33m,[0m[1;33m
    [0m[1;33m)[0m[1;33m[0m[1;33m[0m[0m
    [1;31mDocstring:[0m
    HostSummary Notebooklet class.

    Queries and displays information about a host including:

    - IP address assignment
    - Related alerts
    - Related hunting/investigation bookmarks
    - Azure subscription/resource data.


    Default Options
    ---------------
    heartbeat: Query Heartbeat table for host information.
    azure_net: Query AzureNetworkAnalytics table for host network topology information.
    alerts: Query any alerts for the host.
    bookmarks: Query any bookmarks for the host.
    azure_api: Query Azure API for VM information.

    Other Options
    -------------
    None
    [1;31mInit docstring:[0m
    Intialize a new instance of the notebooklet class.

    Parameters
    ----------
    data_providers : DataProviders, Optional
        Optional DataProviders instance to query data.
        Most classes require this.

    Raises
    ------
    MsticnbDataProviderError
        If DataProviders has not been initialized.
        If required providers are specified by the notebooklet
        but are not available.
    [1;31mFile:[0m           e:\src\msticnb\msticnb\nb\azsent\host\host_summary.py
    [1;31mType:[0m           ABCMeta
    [1;31mSubclasses:[0m



Notebooklets are exposed in ``nb.nb_index``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The values reflect the physical path in which the notebooklets are
stored (you can ignore this)

.. code:: ipython3

    nb.nb_index




.. parsed-literal::

    {'nblts.azsent.host.HostSummary': msticnb.nb.azsent.host.host_summary.HostSummary,
     'nblts.azsent.host.WinHostEvents': msticnb.nb.azsent.host.win_host_events.WinHostEvents,
     'nblts.azsent.network.NetworkFlowSummary': msticnb.nb.azsent.network.network_flow_summary.NetworkFlowSummary}



There is a find function that looks for:
----------------------------------------

-  text or regulate expressions
-  searches class docstring
-  metadata such as entities supported and options supported

.. code:: ipython3

    nb.find("host, net.*", full_match=True)




.. parsed-literal::

    [('HostSummary', msticnb.nb.azsent.host.host_summary.HostSummary),
     ('NetworkFlowSummary',
      msticnb.nb.azsent.network.network_flow_summary.NetworkFlowSummary)]



--------------

More detailed (and user-friendly) help in the ``show_help()`` method
====================================================================

.. code:: ipython3

    nb.nblts.azsent.host.HostSummary.show_help()



.. raw:: html

    <h1>Notebooklet Class - HostSummary</h1>
    <p>HostSummary Notebooklet class.</p>
    <p>Queries and displays information about a host including:</p>
    <ul>
    <li>
    <p>IP address assignment</p>
    </li>
    <li>
    <p>Related alerts</p>
    </li>
    <li>
    <p>Related hunting/investigation bookmarks</p>
    </li>
    <li>
    <p>Azure subscription/resource data.</p>
    </li>
    </ul>
    <p><strong>Default Options
    </strong></p>
    <p>heartbeat: Query Heartbeat table for host information.</p>
    <p>azure_net: Query AzureNetworkAnalytics table for host network topology information.</p>
    <p>alerts: Query any alerts for the host.</p>
    <p>bookmarks: Query any bookmarks for the host.</p>
    <p>azure_api: Query Azure API for VM information.</p>
    <p><strong>Other Options
    </strong></p>
    <p>None</p>
    <hr />
    <h1>Display Sections</h1>
    <h2>Host Entity Summary</h2>
    <p>This shows a summary data for a host. It shows host properties obtained from OMS Heartbeat and Azure API.
    It also lists Azure Sentinel alerts and bookmakrs related to to the host.
    Data and plots are stored in the result class returned by this function.</p>
    <h3>Timeline of related alerts</h3>
    <p>Each marker on the timeline indicates one or more alerts related to the host.</p>
    <h3>Host Entity details</h3>
    <p>These are the host entity details gathered from Heartbeat and, if applicable, AzureNetworkAnalytics and Azure management API.
    The data shows OS information, IP Addresses assigned the host and any Azure VM information available.</p>
    <hr />
    <h1>Results Class</h1>
    <h2>HostSummaryResult</h2>
    <p>Host Details Results.</p>
    <h2>Attributes</h2>
    <ul>
    <li>
    <p>host_entity : msticpy.data.nbtools.entities.Host<br>
    The host entity object contains data about the host
    such as name, environment, operating system version,
    IP addresses and Azure VM details. Depending on the
    type of host, not all of this data may be populated.</p>
    </li>
    <li>
    <p>related_alerts : pd.DataFrame<br>
    Pandas DataFrame of any alerts recorded for the host
    within the query time span.</p>
    </li>
    <li>
    <p>alert_timeline:<br>
    Bokeh time plot of alerts recorded for host.</p>
    </li>
    <li>
    <p>related_bookmarks: pd.DataFrame<br>
    Pandas DataFrame of any investigation bookmarks
    relating to the host.</p>
    </li>
    </ul>
    <hr />
    <h1>Methods</h1>
    <h2>Instance Methods</h2>
    <h3>get_provider</h3>
    <p>get_provider(self, provider_name:str)
    Return data provider for the specified name.</p>
    <h3>run</h3>
    <p>run(self, value:Any=None, data:Union[pandas.core.frame.DataFrame, NoneType]=None, timespan:Union[msticnb.common.TimeSpan, NoneType]=None, options:Union[Iterable[str], NoneType]=None, **kwargs) -&gt; msticnb.nb.azsent.host.host_summary.HostSummaryResult
    Return host summary data.</p>
    <h2>Other Methods</h2>
    <h3>all_options</h3>
    <p>all_options() -&gt; List[str]
    Return supported options for Notebooklet run function.</p>
    <h3>default_options</h3>
    <p>default_options() -&gt; List[str]
    Return default options for Notebooklet run function.</p>
    <h3>description</h3>
    <p>description() -&gt; str
    Return description of the Notebooklet.</p>
    <h3>entity_types</h3>
    <p>entity_types() -&gt; List[str]
    Entity types supported by the notebooklet.</p>
    <h3>get_help</h3>
    <p>get_help(fmt='html') -&gt; str
    Return HTML document for class.</p>
    <h3>get_settings</h3>
    <p>get_settings(print_settings=True) -&gt; Union[str, NoneType]
    Print or return metadata for class.</p>
    <h3>import_cell</h3>
    <p>import_cell()
    Import the text of this module into a new cell.</p>
    <h3>keywords</h3>
    <p>keywords() -&gt; List[str]
    Return search keywords for Notebooklet.</p>
    <h3>list_options</h3>
    <p>list_options() -&gt; str
    Return default options for Notebooklet run function.</p>
    <h3>match_terms</h3>
    <p>match_terms(search_terms:str) -&gt; Tuple[bool, int]
    Search class definition for <code>search_terms</code>.</p>
    <h3>name</h3>
    <p>name() -&gt; str
    Return name of the Notebooklet.</p>
    <h3>result</h3>
    <p>result [property]
    Return result of the most recent notebooklet run.</p>
    <h3>show_help</h3>
    <p>show_help()
    Display Documentation for class.</p>
    <h3>silent</h3>
    <p>silent [property]
    Get the current instance setting for silent running.</p>


--------------

How are notebooklets used?
==========================

Most require time range parameters
----------------------------------

Usually the notebooklet also the ID of the entity that you’re running
the notebooklet for. For example, a host name, an IP Address, etc.

Some notebooklets process data in the form of a dataframe. Use the
``data`` parameter to pass this.

   **Note** You can also pass other parameters used by the notebooklet
   as keyword arguments (``**kwargs``)

.. code:: ipython3

    time_span = nbwidgets.QueryTime(auto_display=True, units="day", origin_time=pd.to_datetime("2019-02-10"), before=10)
    from msticnb.common import TimeSpan



.. parsed-literal::

    HTML(value='<h4>Set query time boundaries</h4>')



.. parsed-literal::

    HBox(children=(DatePicker(value=datetime.date(2019, 2, 10), description='Origin Date'), Text(value='00:00:00',…



.. parsed-literal::

    VBox(children=(IntRangeSlider(value=(-10, 10), description='Time Range (day):', layout=Layout(width='80%'), mi…


Run the notebooklet using the ``run()`` method
----------------------------------------------

   **Note:** You’ll want to assign the return value of ``run()`` to
   something or terminate with a semicolon Both the notebooklet and the
   return ``result`` class generate displayable output - so you’ll get a
   lot of duplicated output.

.. code:: ipython3

    host_summary = nb.nblts.azsent.host.HostSummary()
    host_sum_rslt = host_summary.run(value="Msticalertswin1", timespan=(time_span.start, time_span.end))



.. raw:: html

    <h1>Host Entity Summary</h1>



.. raw:: html

    This shows a summary data for a host. It shows host properties obtained from OMS Heartbeat and Azure API.<br>It also lists Azure Sentinel alerts and bookmakrs related to to the host.<br>Data and plots are stored in the result class returned by this function.


::


    ---------------------------------------------------------------------------

    AttributeError                            Traceback (most recent call last)

    <ipython-input-16-3fdf95fed462> in <module>
          1 host_summary = nb.nblts.azsent.host.HostSummary()
    ----> 2 host_sum_rslt = host_summary.run(value="Msticalertswin1", timespan=(time_span.start, time_span.end))


    e:\src\msticnb\msticnb\common.py in print_text(*args, **kwargs)
        347                         display(HTML(f"<br><b>{sec_title}</b><br>"))
        348                         display(HTML(content.replace("\n", "<br>")))
    --> 349             return func(*args, **kwargs)
        350
        351         return print_text


    e:\src\msticnb\msticnb\nb\azsent\host\host_summary.py in run(self, value, data, timespan, options, **kwargs)
        147         # pylint: disable=attribute-defined-outside-init
        148         result = HostSummaryResult()
    --> 149         result.description = self.NBMetadata.description
        150         result.timespan = timespan
        151


    AttributeError: 'HostSummary' object has no attribute 'NBMetadata'


Result classes content can be displayed in the notebook
-------------------------------------------------------

Use ``display(result)`` if you want to display the content in the middle
of a cell

.. code:: ipython3

    host_sum_rslt



.. raw:: html







    <div class="bk-root" id="84058926-d7a3-418d-86f0-179f39f251e3" data-root-id="1074"></div>







.. raw:: html

    <h4>description</h4>Host&nbsp;summary<br><h4>timespan</h4>[Timestamp('2019-01-31&nbsp;00:00:00'),&nbsp;Timestamp('2019-02-20&nbsp;00:00:00')]<br><h4>host_entity</h4>[msticpy.data.nbtools.entities.Host]<br>The host entity object contains data about the host such as name, environment, operating system version, IP addresses and Azure VM details. Depending on the type of host, not all of this data may be populated.<br>{'AdditionalData':&nbsp;{},&nbsp;'HostName':&nbsp;'Msticalertswin1',&nbsp;'Type':&nbsp;'host'}<br><h4>related_alerts</h4>[pd.DataFrame]<br>Pandas DataFrame of any alerts recorded for the host within the query time span.<br><div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }

        .dataframe tbody tr th {
            vertical-align: top;
        }

        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>TenantId</th>
          <th>TimeGenerated</th>
          <th>AlertDisplayName</th>
          <th>AlertName</th>
          <th>Severity</th>
          <th>Description</th>
          <th>ProviderName</th>
          <th>VendorName</th>
          <th>VendorOriginalId</th>
          <th>SystemAlertId</th>
          <th>ResourceId</th>
          <th>SourceComputerId</th>
          <th>AlertType</th>
          <th>ConfidenceLevel</th>
          <th>ConfidenceScore</th>
          <th>IsIncident</th>
          <th>StartTimeUtc</th>
          <th>EndTimeUtc</th>
          <th>ProcessingEndTime</th>
          <th>RemediationSteps</th>
          <th>ExtendedProperties</th>
          <th>Entities</th>
          <th>SourceSystem</th>
          <th>WorkspaceSubscriptionId</th>
          <th>WorkspaceResourceGroup</th>
          <th>ExtendedLinks</th>
          <th>ProductName</th>
          <th>ProductComponentName</th>
          <th>AlertLink</th>
          <th>Type</th>
          <th>CompromisedEntity</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-18 02:29:07</td>
          <td>SSH Anomalous Login ML</td>
          <td>SSH Anomalous Login ML</td>
          <td>Low</td>
          <td>Anomalous login detected for SSH account</td>
          <td>CustomAlertRule</td>
          <td>Alert Rule</td>
          <td>b0e143b8-4fa8-47bc-8bc1-9780c8b75541</td>
          <td>f1ce87ca-8863-4a66-a0bd-a4d3776a7c64</td>
          <td></td>
          <td></td>
          <td>CustomAlertRule_0a4e5f7c-9756-45f8-83c4-94c756844698</td>
          <td>Unknown</td>
          <td>NaN</td>
          <td>False</td>
          <td>2019-02-18 01:49:02</td>
          <td>2019-02-18 02:19:02</td>
          <td>2019-02-18 02:29:07</td>
          <td></td>
          <td>{\r\n  "Alert Mode": "Aggregated",\r\n  "Search Query": "{\"detailBladeInputs\":{\"id\":\"/subsc...</td>
          <td>[\r\n  {\r\n    "$id": "3",\r\n    "Address": "23.97.60.214",\r\n    "Type": "ip",\r\n    "Count...</td>
          <td>Detection</td>
          <td>40dcc8bf-0478-4f3b-b275-ed0a94f2c013</td>
          <td>asihuntomsworkspacerg</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>SecurityAlert</td>
          <td></td>
        </tr>
        <tr>
          <th>1</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-18 01:59:09</td>
          <td>SSH Anomalous Login ML</td>
          <td>SSH Anomalous Login ML</td>
          <td>Low</td>
          <td>Anomalous login detected for SSH account</td>
          <td>CustomAlertRule</td>
          <td>Alert Rule</td>
          <td>4f454388-02d3-4ace-98bf-3a7e4fdef361</td>
          <td>3968ef4e-b322-48ca-b297-e984aff8888d</td>
          <td></td>
          <td></td>
          <td>CustomAlertRule_0a4e5f7c-9756-45f8-83c4-94c756844698</td>
          <td>Unknown</td>
          <td>NaN</td>
          <td>False</td>
          <td>2019-02-18 01:19:02</td>
          <td>2019-02-18 01:49:02</td>
          <td>2019-02-18 01:59:09</td>
          <td></td>
          <td>{\r\n  "Alert Mode": "Aggregated",\r\n  "Search Query": "{\"detailBladeInputs\":{\"id\":\"/subsc...</td>
          <td>[\r\n  {\r\n    "$id": "3",\r\n    "Address": "203.0.113.1",\r\n    "Type": "ip",\r\n    "Count"...</td>
          <td>Detection</td>
          <td>40dcc8bf-0478-4f3b-b275-ed0a94f2c013</td>
          <td>asihuntomsworkspacerg</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>SecurityAlert</td>
          <td></td>
        </tr>
        <tr>
          <th>2</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-18 02:29:07</td>
          <td>SSH Anomalous Login ML</td>
          <td>SSH Anomalous Login ML</td>
          <td>Low</td>
          <td>Anomalous login detected for SSH account</td>
          <td>CustomAlertRule</td>
          <td>Alert Rule</td>
          <td>b0e143b8-4fa8-47bc-8bc1-9780c8b75541</td>
          <td>3a78a119-abe9-4b5e-9786-300ddcfd9530</td>
          <td></td>
          <td></td>
          <td>CustomAlertRule_0a4e5f7c-9756-45f8-83c4-94c756844698</td>
          <td>Unknown</td>
          <td>NaN</td>
          <td>False</td>
          <td>2019-02-18 01:49:02</td>
          <td>2019-02-18 02:19:02</td>
          <td>2019-02-18 02:29:07</td>
          <td></td>
          <td>{\r\n  "Alert Mode": "Aggregated",\r\n  "Search Query": "{\"detailBladeInputs\":{\"id\":\"/subsc...</td>
          <td>[\r\n  {\r\n    "$id": "3",\r\n    "Address": "23.97.60.214",\r\n    "Type": "ip",\r\n    "Count...</td>
          <td>Detection</td>
          <td>40dcc8bf-0478-4f3b-b275-ed0a94f2c013</td>
          <td>asihuntomsworkspacerg</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>SecurityAlert</td>
          <td></td>
        </tr>
        <tr>
          <th>3</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-18 02:43:27</td>
          <td>SSH Anomalous Login ML</td>
          <td>SSH Anomalous Login ML</td>
          <td>Low</td>
          <td>Anomalous login detected for SSH account</td>
          <td>CustomAlertRule</td>
          <td>Alert Rule</td>
          <td>3f27593a-db5b-4ef4-bdc5-f6ce1915f496</td>
          <td>8f622935-1422-41e6-b8f6-9119e681645c</td>
          <td></td>
          <td></td>
          <td>CustomAlertRule_0a4e5f7c-9756-45f8-83c4-94c756844698</td>
          <td>Unknown</td>
          <td>NaN</td>
          <td>False</td>
          <td>2019-02-18 01:33:19</td>
          <td>2019-02-18 02:33:19</td>
          <td>2019-02-18 02:43:27</td>
          <td></td>
          <td>{\r\n  "Alert Mode": "Aggregated",\r\n  "Search Query": "{\"detailBladeInputs\":{\"id\":\"/subsc...</td>
          <td>[\r\n  {\r\n    "$id": "3",\r\n    "Address": "23.97.60.214",\r\n    "Type": "ip",\r\n    "Count...</td>
          <td>Detection</td>
          <td>40dcc8bf-0478-4f3b-b275-ed0a94f2c013</td>
          <td>asihuntomsworkspacerg</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>SecurityAlert</td>
          <td></td>
        </tr>
        <tr>
          <th>4</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-18 01:54:11</td>
          <td>SSH Anomalous Login ML</td>
          <td>SSH Anomalous Login ML</td>
          <td>Low</td>
          <td>Anomalous login detected for SSH account</td>
          <td>CustomAlertRule</td>
          <td>Alert Rule</td>
          <td>3cbe0028-14e8-43ad-8dc2-77c96d8bb015</td>
          <td>64a2b4af-c3d7-422c-820b-7f1feb664222</td>
          <td></td>
          <td></td>
          <td>CustomAlertRule_0a4e5f7c-9756-45f8-83c4-94c756844698</td>
          <td>Unknown</td>
          <td>NaN</td>
          <td>False</td>
          <td>2019-02-18 01:14:02</td>
          <td>2019-02-18 01:44:02</td>
          <td>2019-02-18 01:54:11</td>
          <td></td>
          <td>{\r\n  "Alert Mode": "Aggregated",\r\n  "Search Query": "{\"detailBladeInputs\":{\"id\":\"/subsc...</td>
          <td>[\r\n  {\r\n    "$id": "3",\r\n    "Address": "203.0.113.1",\r\n    "Type": "ip",\r\n    "Count"...</td>
          <td>Detection</td>
          <td>40dcc8bf-0478-4f3b-b275-ed0a94f2c013</td>
          <td>asihuntomsworkspacerg</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>SecurityAlert</td>
          <td></td>
        </tr>
      </tbody>
    </table>
    </div><br><h4>alert_timeline</h4>Bokeh time plot of alerts recorded for host.<br><div style="display: table;"><div style="display: table-row;"><div style="display: table-cell;"><b title="bokeh.models.layouts.Column">Column</b>(</div><div style="display: table-cell;">id&nbsp;=&nbsp;'1074', <span id="1522" style="cursor: pointer;">&hellip;)</span></div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">align&nbsp;=&nbsp;'start',</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">aspect_ratio&nbsp;=&nbsp;None,</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">background&nbsp;=&nbsp;None,</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">children&nbsp;=&nbsp;[Figure(id='1004', ...), Figure(id='1037', ...)],</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">css_classes&nbsp;=&nbsp;[],</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">disabled&nbsp;=&nbsp;False,</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">height&nbsp;=&nbsp;None,</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">height_policy&nbsp;=&nbsp;'auto',</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">js_event_callbacks&nbsp;=&nbsp;{},</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">js_property_callbacks&nbsp;=&nbsp;{},</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">margin&nbsp;=&nbsp;(0, 0, 0, 0),</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">max_height&nbsp;=&nbsp;None,</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">max_width&nbsp;=&nbsp;None,</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">min_height&nbsp;=&nbsp;None,</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">min_width&nbsp;=&nbsp;None,</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">name&nbsp;=&nbsp;None,</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">rows&nbsp;=&nbsp;'auto',</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">sizing_mode&nbsp;=&nbsp;None,</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">spacing&nbsp;=&nbsp;0,</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">subscribed_events&nbsp;=&nbsp;[],</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">tags&nbsp;=&nbsp;[],</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">visible&nbsp;=&nbsp;True,</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">width&nbsp;=&nbsp;None,</div></div><div class="1521" style="display: none;"><div style="display: table-cell;"></div><div style="display: table-cell;">width_policy&nbsp;=&nbsp;'auto')</div></div></div>
    <script>
    (function() {
      var expanded = false;
      var ellipsis = document.getElementById("1522");
      ellipsis.addEventListener("click", function() {
        var rows = document.getElementsByClassName("1521");
        for (var i = 0; i < rows.length; i++) {
          var el = rows[i];
          el.style.display = expanded ? "none" : "table-row";
        }
        ellipsis.innerHTML = expanded ? "&hellip;)" : "&lsaquo;&lsaquo;&lsaquo;";
        expanded = !expanded;
      });
    })();
    </script>
    <br><h4>related_bookmarks</h4>[pd.DataFrame]<br>Pandas DataFrame of any investigation bookmarks relating to the host.<br><div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }

        .dataframe tbody tr th {
            vertical-align: top;
        }

        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>TenantId</th>
          <th>TimeGenerated</th>
          <th>AlertDisplayName</th>
          <th>AlertName</th>
          <th>Severity</th>
          <th>Description</th>
          <th>ProviderName</th>
          <th>VendorName</th>
          <th>VendorOriginalId</th>
          <th>SystemAlertId</th>
          <th>ResourceId</th>
          <th>SourceComputerId</th>
          <th>AlertType</th>
          <th>ConfidenceLevel</th>
          <th>ConfidenceScore</th>
          <th>IsIncident</th>
          <th>StartTimeUtc</th>
          <th>EndTimeUtc</th>
          <th>ProcessingEndTime</th>
          <th>RemediationSteps</th>
          <th>ExtendedProperties</th>
          <th>Entities</th>
          <th>SourceSystem</th>
          <th>WorkspaceSubscriptionId</th>
          <th>WorkspaceResourceGroup</th>
          <th>ExtendedLinks</th>
          <th>ProductName</th>
          <th>ProductComponentName</th>
          <th>AlertLink</th>
          <th>Type</th>
          <th>CompromisedEntity</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-18 02:29:07</td>
          <td>SSH Anomalous Login ML</td>
          <td>SSH Anomalous Login ML</td>
          <td>Low</td>
          <td>Anomalous login detected for SSH account</td>
          <td>CustomAlertRule</td>
          <td>Alert Rule</td>
          <td>b0e143b8-4fa8-47bc-8bc1-9780c8b75541</td>
          <td>f1ce87ca-8863-4a66-a0bd-a4d3776a7c64</td>
          <td></td>
          <td></td>
          <td>CustomAlertRule_0a4e5f7c-9756-45f8-83c4-94c756844698</td>
          <td>Unknown</td>
          <td>NaN</td>
          <td>False</td>
          <td>2019-02-18 01:49:02</td>
          <td>2019-02-18 02:19:02</td>
          <td>2019-02-18 02:29:07</td>
          <td></td>
          <td>{\r\n  "Alert Mode": "Aggregated",\r\n  "Search Query": "{\"detailBladeInputs\":{\"id\":\"/subsc...</td>
          <td>[\r\n  {\r\n    "$id": "3",\r\n    "Address": "23.97.60.214",\r\n    "Type": "ip",\r\n    "Count...</td>
          <td>Detection</td>
          <td>40dcc8bf-0478-4f3b-b275-ed0a94f2c013</td>
          <td>asihuntomsworkspacerg</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>SecurityAlert</td>
          <td></td>
        </tr>
        <tr>
          <th>1</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-18 01:59:09</td>
          <td>SSH Anomalous Login ML</td>
          <td>SSH Anomalous Login ML</td>
          <td>Low</td>
          <td>Anomalous login detected for SSH account</td>
          <td>CustomAlertRule</td>
          <td>Alert Rule</td>
          <td>4f454388-02d3-4ace-98bf-3a7e4fdef361</td>
          <td>3968ef4e-b322-48ca-b297-e984aff8888d</td>
          <td></td>
          <td></td>
          <td>CustomAlertRule_0a4e5f7c-9756-45f8-83c4-94c756844698</td>
          <td>Unknown</td>
          <td>NaN</td>
          <td>False</td>
          <td>2019-02-18 01:19:02</td>
          <td>2019-02-18 01:49:02</td>
          <td>2019-02-18 01:59:09</td>
          <td></td>
          <td>{\r\n  "Alert Mode": "Aggregated",\r\n  "Search Query": "{\"detailBladeInputs\":{\"id\":\"/subsc...</td>
          <td>[\r\n  {\r\n    "$id": "3",\r\n    "Address": "203.0.113.1",\r\n    "Type": "ip",\r\n    "Count"...</td>
          <td>Detection</td>
          <td>40dcc8bf-0478-4f3b-b275-ed0a94f2c013</td>
          <td>asihuntomsworkspacerg</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>SecurityAlert</td>
          <td></td>
        </tr>
        <tr>
          <th>2</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-18 02:29:07</td>
          <td>SSH Anomalous Login ML</td>
          <td>SSH Anomalous Login ML</td>
          <td>Low</td>
          <td>Anomalous login detected for SSH account</td>
          <td>CustomAlertRule</td>
          <td>Alert Rule</td>
          <td>b0e143b8-4fa8-47bc-8bc1-9780c8b75541</td>
          <td>3a78a119-abe9-4b5e-9786-300ddcfd9530</td>
          <td></td>
          <td></td>
          <td>CustomAlertRule_0a4e5f7c-9756-45f8-83c4-94c756844698</td>
          <td>Unknown</td>
          <td>NaN</td>
          <td>False</td>
          <td>2019-02-18 01:49:02</td>
          <td>2019-02-18 02:19:02</td>
          <td>2019-02-18 02:29:07</td>
          <td></td>
          <td>{\r\n  "Alert Mode": "Aggregated",\r\n  "Search Query": "{\"detailBladeInputs\":{\"id\":\"/subsc...</td>
          <td>[\r\n  {\r\n    "$id": "3",\r\n    "Address": "23.97.60.214",\r\n    "Type": "ip",\r\n    "Count...</td>
          <td>Detection</td>
          <td>40dcc8bf-0478-4f3b-b275-ed0a94f2c013</td>
          <td>asihuntomsworkspacerg</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>SecurityAlert</td>
          <td></td>
        </tr>
        <tr>
          <th>3</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-18 02:43:27</td>
          <td>SSH Anomalous Login ML</td>
          <td>SSH Anomalous Login ML</td>
          <td>Low</td>
          <td>Anomalous login detected for SSH account</td>
          <td>CustomAlertRule</td>
          <td>Alert Rule</td>
          <td>3f27593a-db5b-4ef4-bdc5-f6ce1915f496</td>
          <td>8f622935-1422-41e6-b8f6-9119e681645c</td>
          <td></td>
          <td></td>
          <td>CustomAlertRule_0a4e5f7c-9756-45f8-83c4-94c756844698</td>
          <td>Unknown</td>
          <td>NaN</td>
          <td>False</td>
          <td>2019-02-18 01:33:19</td>
          <td>2019-02-18 02:33:19</td>
          <td>2019-02-18 02:43:27</td>
          <td></td>
          <td>{\r\n  "Alert Mode": "Aggregated",\r\n  "Search Query": "{\"detailBladeInputs\":{\"id\":\"/subsc...</td>
          <td>[\r\n  {\r\n    "$id": "3",\r\n    "Address": "23.97.60.214",\r\n    "Type": "ip",\r\n    "Count...</td>
          <td>Detection</td>
          <td>40dcc8bf-0478-4f3b-b275-ed0a94f2c013</td>
          <td>asihuntomsworkspacerg</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>SecurityAlert</td>
          <td></td>
        </tr>
        <tr>
          <th>4</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-18 01:54:11</td>
          <td>SSH Anomalous Login ML</td>
          <td>SSH Anomalous Login ML</td>
          <td>Low</td>
          <td>Anomalous login detected for SSH account</td>
          <td>CustomAlertRule</td>
          <td>Alert Rule</td>
          <td>3cbe0028-14e8-43ad-8dc2-77c96d8bb015</td>
          <td>64a2b4af-c3d7-422c-820b-7f1feb664222</td>
          <td></td>
          <td></td>
          <td>CustomAlertRule_0a4e5f7c-9756-45f8-83c4-94c756844698</td>
          <td>Unknown</td>
          <td>NaN</td>
          <td>False</td>
          <td>2019-02-18 01:14:02</td>
          <td>2019-02-18 01:44:02</td>
          <td>2019-02-18 01:54:11</td>
          <td></td>
          <td>{\r\n  "Alert Mode": "Aggregated",\r\n  "Search Query": "{\"detailBladeInputs\":{\"id\":\"/subsc...</td>
          <td>[\r\n  {\r\n    "$id": "3",\r\n    "Address": "203.0.113.1",\r\n    "Type": "ip",\r\n    "Count"...</td>
          <td>Detection</td>
          <td>40dcc8bf-0478-4f3b-b275-ed0a94f2c013</td>
          <td>asihuntomsworkspacerg</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>SecurityAlert</td>
          <td></td>
        </tr>
      </tbody>
    </table>
    </div>



--------------

Simple Notebooklet browser
--------------------------

.. code:: ipython3

    nb.browse()



.. parsed-literal::

    VBox(children=(HBox(children=(VBox(children=(Select(options=(('HostSummary', <class 'msticnb.nb.azsent.host.ho…




.. parsed-literal::

    <msticnb.nb_browser.NBBrowser at 0x1cca20b1ef0>



.. code:: ipython3

    # value="MSTICAlertsWin1", timespan=time_span

    win_host_events = nb.nblts.azsent.host.WinHostEvents()
    timespan = TimeSpan(start="2020-05-07 00:10")
    win_host_events_rslt = win_host_events.run(value="MSTICAlertsWin1", timespan=timespan)



.. raw:: html

    <h1>Host Security Events Summary</h1>



.. raw:: html

    This shows a summary of security events for the host. These are grouped by EventID and Account.<br>Data and plots are stored in the result class returned by this function.


.. parsed-literal::

    Getting data from SecurityEvent...



.. raw:: html

    <h2>Summary of Security Events on host</h2>



.. raw:: html

    This is a summary of Security events for the host (excluding process creation and account logon - 4688, 4624, 4625).<br>Yellow highlights indicate account with highest event count for an EventID.



.. raw:: html

    <style  type="text/css" >
        #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col8 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col8 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col4 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col10 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col2 {
                : ;
                background-color:  lightblue;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col5 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col10 {
                : ;
                background-color:  lightblue;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col5 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col6 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col1 {
                : ;
                background-color:  lightblue;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col2 {
                : ;
                background-color:  lightblue;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col3 {
                : ;
                background-color:  lightblue;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col4 {
                : ;
                background-color:  lightblue;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col5 {
                : ;
                background-color:  lightblue;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col7 {
                : ;
                background-color:  lightblue;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col9 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col5 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col5 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col5 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col5 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col5 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col5 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col5 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col5 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col5 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col8 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col5 {
                : ;
                background-color:  lightblue;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col6 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col5 {
                : ;
                background-color:  lightblue;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col6 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col8 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col8 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col6 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col6 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col8 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col8 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col8 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col4 {
                : ;
                background-color:  lightblue;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col6 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col8 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col5 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col8 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col9 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col10 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col1 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col2 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col3 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col4 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col5 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col6 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col7 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col8 {
                color:  white;
                : ;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col9 {
                : ;
                background-color:  lightblue;
                : ;
            }    #T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col10 {
                color:  white;
                : ;
                : ;
            }</style><table id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7" ><thead>    <tr>        <th class="col_heading level0 col0" >Activity</th>        <th class="col_heading level0 col1" >DWM-1</th>        <th class="col_heading level0 col2" >DWM-2</th>        <th class="col_heading level0 col3" >IUSR</th>        <th class="col_heading level0 col4" >LOCAL SERVICE</th>        <th class="col_heading level0 col5" >MSTICAdmin</th>        <th class="col_heading level0 col6" >MSTICAlertsWin1$</th>        <th class="col_heading level0 col7" >NETWORK SERVICE</th>        <th class="col_heading level0 col8" >No Account</th>        <th class="col_heading level0 col9" >SYSTEM</th>        <th class="col_heading level0 col10" >ian</th>    </tr></thead><tbody>
                    <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col0" class="data row0 col0" >1100 - The event logging service has shut down.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col1" class="data row0 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col2" class="data row0 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col3" class="data row0 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col4" class="data row0 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col5" class="data row0 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col6" class="data row0 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col7" class="data row0 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col8" class="data row0 col8" >1</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col9" class="data row0 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row0_col10" class="data row0 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col0" class="data row1 col0" >4608 - Windows is starting up.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col1" class="data row1 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col2" class="data row1 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col3" class="data row1 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col4" class="data row1 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col5" class="data row1 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col6" class="data row1 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col7" class="data row1 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col8" class="data row1 col8" >1</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col9" class="data row1 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row1_col10" class="data row1 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col0" class="data row2 col0" >4616 - The system time was changed.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col1" class="data row2 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col2" class="data row2 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col3" class="data row2 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col4" class="data row2 col4" >2</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col5" class="data row2 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col6" class="data row2 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col7" class="data row2 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col8" class="data row2 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col9" class="data row2 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row2_col10" class="data row2 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col0" class="data row3 col0" >4625 - An account failed to log on.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col1" class="data row3 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col2" class="data row3 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col3" class="data row3 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col4" class="data row3 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col5" class="data row3 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col6" class="data row3 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col7" class="data row3 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col8" class="data row3 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col9" class="data row3 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row3_col10" class="data row3 col10" >2</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col0" class="data row4 col0" >4634 - An account was logged off.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col1" class="data row4 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col2" class="data row4 col2" >4</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col3" class="data row4 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col4" class="data row4 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col5" class="data row4 col5" >12</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col6" class="data row4 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col7" class="data row4 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col8" class="data row4 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col9" class="data row4 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row4_col10" class="data row4 col10" >2</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col0" class="data row5 col0" >4647 - User initiated logoff.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col1" class="data row5 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col2" class="data row5 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col3" class="data row5 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col4" class="data row5 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col5" class="data row5 col5" >2</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col6" class="data row5 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col7" class="data row5 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col8" class="data row5 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col9" class="data row5 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row5_col10" class="data row5 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col0" class="data row6 col0" >4648 - A logon was attempted using explicit credentials.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col1" class="data row6 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col2" class="data row6 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col3" class="data row6 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col4" class="data row6 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col5" class="data row6 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col6" class="data row6 col6" >10</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col7" class="data row6 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col8" class="data row6 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col9" class="data row6 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row6_col10" class="data row6 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col0" class="data row7 col0" >4672 - Special privileges assigned to new logon.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col1" class="data row7 col1" >2</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col2" class="data row7 col2" >2</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col3" class="data row7 col3" >1</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col4" class="data row7 col4" >1</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col5" class="data row7 col5" >14</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col6" class="data row7 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col7" class="data row7 col7" >1</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col8" class="data row7 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col9" class="data row7 col9" >60</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row7_col10" class="data row7 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col0" class="data row8 col0" >4720 - A user account was created.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col1" class="data row8 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col2" class="data row8 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col3" class="data row8 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col4" class="data row8 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col5" class="data row8 col5" >2</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col6" class="data row8 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col7" class="data row8 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col8" class="data row8 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col9" class="data row8 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row8_col10" class="data row8 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col0" class="data row9 col0" >4722 - A user account was enabled.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col1" class="data row9 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col2" class="data row9 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col3" class="data row9 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col4" class="data row9 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col5" class="data row9 col5" >2</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col6" class="data row9 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col7" class="data row9 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col8" class="data row9 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col9" class="data row9 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row9_col10" class="data row9 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col0" class="data row10 col0" >4724 - An attempt was made to reset an account's password.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col1" class="data row10 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col2" class="data row10 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col3" class="data row10 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col4" class="data row10 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col5" class="data row10 col5" >4</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col6" class="data row10 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col7" class="data row10 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col8" class="data row10 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col9" class="data row10 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row10_col10" class="data row10 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col0" class="data row11 col0" >4726 - A user account was deleted.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col1" class="data row11 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col2" class="data row11 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col3" class="data row11 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col4" class="data row11 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col5" class="data row11 col5" >2</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col6" class="data row11 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col7" class="data row11 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col8" class="data row11 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col9" class="data row11 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row11_col10" class="data row11 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col0" class="data row12 col0" >4728 - A member was added to a security-enabled global group.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col1" class="data row12 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col2" class="data row12 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col3" class="data row12 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col4" class="data row12 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col5" class="data row12 col5" >2</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col6" class="data row12 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col7" class="data row12 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col8" class="data row12 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col9" class="data row12 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row12_col10" class="data row12 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col0" class="data row13 col0" >4729 - A member was removed from a security-enabled global group.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col1" class="data row13 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col2" class="data row13 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col3" class="data row13 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col4" class="data row13 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col5" class="data row13 col5" >2</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col6" class="data row13 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col7" class="data row13 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col8" class="data row13 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col9" class="data row13 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row13_col10" class="data row13 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col0" class="data row14 col0" >4732 - A member was added to a security-enabled local group.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col1" class="data row14 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col2" class="data row14 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col3" class="data row14 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col4" class="data row14 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col5" class="data row14 col5" >4</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col6" class="data row14 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col7" class="data row14 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col8" class="data row14 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col9" class="data row14 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row14_col10" class="data row14 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col0" class="data row15 col0" >4733 - A member was removed from a security-enabled local group.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col1" class="data row15 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col2" class="data row15 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col3" class="data row15 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col4" class="data row15 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col5" class="data row15 col5" >3</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col6" class="data row15 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col7" class="data row15 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col8" class="data row15 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col9" class="data row15 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row15_col10" class="data row15 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col0" class="data row16 col0" >4738 - A user account was changed.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col1" class="data row16 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col2" class="data row16 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col3" class="data row16 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col4" class="data row16 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col5" class="data row16 col5" >5</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col6" class="data row16 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col7" class="data row16 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col8" class="data row16 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col9" class="data row16 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row16_col10" class="data row16 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col0" class="data row17 col0" >4776 - The domain controller attempted to validate the credentials for an account.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col1" class="data row17 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col2" class="data row17 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col3" class="data row17 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col4" class="data row17 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col5" class="data row17 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col6" class="data row17 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col7" class="data row17 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col8" class="data row17 col8" >18</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col9" class="data row17 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row17_col10" class="data row17 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col0" class="data row18 col0" >4798 - A user's local group membership was enumerated.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col1" class="data row18 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col2" class="data row18 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col3" class="data row18 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col4" class="data row18 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col5" class="data row18 col5" >14</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col6" class="data row18 col6" >652</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col7" class="data row18 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col8" class="data row18 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col9" class="data row18 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row18_col10" class="data row18 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col0" class="data row19 col0" >4799 - A security-enabled local group membership was enumerated</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col1" class="data row19 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col2" class="data row19 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col3" class="data row19 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col4" class="data row19 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col5" class="data row19 col5" >4</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col6" class="data row19 col6" >236</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col7" class="data row19 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col8" class="data row19 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col9" class="data row19 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row19_col10" class="data row19 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col0" class="data row20 col0" >4826 - Boot Configuration Data loaded.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col1" class="data row20 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col2" class="data row20 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col3" class="data row20 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col4" class="data row20 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col5" class="data row20 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col6" class="data row20 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col7" class="data row20 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col8" class="data row20 col8" >1</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col9" class="data row20 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row20_col10" class="data row20 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col0" class="data row21 col0" >4902 - The Per-user audit policy table was created.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col1" class="data row21 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col2" class="data row21 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col3" class="data row21 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col4" class="data row21 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col5" class="data row21 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col6" class="data row21 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col7" class="data row21 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col8" class="data row21 col8" >1</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col9" class="data row21 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row21_col10" class="data row21 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col0" class="data row22 col0" >4904 - An attempt was made to register a security event source.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col1" class="data row22 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col2" class="data row22 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col3" class="data row22 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col4" class="data row22 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col5" class="data row22 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col6" class="data row22 col6" >1</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col7" class="data row22 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col8" class="data row22 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col9" class="data row22 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row22_col10" class="data row22 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col0" class="data row23 col0" >4907 - Auditing settings on object were changed.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col1" class="data row23 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col2" class="data row23 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col3" class="data row23 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col4" class="data row23 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col5" class="data row23 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col6" class="data row23 col6" >198</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col7" class="data row23 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col8" class="data row23 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col9" class="data row23 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row23_col10" class="data row23 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col0" class="data row24 col0" >5024 - The Windows Firewall Service has started successfully.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col1" class="data row24 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col2" class="data row24 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col3" class="data row24 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col4" class="data row24 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col5" class="data row24 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col6" class="data row24 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col7" class="data row24 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col8" class="data row24 col8" >1</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col9" class="data row24 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row24_col10" class="data row24 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col0" class="data row25 col0" >5033 - The Windows Firewall Driver has started successfully.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col1" class="data row25 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col2" class="data row25 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col3" class="data row25 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col4" class="data row25 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col5" class="data row25 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col6" class="data row25 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col7" class="data row25 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col8" class="data row25 col8" >1</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col9" class="data row25 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row25_col10" class="data row25 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col0" class="data row26 col0" >5058 - Key file operation.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col1" class="data row26 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col2" class="data row26 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col3" class="data row26 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col4" class="data row26 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col5" class="data row26 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col6" class="data row26 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col7" class="data row26 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col8" class="data row26 col8" >159</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col9" class="data row26 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row26_col10" class="data row26 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col0" class="data row27 col0" >5059 - Key migration operation.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col1" class="data row27 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col2" class="data row27 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col3" class="data row27 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col4" class="data row27 col4" >1</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col5" class="data row27 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col6" class="data row27 col6" >206</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col7" class="data row27 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col8" class="data row27 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col9" class="data row27 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row27_col10" class="data row27 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col0" class="data row28 col0" >5061 - Cryptographic operation.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col1" class="data row28 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col2" class="data row28 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col3" class="data row28 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col4" class="data row28 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col5" class="data row28 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col6" class="data row28 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col7" class="data row28 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col8" class="data row28 col8" >159</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col9" class="data row28 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row28_col10" class="data row28 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col0" class="data row29 col0" >8001</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col1" class="data row29 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col2" class="data row29 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col3" class="data row29 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col4" class="data row29 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col5" class="data row29 col5" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col6" class="data row29 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col7" class="data row29 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col8" class="data row29 col8" >1</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col9" class="data row29 col9" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row29_col10" class="data row29 col10" >0</td>
                </tr>
                <tr>
                                    <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col0" class="data row30 col0" >8002 - A process was allowed to run.</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col1" class="data row30 col1" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col2" class="data row30 col2" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col3" class="data row30 col3" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col4" class="data row30 col4" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col5" class="data row30 col5" >192</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col6" class="data row30 col6" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col7" class="data row30 col7" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col8" class="data row30 col8" >0</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col9" class="data row30 col9" >12</td>
                            <td id="T_41cb5bda_a778_11ea_af2c_0002723f5ca7row30_col10" class="data row30 col10" >0</td>
                </tr>
        </tbody></table>



.. raw:: html

    <h2>Summary of Account Management Events on host</h2>



.. raw:: html

    This shows the subset of events related to account management, for example, creation/deletion of accounts, changes to group membership, etc.<br>Yellow highlights indicate account with highest event count.



.. raw:: html

    <style  type="text/css" >
        #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row0_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row0_col1 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row1_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row1_col1 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row2_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row2_col1 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row3_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row3_col1 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row4_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row4_col1 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row5_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row5_col1 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row6_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row6_col1 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row7_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row7_col1 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row8_col0 {
                : ;
                : ;
                width:  400px;
                text-align:  left;
            }    #T_41d546d8_a778_11ea_9e4d_0002723f5ca7row8_col1 {
                : ;
                background-color:  lightblue;
                background-color:  yellow;
            }</style><table id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7" ><thead>    <tr>        <th class="col_heading level0 col0" >Activity</th>        <th class="col_heading level0 col1" >MSTICAdmin</th>    </tr></thead><tbody>
                    <tr>
                                    <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row0_col0" class="data row0 col0" >4720 - A user account was created.</td>
                            <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row0_col1" class="data row0 col1" >2</td>
                </tr>
                <tr>
                                    <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row1_col0" class="data row1 col0" >4722 - A user account was enabled.</td>
                            <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row1_col1" class="data row1 col1" >2</td>
                </tr>
                <tr>
                                    <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row2_col0" class="data row2 col0" >4724 - An attempt was made to reset an account's password.</td>
                            <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row2_col1" class="data row2 col1" >4</td>
                </tr>
                <tr>
                                    <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row3_col0" class="data row3 col0" >4726 - A user account was deleted.</td>
                            <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row3_col1" class="data row3 col1" >2</td>
                </tr>
                <tr>
                                    <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row4_col0" class="data row4 col0" >4728 - A member was added to a security-enabled global group.</td>
                            <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row4_col1" class="data row4 col1" >2</td>
                </tr>
                <tr>
                                    <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row5_col0" class="data row5 col0" >4729 - A member was removed from a security-enabled global group.</td>
                            <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row5_col1" class="data row5 col1" >2</td>
                </tr>
                <tr>
                                    <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row6_col0" class="data row6 col0" >4732 - A member was added to a security-enabled local group.</td>
                            <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row6_col1" class="data row6 col1" >4</td>
                </tr>
                <tr>
                                    <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row7_col0" class="data row7 col0" >4733 - A member was removed from a security-enabled local group.</td>
                            <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row7_col1" class="data row7 col1" >3</td>
                </tr>
                <tr>
                                    <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row8_col0" class="data row8 col0" >4738 - A user account was changed.</td>
                            <td id="T_41d546d8_a778_11ea_9e4d_0002723f5ca7row8_col1" class="data row8 col1" >5</td>
                </tr>
        </tbody></table>



.. raw:: html

    <h2>Timeline of Account Management Events on host</h2>



.. raw:: html


    <div class="bk-root">
        <a href="https://bokeh.org" target="_blank" class="bk-logo bk-logo-small bk-logo-notebook"></a>
        <span id="1523">Loading BokehJS ...</span>
    </div>





.. raw:: html







    <div class="bk-root" id="0003fcfd-ab60-43f2-8d7a-639877909091" data-root-id="1694"></div>






.. raw:: html

    <p style=''>To unpack eventdata from selected events use expand_events()</p>


Additional operations apart from ``run()``
------------------------------------------

We can use expand events to unpack the ``EventData`` column for selected
EventIDs

.. code:: ipython3

    win_host_events_rslt.account_events.head(5)




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }

        .dataframe tbody tr th {
            vertical-align: top;
        }

        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>TenantId</th>
          <th>TimeGenerated</th>
          <th>SourceSystem</th>
          <th>Account</th>
          <th>AccountType</th>
          <th>Computer</th>
          <th>EventSourceName</th>
          <th>Channel</th>
          <th>Task</th>
          <th>Level</th>
          <th>EventData</th>
          <th>EventID</th>
          <th>Activity</th>
          <th>PartitionKey</th>
          <th>RowKey</th>
          <th>StorageAccount</th>
          <th>AzureDeploymentID</th>
          <th>AzureTableName</th>
          <th>AccessList</th>
          <th>AccessMask</th>
          <th>AccessReason</th>
          <th>AccountDomain</th>
          <th>AccountExpires</th>
          <th>AccountName</th>
          <th>AccountSessionIdentifier</th>
          <th>...</th>
          <th>TargetUserSid</th>
          <th>TemplateContent</th>
          <th>TemplateDSObjectFQDN</th>
          <th>TemplateInternalName</th>
          <th>TemplateOID</th>
          <th>TemplateSchemaVersion</th>
          <th>TemplateVersion</th>
          <th>TokenElevationType</th>
          <th>TransmittedServices</th>
          <th>UserAccountControl</th>
          <th>UserParameters</th>
          <th>UserPrincipalName</th>
          <th>UserWorkstations</th>
          <th>VirtualAccount</th>
          <th>VendorIds</th>
          <th>Workstation</th>
          <th>WorkstationName</th>
          <th>SourceComputerId</th>
          <th>EventOriginId</th>
          <th>MG</th>
          <th>TimeCollected</th>
          <th>ManagementGroupName</th>
          <th>Type</th>
          <th>_ResourceId</th>
          <th>EventProperties</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>47</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-11 09:58:50.173</td>
          <td>OpsManager</td>
          <td>MSTICAlertsWin1\MSTICAdmin</td>
          <td>User</td>
          <td>MSTICAlertsWin1</td>
          <td>Microsoft-Windows-Security-Auditing</td>
          <td>Security</td>
          <td>13826</td>
          <td>8</td>
          <td>&lt;EventData xmlns="http://schemas.microsoft.com/win/2004/08/events/event"&gt;\r\n  &lt;Data Name="Membe...</td>
          <td>4728</td>
          <td>4728 - A member was added to a security-enabled global group.</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>...</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>263a788b-6526-4cdc-8ed9-d79402fe4aa0</td>
          <td>27df6071-1e81-4e24-934c-dc96667b83ab</td>
          <td>00000000-0000-0000-0000-000000000001</td>
          <td>2019-02-11 09:58:51.400</td>
          <td>AOI-52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>SecurityEvent</td>
          <td>/subscriptions/40dcc8bf-0478-4f3b-b275-ed0a94f2c013/resourcegroups/asihuntomsworkspacerg/provide...</td>
          <td>{'MemberName': '-', 'MemberSid': 'S-1-5-21-996632719-2361334927-4038480536-1118', 'TargetUserNam...</td>
        </tr>
        <tr>
          <th>48</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-11 09:58:50.173</td>
          <td>OpsManager</td>
          <td>MSTICAlertsWin1\MSTICAdmin</td>
          <td>User</td>
          <td>MSTICAlertsWin1</td>
          <td>Microsoft-Windows-Security-Auditing</td>
          <td>Security</td>
          <td>13824</td>
          <td>8</td>
          <td>&lt;EventData xmlns="http://schemas.microsoft.com/win/2004/08/events/event"&gt;\r\n  &lt;Data Name="Targe...</td>
          <td>4720</td>
          <td>4720 - A user account was created.</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>%%1794</td>
          <td></td>
          <td></td>
          <td>...</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>\t\t%%2080 \t\t%%2082 \t\t%%2084</td>
          <td>%%1793</td>
          <td>-</td>
          <td>%%1793</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>263a788b-6526-4cdc-8ed9-d79402fe4aa0</td>
          <td>2c09036a-5ca7-4115-9ddf-e9eb49c14247</td>
          <td>00000000-0000-0000-0000-000000000001</td>
          <td>2019-02-11 09:58:51.400</td>
          <td>AOI-52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>SecurityEvent</td>
          <td>/subscriptions/40dcc8bf-0478-4f3b-b275-ed0a94f2c013/resourcegroups/asihuntomsworkspacerg/provide...</td>
          <td>{'TargetUserName': 'abai$', 'TargetDomainName': 'MSTICAlertsWin1', 'TargetSid': 'S-1-5-21-996632...</td>
        </tr>
        <tr>
          <th>49</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-11 09:58:50.183</td>
          <td>OpsManager</td>
          <td>MSTICAlertsWin1\MSTICAdmin</td>
          <td>User</td>
          <td>MSTICAlertsWin1</td>
          <td>Microsoft-Windows-Security-Auditing</td>
          <td>Security</td>
          <td>13824</td>
          <td>8</td>
          <td>&lt;EventData xmlns="http://schemas.microsoft.com/win/2004/08/events/event"&gt;\r\n  &lt;Data Name="Targe...</td>
          <td>4722</td>
          <td>4722 - A user account was enabled.</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>...</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>263a788b-6526-4cdc-8ed9-d79402fe4aa0</td>
          <td>fefd6761-e431-4cfa-9cd2-c5700f6186df</td>
          <td>00000000-0000-0000-0000-000000000001</td>
          <td>2019-02-11 09:58:51.400</td>
          <td>AOI-52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>SecurityEvent</td>
          <td>/subscriptions/40dcc8bf-0478-4f3b-b275-ed0a94f2c013/resourcegroups/asihuntomsworkspacerg/provide...</td>
          <td>{'TargetUserName': 'abai$', 'TargetDomainName': 'MSTICAlertsWin1', 'TargetSid': 'S-1-5-21-996632...</td>
        </tr>
        <tr>
          <th>50</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-11 09:58:50.183</td>
          <td>OpsManager</td>
          <td>MSTICAlertsWin1\MSTICAdmin</td>
          <td>User</td>
          <td>MSTICAlertsWin1</td>
          <td>Microsoft-Windows-Security-Auditing</td>
          <td>Security</td>
          <td>13824</td>
          <td>8</td>
          <td>&lt;EventData xmlns="http://schemas.microsoft.com/win/2004/08/events/event"&gt;\r\n  &lt;Data Name="Dummy...</td>
          <td>4738</td>
          <td>4738 - A user account was changed.</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>%%1794</td>
          <td></td>
          <td></td>
          <td>...</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>\t\t%%2048 \t\t%%2050</td>
          <td>-</td>
          <td>-</td>
          <td>%%1793</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>263a788b-6526-4cdc-8ed9-d79402fe4aa0</td>
          <td>1d3997a3-9ede-4f9b-877a-eaabc63a3c1e</td>
          <td>00000000-0000-0000-0000-000000000001</td>
          <td>2019-02-11 09:58:51.400</td>
          <td>AOI-52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>SecurityEvent</td>
          <td>/subscriptions/40dcc8bf-0478-4f3b-b275-ed0a94f2c013/resourcegroups/asihuntomsworkspacerg/provide...</td>
          <td>{'Dummy': '-', 'TargetUserName': 'abai$', 'TargetDomainName': 'MSTICAlertsWin1', 'TargetSid': 'S...</td>
        </tr>
        <tr>
          <th>51</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-11 09:58:50.183</td>
          <td>OpsManager</td>
          <td>MSTICAlertsWin1\MSTICAdmin</td>
          <td>User</td>
          <td>MSTICAlertsWin1</td>
          <td>Microsoft-Windows-Security-Auditing</td>
          <td>Security</td>
          <td>13824</td>
          <td>8</td>
          <td>&lt;EventData xmlns="http://schemas.microsoft.com/win/2004/08/events/event"&gt;\r\n  &lt;Data Name="Targe...</td>
          <td>4724</td>
          <td>4724 - An attempt was made to reset an account's password.</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>...</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>263a788b-6526-4cdc-8ed9-d79402fe4aa0</td>
          <td>66e7e96a-d33d-4eb7-bc89-f4e654d74009</td>
          <td>00000000-0000-0000-0000-000000000001</td>
          <td>2019-02-11 09:58:51.400</td>
          <td>AOI-52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>SecurityEvent</td>
          <td>/subscriptions/40dcc8bf-0478-4f3b-b275-ed0a94f2c013/resourcegroups/asihuntomsworkspacerg/provide...</td>
          <td>{'TargetUserName': 'abai$', 'TargetDomainName': 'MSTICAlertsWin1', 'TargetSid': 'S-1-5-21-996632...</td>
        </tr>
      </tbody>
    </table>
    <p>5 rows × 226 columns</p>
    </div>



.. code:: ipython3

    win_host_events.expand_events(event_ids=4728).head(5)



.. raw:: html

    <h3>Parsing eventdata into columns</h3>



.. raw:: html

    This may take some time to complete for large numbers of events.<br>Since event types have different schema, some of the columns will not be populated for certain Event IDs and will show as `NaN`.



.. raw:: html

    <p style=''>Parsing event data...</p>




.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }

        .dataframe tbody tr th {
            vertical-align: top;
        }

        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>TenantId</th>
          <th>TimeGenerated</th>
          <th>SourceSystem</th>
          <th>Account</th>
          <th>AccountType</th>
          <th>Computer</th>
          <th>EventSourceName</th>
          <th>Channel</th>
          <th>Task</th>
          <th>Level</th>
          <th>EventData</th>
          <th>EventID</th>
          <th>Activity</th>
          <th>MemberName</th>
          <th>MemberSid</th>
          <th>PrivilegeList</th>
          <th>SubjectAccount</th>
          <th>SubjectDomainName</th>
          <th>SubjectLogonId</th>
          <th>SubjectUserName</th>
          <th>SubjectUserSid</th>
          <th>TargetAccount</th>
          <th>TargetDomainName</th>
          <th>TargetSid</th>
          <th>TargetUserName</th>
          <th>SourceComputerId</th>
          <th>EventOriginId</th>
          <th>MG</th>
          <th>TimeCollected</th>
          <th>ManagementGroupName</th>
          <th>Type</th>
          <th>_ResourceId</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>47</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-11 09:58:50.173</td>
          <td>OpsManager</td>
          <td>MSTICAlertsWin1\MSTICAdmin</td>
          <td>User</td>
          <td>MSTICAlertsWin1</td>
          <td>Microsoft-Windows-Security-Auditing</td>
          <td>Security</td>
          <td>13826</td>
          <td>8</td>
          <td>&lt;EventData xmlns="http://schemas.microsoft.com/win/2004/08/events/event"&gt;\r\n  &lt;Data Name="Membe...</td>
          <td>4728</td>
          <td>4728 - A member was added to a security-enabled global group.</td>
          <td>-</td>
          <td>S-1-5-21-996632719-2361334927-4038480536-1118</td>
          <td>-</td>
          <td>MSTICAlertsWin1\MSTICAdmin</td>
          <td>MSTICAlertsWin1</td>
          <td>0xbd57571</td>
          <td>MSTICAdmin</td>
          <td>S-1-5-21-996632719-2361334927-4038480536-500</td>
          <td>MSTICAlertsWin1\None</td>
          <td>MSTICAlertsWin1</td>
          <td>S-1-5-21-996632719-2361334927-4038480536-513</td>
          <td>None</td>
          <td>263a788b-6526-4cdc-8ed9-d79402fe4aa0</td>
          <td>27df6071-1e81-4e24-934c-dc96667b83ab</td>
          <td>00000000-0000-0000-0000-000000000001</td>
          <td>2019-02-11 09:58:51.400</td>
          <td>AOI-52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>SecurityEvent</td>
          <td>/subscriptions/40dcc8bf-0478-4f3b-b275-ed0a94f2c013/resourcegroups/asihuntomsworkspacerg/provide...</td>
        </tr>
        <tr>
          <th>58</th>
          <td>52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>2019-02-11 09:58:50.447</td>
          <td>OpsManager</td>
          <td>MSTICAlertsWin1\MSTICAdmin</td>
          <td>User</td>
          <td>MSTICAlertsWin1</td>
          <td>Microsoft-Windows-Security-Auditing</td>
          <td>Security</td>
          <td>13826</td>
          <td>8</td>
          <td>&lt;EventData xmlns="http://schemas.microsoft.com/win/2004/08/events/event"&gt;\r\n  &lt;Data Name="Membe...</td>
          <td>4728</td>
          <td>4728 - A member was added to a security-enabled global group.</td>
          <td>-</td>
          <td>S-1-5-21-996632719-2361334927-4038480536-1119</td>
          <td>-</td>
          <td>MSTICAlertsWin1\MSTICAdmin</td>
          <td>MSTICAlertsWin1</td>
          <td>0xbd57571</td>
          <td>MSTICAdmin</td>
          <td>S-1-5-21-996632719-2361334927-4038480536-500</td>
          <td>MSTICAlertsWin1\None</td>
          <td>MSTICAlertsWin1</td>
          <td>S-1-5-21-996632719-2361334927-4038480536-513</td>
          <td>None</td>
          <td>263a788b-6526-4cdc-8ed9-d79402fe4aa0</td>
          <td>73b0fe4e-9886-43ab-afa6-b43eb7434402</td>
          <td>00000000-0000-0000-0000-000000000001</td>
          <td>2019-02-11 09:58:51.400</td>
          <td>AOI-52b1ab41-869e-4138-9e40-2a4457f09bf0</td>
          <td>SecurityEvent</td>
          <td>/subscriptions/40dcc8bf-0478-4f3b-b275-ed0a94f2c013/resourcegroups/asihuntomsworkspacerg/provide...</td>
        </tr>
      </tbody>
    </table>
    </div>



--------------

Anatomy of a Notebooklet
========================

Three sections:
===============

-  Results class - what is it going to return
-  Notebooklet class - ``run()`` defines what the notebooklet does
-  Code - series of functions that do the actual work

.. code:: ipython3

    nb.nblts.azsent.host.WinHostEvents.import_cell()

.. code:: ipython3

    # -------------------------------------------------------------------------
    # Copyright (c) Microsoft Corporation. All rights reserved.
    # Licensed under the MIT License. See License.txt in the project root for
    # license information.
    # --------------------------------------------------------------------------
    """Notebooklet for Windows Security Events."""
    import pkgutil
    import os
    from typing import Any, Optional, Iterable, Union, Dict
    from defusedxml import ElementTree
    from defusedxml.ElementTree import ParseError

    import attr
    from bokeh.plotting.figure import Figure
    from bokeh.models import LayoutDOM
    from IPython.display import display
    import numpy as np
    import pandas as pd
    from msticpy.nbtools import nbdisplay

    from msticnb.common import (
        TimeSpan,
        MsticnbMissingParameterError,
        nb_data_wait,
        set_text,
        nb_markdown,
    )
    from msticnb.notebooklet import Notebooklet, NotebookletResult, NBMetaData
    from msticnb. import nb_metadata

    from msticnb._version import VERSION

    __version__ = VERSION
    __author__ = "Ian Hellen"


    _CLS_METADATA: NBMetaData
    _CELL_DOCS: Dict[str, Any]
    _CLS_METADATA, _CELL_DOCS = nb_metadata.read_mod_metadata(__file__, __name__)


    # pylint: disable=too-few-public-methods
    @attr.s(auto_attribs=True)
    class WinHostEventsResult(NotebookletResult):
        """
        Windows Host Security Events Results.

        Attributes
        ----------
        all_events : pd.DataFrame
            DataFrame of all raw events retrieved.
        event_pivot : pd.DataFrame
            DataFrame that is a pivot table of event ID
            vs. Account
        account_events : pd.DataFrame
            DataFrame containing a subset of account management
            events such as account and group modification.
        acct_pivot : pd.DataFrame
            DataFrame that is a pivot table of event ID
            vs. Account of account management events
        account_timeline : Union[Figure, LayoutDOM]
            Bokeh plot figure or Layout showing the account events on an
            interactive timeline.
        expanded_events : pd.DataFrame
            If `expand_events` option is specified, this will contain
            the parsed/expanded EventData as individual columns.

        """

        description: str = "Windows Host Security Events"
        all_events: pd.DataFrame = None
        event_pivot: pd.DataFrame = None
        account_events: pd.DataFrame = None
        account_pivot: pd.DataFrame = None
        account_timeline: Union[Figure, LayoutDOM] = None
        expanded_events: pd.DataFrame = None


    class WinHostEvents(Notebooklet):
        """
        Windows host Security Events Notebooklet class.

        Queries and displays Windows Security Events including:

        - All security events summary
        - Extracting and displaying account management events
        - Account management event timeline
        - Optionally parsing packed event data into DataFrame columns

        Process (4688) and Account Logon (4624, 4625) are not included
        in the event types processed by this module.

        """

        metadata = _CLS_METADATA
        __doc__ = nb_metadata.update_class_doc(__doc__, metadata)
        _cell_docs = _CELL_DOCS

        @set_text(docs=_CELL_DOCS, key="run")
        def run(
            self,
            value: Any = None,
            data: Optional[pd.DataFrame] = None,
            timespan: Optional[TimeSpan] = None,
            options: Optional[Iterable[str]] = None,
            **kwargs,
        ) -> WinHostEventsResult:
            """
            Return Windows Security Event summary.

            Parameters
            ----------
            value : str
                Host name
            data : Optional[pd.DataFrame], optional
                Not used, by default None
            timespan : TimeSpan
                Timespan over which operations such as queries will be
                performed, by default None.
                This can be a TimeStamp object or another object that
                has valid `start`, `end`, or `period` attributes.
            options : Optional[Iterable[str]], optional
                List of options to use, by default None.
                A value of None means use default options.
                Options prefixed with "+" will be added to the default options.
                To see the list of available options type `help(cls)` where
                "cls" is the notebooklet class or an instance of this class.

            Other Parameters
            ----------------
            start : Union[datetime, datelike-string]
                Alternative to specifying timespan parameter.
            end : Union[datetime, datelike-string]
                Alternative to specifying timespan parameter.

            Returns
            -------
            HostSummaryResult
                Result object with attributes for each result type.

            Raises
            ------
            MsticnbMissingParameterError
                If required parameters are missing

            """
            super().run(
                value=value, data=data, timespan=timespan, options=options, **kwargs
            )

            if not value:
                raise MsticnbMissingParameterError("value")
            if not timespan:
                raise MsticnbMissingParameterError("timespan.")

            result = WinHostEventsResult()
            result.description = self.metadata.description
            result.timespan = timespan

            all_events_df, event_pivot_df = _get_win_security_events(
                self.query_provider, host_name=value, timespan=self.timespan
            )
            result.all_events = all_events_df
            result.event_pivot = event_pivot_df

            if "event_pivot" in self.options:
                _display_event_pivot(event_pivot=event_pivot_df)

            if "acct_events" in self.options:
                result.account_events = _extract_acct_mgmt_events(event_data=all_events_df)
                result.account_pivot = _create_acct_event_pivot(
                    account_event_data=result.account_events
                )
                if result.account_pivot is not None:
                    _display_acct_event_pivot(event_pivot_df=result.account_pivot)
                    result.account_timeline = _display_acct_mgmt_timeline(
                        acct_event_data=result.account_events
                    )

            if "expand_events" in self.options:
                result.expanded_events = _parse_eventdata(all_events_df)

            nb_markdown("To unpack eventdata from selected events use expand_events()")
            self._last_result = result  # pylint: disable=attribute-defined-outside-init
            return self._last_result

        def expand_events(
            self, event_ids: Optional[Union[int, Iterable[int]]] = None
        ) -> pd.DataFrame:
            """
            Expand `EventData` for `event_ids` into separate columns.

            Parameters
            ----------
            event_ids : Optional[Union[int, Iterable[int]]], optional
                Single or interable of event IDs (ints).
                If no event_ids are specified all events will be expanded.

            Returns
            -------
            pd.DataFrame
                Results with expanded columns.

            Notes
            -----
            For a specific event ID you can expand the EventProperties values
            into their own columns using this function.
            You can do this for the whole data set but it will time-consuming
            and result in a lot of sparse columns in the output data frame.

            """
            if (
                not self._last_result or self._last_result.all_events is None
            ):  # type: ignore
                print(
                    "Please use 'run()' to fetch the data before using this method.",
                    "\nThen call 'expand_events()'",
                )
                return None
            return _parse_eventdata(
                event_data=self._last_result.all_events,  # type: ignore
                event_ids=event_ids,
            )


    # %%
    # Get Windows Security Events
    def _get_win_security_events(qry_prov, host_name, timespan):
        nb_data_wait("SecurityEvent")

        all_events_df = qry_prov.WindowsSecurity.list_host_events(
            timespan,
            host_name=host_name,
            add_query_items="| where EventID != 4688 and EventID != 4624",
        )

        # Create a pivot of Event vs. Account
        win_events_acc = all_events_df[["Account", "Activity", "TimeGenerated"]].copy()
        win_events_acc = win_events_acc.replace("-\\-", "No Account").replace(
            {"Account": ""}, value="No Account"
        )
        win_events_acc["Account"] = win_events_acc.apply(
            lambda x: x.Account.split("\\")[-1], axis=1
        )
        event_pivot_df = (
            pd.pivot_table(
                win_events_acc,
                values="TimeGenerated",
                index=["Activity"],
                columns=["Account"],
                aggfunc="count",
            )
            .fillna(0)
            .reset_index()
        )
        return all_events_df, event_pivot_df


    @set_text(docs=_CELL_DOCS, key="display_event_pivot")
    def _display_event_pivot(event_pivot):
        display(
            event_pivot.style.applymap(lambda x: "color: white" if x == 0 else "")
            .applymap(
                lambda x: "background-color: lightblue"
                if not isinstance(x, str) and x > 0
                else ""
            )
            .set_properties(subset=["Activity"], **{"width": "400px", "text-align": "left"})
            .highlight_max(axis=1)
            .hide_index()
        )


    # %%
    # Extract event details from events
    SCHEMA = "http://schemas.microsoft.com/win/2004/08/events/event"


    def _parse_event_data_row(row):
        try:
            xdoc = ElementTree.fromstring(row.EventData)
            col_dict = {
                elem.attrib["Name"]: elem.text for elem in xdoc.findall(f"{{{SCHEMA}}}Data")
            }
            reassigned = set()
            for key, val in col_dict.items():
                if key in row and not row[key]:
                    row[key] = val
                    reassigned.add(key)
            if reassigned:
                for key in reassigned:
                    col_dict.pop(key)
            return col_dict
        except (ParseError, TypeError):
            return None


    def _expand_event_properties(input_df):
        # For a specific event ID you can explode the EventProperties values
        # into their own columns using this function. You can do this for
        # the whole data set but it will result
        # in a lot of sparse columns in the output data frame.
        exp_df = input_df.apply(lambda x: pd.Series(x.EventProperties), axis=1)
        return (
            exp_df.drop(set(input_df.columns).intersection(exp_df.columns), axis=1)
            .merge(
                input_df.drop("EventProperties", axis=1),
                how="inner",
                left_index=True,
                right_index=True,
            )
            .replace("", np.nan)  # these 3 lines get rid of blank columns
            .dropna(axis=1, how="all")
            .fillna("")
        )


    @set_text(docs=_CELL_DOCS, key="parse_eventdata")
    def _parse_eventdata(event_data, event_ids: Optional[Union[int, Iterable[int]]] = None):
        if event_ids:
            if isinstance(event_ids, int):
                event_ids = [event_ids]
            src_event_data = event_data[event_data["EventID"].isin(event_ids)].copy()
        else:
            src_event_data = event_data.copy()

        # Parse event properties into a dictionary
        nb_markdown("Parsing event datamsticnb.")
        src_event_data["EventProperties"] = src_event_data.apply(
            _parse_event_data_row, axis=1
        )
        return _expand_event_properties(src_event_data)


    # %%
    # Account management events
    def _extract_acct_mgmt_events(event_data):
        # Get a full list of Windows Security Events

        w_evt = pkgutil.get_data("msticpy", f"resources{os.sep}WinSecurityEvent.json")
        win_event_df = pd.read_json(w_evt)

        # Create criteria for events that we're interested in
        acct_sel = win_event_df["subcategory"] == "User Account Management"
        group_sel = win_event_df["subcategory"] == "Security Group Management"
        schtask_sel = (win_event_df["subcategory"] == "Other Object Access Events") & (
            win_event_df["description"].str.contains("scheduled task")
        )

        event_list = win_event_df[acct_sel | group_sel | schtask_sel]["event_id"].to_list()
        # Add Service install event
        event_list.append(7045)
        return event_data[event_data["EventID"].isin(event_list)]


    def _create_acct_event_pivot(account_event_data):
        # Create a pivot of Event vs. Account
        if account_event_data.empty:
            return None
        win_events_acc = account_event_data[["Account", "Activity", "TimeGenerated"]].copy()
        win_events_acc = win_events_acc.replace("-\\-", "No Account").replace(
            {"Account": ""}, value="No Account"
        )
        win_events_acc["Account"] = win_events_acc.apply(
            lambda x: x.Account.split("\\")[-1], axis=1
        )

        event_pivot_df = (
            pd.pivot_table(
                win_events_acc,
                values="TimeGenerated",
                index=["Activity"],
                columns=["Account"],
                aggfunc="count",
            )
            .fillna(0)
            .reset_index()
        )
        return event_pivot_df


    @set_text(docs=_CELL_DOCS, key="display_acct_event_pivot")
    def _display_acct_event_pivot(event_pivot_df):
        display(
            event_pivot_df.style.applymap(lambda x: "color: white" if x == 0 else "")
            .applymap(
                lambda x: "background-color: lightblue"
                if not isinstance(x, str) and x > 0
                else ""
            )
            .set_properties(subset=["Activity"], **{"width": "400px", "text-align": "left"})
            .highlight_max(axis=1)
            .hide_index()
        )


    @set_text(docs=_CELL_DOCS, key="display_acct_mgmt_timeline")
    def _display_acct_mgmt_timeline(acct_event_data):
        # Plot events on a timeline
        return nbdisplay.display_timeline(
            data=acct_event_data,
            group_by="EventID",
            source_columns=["Activity", "Account"],
            legend="right",
        )


--------------

More Info
=========

msticpy
-------

-  Documentation - https://msticpy.readthedocs.io
-  GitHub - https://github.com/microsoft/msticpy
-  PyPI - https://pypi.org/project/msticpy/

msticnb - Notebooklets
----------------------

-  GitHub - https://github.com/microsoft/msticnb

Notebooks
---------

-  Azure-Sentinel-Notebooks -
   https://github.com/Azure/Azure-Sentinel-Notebooks
-  Binder-able demo -
   https://github.com/Azure/Azure-Sentinel-Notebooks/tree/master/nbdemo

– ## Network Flow Notebooklet

.. code:: ipython3

    nb.init(
        "LocalData",
        LocalData_data_paths=["e:\\src\\msticnb\\msticnb\\tests\\testdata"],
        LocalData_query_paths=["e:\\src\\msticnb\\msticnb\\tests\\testdata"],
    )
    flow_summary = nb.nblts.azsent.network.NetworkFlowSummary()
    flow_result = flow_summary.run(value="MSTICAlertsWin1", timespan=TimeSpan(time_selector=time_span))


.. parsed-literal::

    e:\src\microsoft\msticpy\msticpy\data\query_store.py:172: UserWarning: e:\src\msticnb\msticnb\tests\testdata\msticpyconfig-test.yaml is not a valid query definition file.
      warnings.warn(f"{file_path} is not a valid query definition file.")


.. parsed-literal::

    Warning: ('No AzureCLI configuration found in configuration settings.',)
    Please wait. Loading Kqlmagic extension...



.. parsed-literal::

    <IPython.core.display.Javascript object>



.. parsed-literal::

    <IPython.core.display.Javascript object>



.. parsed-literal::

    <IPython.core.display.Javascript object>



.. raw:: html

    <!DOCTYPE html>
                        <html><body>

                        <!-- h1 id="user_code_p"><b>ECBUBUG2M</b><br></h1-->

                        <input  id="kql_MagicCodeAuthInput" type="text" readonly style="font-weight: bold; border: none;" size = '9' value='ECBUBUG2M'>

                        <button id='kql_MagicCodeAuth_button', onclick="this.style.visibility='hidden';kql_MagicCodeAuthFunction()">Copy code to clipboard and authenticate</button>

                        <script>
                        var kql_MagicUserCodeAuthWindow = null
                        function kql_MagicCodeAuthFunction() {
                            /* Get the text field */
                            var copyText = document.getElementById("kql_MagicCodeAuthInput");

                            /* Select the text field */
                            copyText.select();

                            /* Copy the text inside the text field */
                            document.execCommand("copy");

                            /* Alert the copied text */
                            // alert("Copied the text: " + copyText.value);

                            var w = screen.width / 2;
                            var h = screen.height / 2;
                            params = 'width='+w+',height='+h
                            kql_MagicUserCodeAuthWindow = window.open('https://microsoft.com/devicelogin', 'kql_MagicUserCodeAuthWindow', params);

                            // TODO: save selected cell index, so that the clear will be done on the lince cell
                        }
                        </script>

                        </body></html>



.. raw:: html

    <!DOCTYPE html>
                        <html><body><script>

                            // close authentication window
                            if (kql_MagicUserCodeAuthWindow && kql_MagicUserCodeAuthWindow.opener != null && !kql_MagicUserCodeAuthWindow.closed) {
                                kql_MagicUserCodeAuthWindow.close()
                            }
                            // TODO: make sure, you clear the right cell. BTW, not sure it is a must to do any clearing

                            // clear output cell
                            Jupyter.notebook.clear_output(Jupyter.notebook.get_selected_index())

                            // TODO: if in run all mode, move to last cell, otherwise move to next cell
                            // move to next cell

                        </script></body></html>



.. raw:: html

    <html>
            <head>

            </head>
            <body>
            <div><p style='padding: 10px; color: #b94a48; background-color: #f2dede; border-color: #eed3d7'>{&quot;error&quot;:{&quot;message&quot;:&quot;The&nbsp;provided&nbsp;credentials&nbsp;have&nbsp;insufficient&nbsp;access&nbsp;to&nbsp;perform&nbsp;the&nbsp;requested&nbsp;operation&quot;,&quot;code&quot;:&quot;InsufficientAccessError&quot;}}</p></div>
            </body>
            </html>



.. raw:: html

    <html>
            <head>

            </head>
            <body>
            <div><p style='padding: 10px; color: #b94a48; background-color: #f2dede; border-color: #eed3d7'>{&quot;error&quot;:{&quot;message&quot;:&quot;The&nbsp;provided&nbsp;credentials&nbsp;have&nbsp;insufficient&nbsp;access&nbsp;to&nbsp;perform&nbsp;the&nbsp;requested&nbsp;operation&quot;,&quot;code&quot;:&quot;InsufficientAccessError&quot;}}</p></div>
            </body>
            </html>


.. parsed-literal::

    Using Open PageRank. See https://www.domcop.com/openpagerank/what-is-openpagerank
    Loaded providers: LocalData, geolitelookup, tilookup



.. raw:: html

    <h1>Host Network Summary</h1>



.. raw:: html

    This shows a summary of network flows for this endpoint.<br>Data and plots are stored in the result class returned by this function.


.. parsed-literal::

    Getting data from AzureNetworkAnalytics...



.. raw:: html

    <h2>Timeline of network flows by protocol type.</h2>



.. raw:: html


    <div class="bk-root">
        <a href="https://bokeh.org" target="_blank" class="bk-logo bk-logo-small bk-logo-notebook"></a>
        <span id="2063">Loading BokehJS ...</span>
    </div>





.. raw:: html







    <div class="bk-root" id="02aa45b8-5e34-401c-b3c4-dfebda7ce7ab" data-root-id="2162"></div>






.. raw:: html

    <h2>Timeline of network flows by direction.</h2>



.. raw:: html

    I = inbound, O = outbound.



.. raw:: html


    <div class="bk-root">
        <a href="https://bokeh.org" target="_blank" class="bk-logo bk-logo-small bk-logo-notebook"></a>
        <span id="2435">Loading BokehJS ...</span>
    </div>





.. raw:: html







    <div class="bk-root" id="40298c83-0f9d-480f-8afd-1a6c88491c05" data-root-id="2510"></div>






.. raw:: html

    <h2>Timeline of network flows quantity.</h2>



.. raw:: html

    Each protocol is plotted as a separate colored series. The vertical axis indicates the number for flows recorded for that time slot.



.. raw:: html


    <div class="bk-root">
        <a href="https://bokeh.org" target="_blank" class="bk-logo bk-logo-small bk-logo-notebook"></a>
        <span id="2751">Loading BokehJS ...</span>
    </div>





.. raw:: html







    <div class="bk-root" id="102b4974-eec5-45ca-899f-b14238bd58f6" data-root-id="2977"></div>






.. raw:: html

    <h2>Flow Index.</h2>



.. raw:: html

    List of flows grouped by source, dest, protocol and direction.



.. raw:: html

    <style  type="text/css" >
        #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row0_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 3.6%, transparent 3.6%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row1_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 28.6%, transparent 28.6%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row2_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 3.6%, transparent 3.6%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row3_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 53.6%, transparent 53.6%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row4_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 100.0%, transparent 100.0%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row5_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 14.3%, transparent 14.3%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row6_col4 {
                width:  10em;
                 height:  80%;
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row7_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 14.3%, transparent 14.3%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row8_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 3.6%, transparent 3.6%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row9_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 28.6%, transparent 28.6%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row10_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 3.6%, transparent 3.6%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row11_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 21.4%, transparent 21.4%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row12_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 3.6%, transparent 3.6%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row13_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 21.4%, transparent 21.4%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row14_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 21.4%, transparent 21.4%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row15_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 35.7%, transparent 35.7%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row16_col4 {
                width:  10em;
                 height:  80%;
                background:  linear-gradient(90deg,#d65f5f 14.3%, transparent 14.3%);
            }    #T_89b3e1b8_a778_11ea_853b_0002723f5ca7row17_col4 {
                width:  10em;
                 height:  80%;
            }</style><table id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7" ><thead>    <tr>        <th class="blank level0" ></th>        <th class="col_heading level0 col0" >source</th>        <th class="col_heading level0 col1" >dest</th>        <th class="col_heading level0 col2" >L7Protocol</th>        <th class="col_heading level0 col3" >FlowDirection</th>        <th class="col_heading level0 col4" >TotalAllowedFlows</th>    </tr></thead><tbody>
                    <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row0" class="row_heading level0 row0" >0</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row0_col0" class="data row0 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row0_col1" class="data row0 col1" >13.107.4.50</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row0_col2" class="data row0 col2" >http</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row0_col3" class="data row0 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row0_col4" class="data row0 col4" >2</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row1" class="row_heading level0 row1" >1</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row1_col0" class="data row1 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row1_col1" class="data row1 col1" >13.65.107.32</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row1_col2" class="data row1 col2" >https</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row1_col3" class="data row1 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row1_col4" class="data row1 col4" >9</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row2" class="row_heading level0 row2" >2</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row2_col0" class="data row2 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row2_col1" class="data row2 col1" >13.67.143.117</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row2_col2" class="data row2 col2" >https</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row2_col3" class="data row2 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row2_col4" class="data row2 col4" >2</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row3" class="row_heading level0 row3" >3</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row3_col0" class="data row3 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row3_col1" class="data row3 col1" >13.71.172.128</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row3_col2" class="data row3 col2" >https</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row3_col3" class="data row3 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row3_col4" class="data row3 col4" >16</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row4" class="row_heading level0 row4" >4</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row4_col0" class="data row4 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row4_col1" class="data row4 col1" >13.71.172.130</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row4_col2" class="data row4 col2" >https</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row4_col3" class="data row4 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row4_col4" class="data row4 col4" >29</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row5" class="row_heading level0 row5" >5</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row5_col0" class="data row5 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row5_col1" class="data row5 col1" >134.170.58.123</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row5_col2" class="data row5 col2" >https</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row5_col3" class="data row5 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row5_col4" class="data row5 col4" >5</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row6" class="row_heading level0 row6" >6</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row6_col0" class="data row6 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row6_col1" class="data row6 col1" >20.38.98.100</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row6_col2" class="data row6 col2" >https</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row6_col3" class="data row6 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row6_col4" class="data row6 col4" >1</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row7" class="row_heading level0 row7" >7</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row7_col0" class="data row7 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row7_col1" class="data row7 col1" >204.79.197.200</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row7_col2" class="data row7 col2" >https</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row7_col3" class="data row7 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row7_col4" class="data row7 col4" >5</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row8" class="row_heading level0 row8" >8</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row8_col0" class="data row8 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row8_col1" class="data row8 col1" >23.48.36.47</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row8_col2" class="data row8 col2" >http</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row8_col3" class="data row8 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row8_col4" class="data row8 col4" >2</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row9" class="row_heading level0 row9" >9</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row9_col0" class="data row9 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row9_col1" class="data row9 col1" >40.124.45.19</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row9_col2" class="data row9 col2" >https</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row9_col3" class="data row9 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row9_col4" class="data row9 col4" >9</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row10" class="row_heading level0 row10" >10</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row10_col0" class="data row10 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row10_col1" class="data row10 col1" >40.77.226.250</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row10_col2" class="data row10 col2" >https</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row10_col3" class="data row10 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row10_col4" class="data row10 col4" >2</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row11" class="row_heading level0 row11" >11</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row11_col0" class="data row11 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row11_col1" class="data row11 col1" >40.77.228.69</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row11_col2" class="data row11 col2" >https</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row11_col3" class="data row11 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row11_col4" class="data row11 col4" >7</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row12" class="row_heading level0 row12" >12</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row12_col0" class="data row12 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row12_col1" class="data row12 col1" >40.77.232.95</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row12_col2" class="data row12 col2" >https</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row12_col3" class="data row12 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row12_col4" class="data row12 col4" >2</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row13" class="row_heading level0 row13" >13</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row13_col0" class="data row13 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row13_col1" class="data row13 col1" >52.168.138.145</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row13_col2" class="data row13 col2" >ntp</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row13_col3" class="data row13 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row13_col4" class="data row13 col4" >7</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row14" class="row_heading level0 row14" >14</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row14_col0" class="data row14 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row14_col1" class="data row14 col1" >65.55.44.108</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row14_col2" class="data row14 col2" >https</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row14_col3" class="data row14 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row14_col4" class="data row14 col4" >7</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row15" class="row_heading level0 row15" >15</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row15_col0" class="data row15 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row15_col1" class="data row15 col1" >65.55.44.109</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row15_col2" class="data row15 col2" >https</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row15_col3" class="data row15 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row15_col4" class="data row15 col4" >11</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row16" class="row_heading level0 row16" >16</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row16_col0" class="data row16 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row16_col1" class="data row16 col1" >72.21.81.200</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row16_col2" class="data row16 col2" >https</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row16_col3" class="data row16 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row16_col4" class="data row16 col4" >5</td>
                </tr>
                <tr>
                            <th id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7level0_row17" class="row_heading level0 row17" >17</th>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row17_col0" class="data row17 col0" >10.0.3.5</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row17_col1" class="data row17 col1" >72.21.91.29</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row17_col2" class="data row17 col2" >http</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row17_col3" class="data row17 col3" >O</td>
                            <td id="T_89b3e1b8_a778_11ea_853b_0002723f5ca7row17_col4" class="data row17 col4" >1</td>
                </tr>
        </tbody></table>



.. raw:: html

    <h2>Flow Summary with ASN details.</h2>



.. raw:: html

    Gets the ASN details from WhoIs.<br>The data shows flows grouped by source and destination ASNs. All protocol types and all source IP addresses are grouped into lists for each ASN.



.. raw:: html

    <p style=''>Found 19 unique IP Addresses.</p>


.. parsed-literal::

    Getting data from Whois...
    ..................


.. raw:: html

    <div>
    <style scoped>
        .dataframe tbody tr th:only-of-type {
            vertical-align: middle;
        }

        .dataframe tbody tr th {
            vertical-align: top;
        }

        .dataframe thead th {
            text-align: right;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>DestASN</th>
          <th>SourceASN</th>
          <th>TotalAllowedFlows</th>
          <th>L7Protocols</th>
          <th>source_ips</th>
          <th>dest_ips</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0</th>
          <td>AKAMAI-ASN1, EU</td>
          <td>No ASN Information for IP type: Private</td>
          <td>2.0</td>
          <td>[http]</td>
          <td>[10.0.3.5]</td>
          <td>[23.48.36.47]</td>
        </tr>
        <tr>
          <th>1</th>
          <td>EDGECAST, US</td>
          <td>No ASN Information for IP type: Private</td>
          <td>6.0</td>
          <td>[https, http]</td>
          <td>[10.0.3.5]</td>
          <td>[72.21.81.200, 72.21.91.29]</td>
        </tr>
        <tr>
          <th>2</th>
          <td>MICROSOFT-CORP-MSN-AS-BLOCK, US</td>
          <td>No ASN Information for IP type: Private</td>
          <td>114.0</td>
          <td>[http, https, ntp]</td>
          <td>[10.0.3.5]</td>
          <td>[13.107.4.50, 13.65.107.32, 13.67.143.117, 13.71.172.128, 13.71.172.130, 134.170.58.123, 20.38.9...</td>
        </tr>
      </tbody>
    </table>
    </div>



.. raw:: html

    <p style=''>Select ASNs to examine using select_asns()</p>



.. raw:: html

    <p style=''>Lookup threat intel for IPs from selected ASNs using lookup_ti_for_asn_ips()</p>



.. raw:: html

    <p style=''>Display Geolocation of threats with show_selected_asn_map()</p>



.. raw:: html

    <p style=''>For usage type 'help(NetworkFlowSummary.function_name)'</p>


.. code:: ipython3

    flow_summary.select_asns()



.. raw:: html

    <h2>Select the ASNs to process.</h2>



.. raw:: html

    Choose any unusual looking ASNs that you want to examine.<br>The remote IPs from each selected ASN will be sent to your selected Threat Intelligence providers to check if there are indications of malicious activity associated with these IPs.<br>By default, the most infrequently accessed ASNs are selected.


.. parsed-literal::

    None does not appear to be an IPv4 or IPv6 address



.. parsed-literal::

    VBox(children=(Text(value='', description='Filter:', style=DescriptionStyle(description_width='initial')), HBo…



.. parsed-literal::

    <msticpy.nbtools.nbwidgets.SelectSubset at 0x1cca2547860>


.. code:: ipython3

    flow_summary.lookup_ti_for_asn_ips()
    flow_summary.show_selected_asn_map()



.. raw:: html

    <p style=''>2 unique IPs in selected ASNs</p>



.. raw:: html

    <h2>TI Lookup for IP Addresses in selected ASNs.</h2>



.. raw:: html

    The remote IPs from each selected ASN are are searched for your selected Threat Intelligence providers. Check the results to see if there are indications of malicious activity associated with these IPs.


.. parsed-literal::

    Getting data from Threat Intelligence...



.. parsed-literal::

    <IPython.core.display.Javascript object>



.. raw:: html

    <html>
            <head>

            </head>
            <body>
            <div><p style='padding: 10px; color: #b94a48; background-color: #f2dede; border-color: #eed3d7'>{&quot;error&quot;:{&quot;message&quot;:&quot;The&nbsp;provided&nbsp;credentials&nbsp;have&nbsp;insufficient&nbsp;access&nbsp;to&nbsp;perform&nbsp;the&nbsp;requested&nbsp;operation&quot;,&quot;code&quot;:&quot;InsufficientAccessError&quot;}}</p></div>
            </body>
            </html>



.. raw:: html

    <html>
            <head>

            </head>
            <body>
            <div><p style='padding: 10px; color: #b94a48; background-color: #f2dede; border-color: #eed3d7'>{&quot;error&quot;:{&quot;message&quot;:&quot;The&nbsp;provided&nbsp;credentials&nbsp;have&nbsp;insufficient&nbsp;access&nbsp;to&nbsp;perform&nbsp;the&nbsp;requested&nbsp;operation&quot;,&quot;code&quot;:&quot;InsufficientAccessError&quot;}}</p></div>
            </body>
            </html>



.. parsed-literal::

    <IPython.core.display.Javascript object>



.. raw:: html

    <html>
            <head>

            </head>
            <body>
            <div><p style='padding: 10px; color: #3a87ad; background-color: #d9edf7; border-color: #bce9f1'>&nbsp;*&nbsp;ab86c959-1ba3-495c-a00d-ced30d8825d3@loganalytics</p></div>
            </body>
            </html>



.. raw:: html

    <html>
            <head>

            </head>
            <body>
            <div><p style='padding: 10px; color: #b94a48; background-color: #f2dede; border-color: #eed3d7'>{&quot;error&quot;:{&quot;message&quot;:&quot;The&nbsp;provided&nbsp;credentials&nbsp;have&nbsp;insufficient&nbsp;access&nbsp;to&nbsp;perform&nbsp;the&nbsp;requested&nbsp;operation&quot;,&quot;code&quot;:&quot;InsufficientAccessError&quot;}}</p></div>
            </body>
            </html>


.. parsed-literal::

    Warning - query did not complete successfully.
    Unknown response from provider: None



.. raw:: html

    <p style=''>10 TI results received.</p>



.. raw:: html

    <p style=''>6 positive results found.</p>


::


    ---------------------------------------------------------------------------

    AttributeError                            Traceback (most recent call last)

    <ipython-input-26-b4e60ddf222d> in <module>
    ----> 1 flow_summary.lookup_ti_for_asn_ips()
          2 flow_summary.show_selected_asn_map()


    e:\src\msticnb\msticnb\nb\azsent\network\network_flow_summary.py in lookup_ti_for_asn_ips(self)
        294             flows_df=self._last_result,
        295             selected_ips=selected_ips,
    --> 296             ti_lookup=self.data_providers["tilookup"],
        297         )
        298         self._last_result.ti_results = ti_results


    e:\src\msticnb\msticnb\common.py in print_text(*args, **kwargs)
        347                         display(HTML(f"<br><b>{sec_title}</b><br>"))
        348                         display(HTML(content.replace("\n", "<br>")))
    --> 349             return func(*args, **kwargs)
        350
        351         return print_text


    e:\src\msticnb\msticnb\nb\azsent\network\network_flow_summary.py in _lookup_ip_ti(flows_df, ti_lookup, selected_ips)
        606
        607     if not ti_results_pos.empty:
    --> 608         src_pos = flows_df.merge(ti_results_pos, left_on="source", right_on="Ioc")
        609         dest_pos = flows_df.merge(ti_results_pos, left_on="dest", right_on="Ioc")
        610         ti_ip_results = pd.concat([src_pos, dest_pos])


    AttributeError: 'NetworkFlowResult' object has no attribute 'merge'


.. code:: ipython3

    from msticnb.nb_metadata import NBMetaData
    newmd = eval(repr(nb.nblts.azsent.host.WinHostEvents.metadata))
    newmd == nb.nblts.azsent.host.WinHostEvents.metadata




.. parsed-literal::

    True



.. code:: ipython3

    nb.nblts.azsent.host.WinHostEvents.import_cell()


::


    ---------------------------------------------------------------------------

    AttributeError                            Traceback (most recent call last)

    <ipython-input-3-950eab3edc91> in <module>
    ----> 1 nb.nblts.azsent.host.WinHostEvents.import_cell()


    e:\src\msticnb\msticnb\notebooklet.py in import_cell(cls)
        520             if mod_text:
        521                 # replace relative references with absolute paths
    --> 522                 mod_text = cls._update_mod_for_import(mod_text)
        523                 shell = get_ipython()
        524                 shell.set_next_input(mod_text)


    e:\src\msticnb\msticnb\notebooklet.py in _update_mod_for_import(cls, mod_text)
        527     def _update_mod_for_import(cls, mod_text):
        528         mod_text = re.sub(r"\.{3,}", "msticnb.", mod_text)
    --> 529         metadata, docs = read_mod_metadata(cls.__file__, cls.__name__)
        530         metadata_repr = repr(metadata)
        531         metadata_repr = metadata_repr.replace("NBMetaData", "nb_metadata.NBMetaData")


    AttributeError: type object 'WinHostEvents' has no attribute '__file__'


.. code:: ipython3

    from msticnb.nb.azsent.host.host_summary import _CELL_DOCS

    str(_CELL_DOCS)

    metadata_repr = repr(nb.nblts.azsent.host.WinHostEvents.metadata)
    metadata_repr = metadata_repr.replace("NBMetaData", "nb_metadata.NBMetaData")

.. code:: ipython3

    from msticnb.nb.azsent.host import host_summary
    host_summary.__file__
    with open(host_summary.__file__, "r") as mod_file:
        mod_text = mod_file.read()

    repl_text = "_CLS_METADATA, _CELL_DOCS = nb_metadata.read_mod_metadata(__file__, __name__)"
    docs_repl = f"_CELL_DOCS = {str(_CELL_DOCS)}\n"
    docs_repl = f"{docs_repl}\n_CLS_METADATA = {metadata_repr}"
    print(mod_text.replace(repl_text, docs_repl)[1000:3000])


::


    ---------------------------------------------------------------------------

    NameError                                 Traceback (most recent call last)

    <ipython-input-4-3553fa654387> in <module>
          5
          6 repl_text = "_CLS_METADATA, _CELL_DOCS = nb_metadata.read_mod_metadata(__file__, __name__)"
    ----> 7 docs_repl = f"_CELL_DOCS = {str(_CELL_DOCS)}\n"
          8 docs_repl = f"{docs_repl}\n_CLS_METADATA = {metadata_repr}"
          9 print(mod_text.replace(repl_text, docs_repl)[1000:3000])


    NameError: name '_CELL_DOCS' is not defined


.. code:: ipython3

    nb.nblts.azsent.host.WinHostEvents.__module__




.. parsed-literal::

    'msticnb.nb.azsent.host.win_host_events'


