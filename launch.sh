#!/bin/bash

# Generate parquet dataset
python generate_data.py

# Launch app for deployment with gunicorn
gunicorn "app:server" --timeout 60 --workers 4


## FROM THE DASK EXAMPLE. INTEGRATE WITH ABOVE
#!/bin/bash
# Add this directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:`dirname "$(realpath $0)"`

# Set environment variable for Dask scheduler
export DASK_SCHEDULER_HOST=127.0.0.1
export DASK_SCHEDULER_PORT=8786

# Launch Dask scheduler and workers in the background
dask-scheduler --host $DASK_SCHEDULER_HOST --port $DASK_SCHEDULER_PORT &
dask-worker $DASK_SCHEDULER_HOST:$DASK_SCHEDULER_PORT --nprocs 4 --nthreads 1 --local-directory dask-work-dir &

# Publish dataset to cluster
python publish_data.py

# Launch app for deployment with gunicorn
gunicorn "app:get_server()" --timeout 60 --workers 4
wait
