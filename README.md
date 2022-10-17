This sample demonstrates how to use [Vaex](https://vaex.readthedocs.io/en/latest/) to load a Parquet file and perform
multi-threaded calculations on a 42 million row dataset.

# Vaex Overview

The Vaex project provides a multi-threaded pandas-like `DataFrame`
that is designed to make very efficient use of available memory.
Unlike pandas, when a Vaex `DataFrame` is loaded from a binary file
(e.g. parquet, hdf5, arrow), the data from the file is not immediately
loaded into memory. Instead, a memory map is created and
required portions of the file are lazily loaded into memory as needed.

This design makes it possible for multiple processes
(e.g. multiple gunicorn workers serving a Dash app) to use Vaex to load
and process a large binary file without loading multiple copies of
the file into memory.  The operating system takes care of ensuring that
the same in-memory representation of the mapped file is shared
across processes.

## Application Architecture

**Data Pipeline**

When working with large datasets, we recommend that you do not commit these
files into your project directory. Uploading large files (>10MB) is not
supported very well by `git` and can make your project onerous to share among
peers and to host on git platforms.

Instead, we recommend one of these three options:

1. On deploy, download or generate the data and save the files to a folder
in the deployed application's container. Try to keep data-fetching code
in a separate file that can be run separately from your Dash application so that data-fetching doesn't impact
the start-up of your application and cause `gunicorn` start-up timeouts.
When working locally, you'll have a copy of this data on your filesystem as well.
Avoid committing this data into your project by adding the data folder to
`.gitignore`. You may download the file from any source like S3, a database,
or an API.
2. Alternatively, host your data on S3 and use Vaex's [S3 support](https://vaex.readthedocs.io/en/latest/api.html#vaex.open)
3. If your datafiles aren't available in S3, a database, or an API then we would
recommend mounting a local directory on your Dash Enterprise server and
uploading your data files to your server directly with a tool like `scp`.

This particular application uses Option 1. The `generate_data.py` script
generates a 1.3GB synthetic Parquet file and is run on deploy
(see `Procfile` & `launch.sh`). The parquet files are saved to the `runtime_data/`
directory which is ignored from `git` via `.gitignore`.

If you go with Option 1, then you would modify `generate_data.py` to fetch
or generate your own data for your application.

> **Note:** While Vaex can load csv files, memory mapping is not supported
in this case. This means that the entire csv file will be loaded
into memory when it is opened and each process that opens the same
csv file will get a separate copy in memory. This defeats the purpose of
Vaex. So, we recommend converting csv files to a binary format like `parquet`
before ingestion.

**Zero Downtime Deploys**

Since initialization can take a few minutes, we recommend configuring the
project's `CHECKS` file by uncommenting the lines and replacing `app-name`
with your application's app name.

Without a properly-configured `CHECKS` file, Dash Enterprise will start sending
traffic to your application 10 seconds after you deploy it, which may not be enough
time for the app to be ready to respond to requests. For more details on zero-downtime
deploys, see [App Health Checks](/Docs/dash-enterprise/checks).

> If you are using Dash Enterprise on Kubernetes, you would use `app.json`
> instead of `CHECKS`. See the Dash Enterprise on Kubernetes chapter for
> more detail.

## Running Locally

1. Install the Python dependencies
```
pip install -r requirements.txt
```
2. Generate mock data.

  This will take 5-15 minutes.
```
python generate_data.py
```
3. Run the application
```
python app.py
```

## RAPIDS vs Dask vs Vaex vs Databricks vs Postgres

This sample app demonstrates how to filter & aggregate large amounts of data that
don't fit in memory. There are several strategies to consider:
 - Pandas - Before you try a more advanced library, try keeping the data in
   memory and/or increasing the memory of your server. In Dash Enterprise on
   a single server, memory is shared across all apps. In Dash Enterprise for
   Kubernetes, memory is provisioned per-application. Try the `--preload` flag
   in `gunicorn` to prevent large dataframes from being duplicated across every worker.
 - Vaex ([sample app](/Docs/templates/vaex-sample)) - For binning, filtering, and
   aggregating Vaex is one of the fastest CPU-based DataFrame libraries out there.
   See this [3rd party performance comparison on a particular set of dataframe operations](https://towardsdatascience.com/beyond-pandas-spark-dask-vaex-and-other-big-data-technologies-battling-head-to-head-a453a1f8cc13).
   Vaex is relatively simple to set up and program since it doesn't run a separate
   cluster or process like Dask.
 - Dask ([sample app](/Docs/templates/dask-sample)) - Dask may be slower
   than Vaex for a certain set of operations, but it provides more than
   just DataFrames like ad-hoc parallelization with `dask.delayed` and
   other data structures like `arrays` and `bags`. Also, there is large
   ecosystem of tools that use Dask like XArray, Datashader, and XGBoost.
   From a development perspective, keeping data in a Dask cluster can provide
   a much faster development experience since the data does not need to be
   reloaded when you make changes to your application code.
 - RAPIDS ([sample app](/Docs/templates/rapids-sample)) - If you have licensed Dash
   Enterprise for Kubernetes, then providing a GPU node in your cluster and
   using RAPIDS will be one of the fastest ways to filter and aggregate a large
   amount of data in real time. Our sample apps use Dask to manage access to the
   GPU and so the advantages and tradeoffs related to Dask apply to RAPIDS as well.
 - Databricks (see [sample app with databricks-connect](/Docs/templates/databricks-connect)
   and [DatabricksDash library for building Dash apps within Databricks](/Docs/databricks-dash)) -
   If your organization has already licensed and is finding value with Databricks,
   then this could be a good approach for large datasets.
 - Postgres (see [sample app](/Docs/templates/celery-periodic-task-postgres)) - Databases
   are a tried and true method for querying, filtering, and aggregating data. In this workflow,
   you could either query an external database directly with SQL & SQLalchemy or
   [ibis](https://docs.ibis-project.org/) or you could write data into a Postgres database that
   is linked to your application with Pandas `df.to_sql`. Dash Enterprise on a single server
   enables you to create and link Postgres databases to your application.
