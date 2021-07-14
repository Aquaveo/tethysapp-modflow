# Installation

## Services

### GeoServer & PostGIS

```bash
tethys docker init -c geoserver postgis
```

Notes:

* Configure geoserver container with 1 REST node and 4 normal nodes
* At least 1 GB per node

### HTCondor

A system installation of HTCondor is fine. For development use a personal installation.

* https://research.cs.wisc.edu/htcondor/instructions/ubuntu/20/stable/

Create a symbolic link named `/opt/tethys-python` that points at the Tethys python executable. All of the condor job scripts for the app have the shebang `#! /opt/tethys-python` so that they will run with that Python.

```bash
conda activate tethys
which python
ln -s <which_python_result> /opt/tethys-python
```

Alternatively, you may want to use the `aquaveollc/condor-standalone` image to run HTCondor in a container. If you do so, you will need to create a new Dockerfile that extends this image and adds the `tethysext-atcore` and `modflow_adapter` libraries (the image should already have a conda environment with the `/opt/tethys-python` link). See: https://hub.docker.com/r/aquaveollc/condor-standalone

## App Dependencies

```bash
# Download and Install ATcore
git clone https://github.com/Aquaveo/tethysext-atcore.git
python setup.py <develop|install>

# Download and Install Modflow Adapter
git clone https://github.com/Aquaveo/modflow-adapter.git
python setup.py <develop|install>
```

## App

```bash
git clone https://github.com/Aquaveo/tethysapp-modflow.git
tethys install <-d>
```

## Setup Services and Settings

```bash
# Sync App to DB
tethys manage sync

# Create Services (if not already created)
tethys services create persistent -n <ps_service_name> -c <db_user>:<db_pass>@<db_host>:<db_port>
tethys services create spatial -n <gs_service_name> -c <username>:<password>@<protocol>://<host>:<port> -p <protocol>://<public_host>:<public_port>
tethys schedulers create-condor -n remote_cluster -e <condor_host> -e <condor_user> -f <path_to_ssh_key> -k <ssh_key_password>

# Link Services to App
tethys link persistent:<ps_service_name> <app_package>:ps_database:primary_db
tethys link persistent:<ps_service_name> <app_package>:ps_connection:model_db_1
tethys link spatial:<gs_service_name> <app_package>:ds_spatial:primary_geoserver

# Syncstores
tethys syncstores modflow
```

## Initialize App

```bash
python init_modflow.py
```

# Testing

The app includes a `test.sh` script that will run all tests and lint. To use:

1. Manually create a new database called `modflow_tests` in your PostGIS database.

2. Add these to your `.bashrc` or equivalent:

```bash
# You may want these in your .bashrc
export TETHYS_MANAGE=/path/to/tethys/manage.py
export MODFLOW_TEST_DATABASE=postgresql://<username>:<password>@<host>:<port>/modflow_tests
```

3. From the app source directory, run the following command:

```bash
. test.sh $TETHYS_MANAGE
```

2. To run integrated tests, install extension in existing installation of Tethys and run:
