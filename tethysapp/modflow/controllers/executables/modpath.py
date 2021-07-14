"""
********************************************************************************
* Name: modpath.py
* Author: ckrewson
* Created On: February 18, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import os
import shutil
import logging
import json
from tethysext.atcore.services.model_file_database import ModelFileDatabase
from modflow_adapter.models.app_users.modflow_model_resource import ModflowModelResource
from tethysapp.modflow.app import Modflow as app
from modflow_adapter.services.modflow_spatial_manager import ModflowSpatialManager
from django.http import JsonResponse
from tethysapp.modflow.condor_workflows.modpath_workflow import ModpathWorkflow
from guardian.utils import get_anonymous_user
import time

log = logging.getLogger('tethys.' + __name__)


def modpath(request):
    """
    Ajax controller that prepares and submits the new modpath jobs and workflow.
    """
    session = None
    try:
        session_id = request.session.session_key
        resource_id = request.POST.get('resource_id')
        cancel_status = request.POST.get('cancel', '')

        # Getting model attribute data from database
        Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
        session = Session()
        resource = session.query(ModflowModelResource).get(resource_id)

        if cancel_status:
            max_wait_time = 20
            job_id = get_job_id(resource_id, session, max_wait_time)
            job_manager = app.get_job_manager()

            running_job = job_manager.get_job(job_id)

            # Stop running job
            running_job.stop()

            # Clear job_id
            resource.set_attribute('job_id', '')
            session.commit()

            return JsonResponse({'success': True, 'message': 'Flow Path Tool has been cancelled.'})
        else:
            lon = request.POST.get('lon')
            lat = request.POST.get('lat')
            depth = request.POST.get('depth')

            if not resource_id:
                return JsonResponse({'success': False, 'message': 'No resource ID given. Check URL for ID.'})

            xll = resource.get_attribute('xll')
            yll = resource.get_attribute('yll')
            rotation = resource.get_attribute('rotation')
            if not rotation:
                rotation = "0"
            model_units = resource.get_attribute('model_units')
            model_version = resource.get_attribute('model_version')
            srid = resource.get_attribute('srid')
            database_id = resource.get_attribute('database_id')

            # setting up spatial manager to get model file list, and modflow executables
            model_db = ModelFileDatabase(app=app, database_id=database_id)
            gs_engine = app.get_spatial_dataset_service(app.GEOSERVER_NAME, as_engine=True)
            spatial_manager = ModflowSpatialManager(geoserver_engine=gs_engine,
                                                    model_file_db_connection=model_db.model_db_connection,
                                                    modflow_version=model_version)

            modflow_exe = os.path.join(spatial_manager.EXE_PATH, model_version)
            modpath_exe = os.path.join(spatial_manager.EXE_PATH, 'mp7')

            model_file_list = spatial_manager.model_file_db.list()

            # Loop through model file database for a .nam or .mfn file
            for file in model_file_list:
                # TODO: figure out .mfn problems
                if file.split(".")[-1] in ['nam', 'mfn']:
                    break

            user_workspace = app.get_user_workspace(request.user)
            user_workspace_path = user_workspace.path

            # Django validation. After Django2.0, is_authenticated is a property
            try:
                check_user = request.user.is_authenticated()
            except:  # noqa: E722
                check_user = request.user.is_authenticated

            # Used to get a valid Django anonymous user if not signed in
            if check_user:
                user = request.user
            else:
                user = get_anonymous_user()

            try:
                job = ModpathWorkflow(
                    user=user,
                    workspace=user_workspace_path,
                    session_id=session_id,
                    lat=lat,
                    lon=lon,
                    depth=depth,
                    xll=xll,
                    yll=yll,
                    rotation=rotation,
                    db_dir=model_db.directory,
                    model_units=model_units,
                    model_version=model_version,
                    modflow_exe=modflow_exe,
                    modpath_exe=modpath_exe,
                    nam_file=file,
                    srid=srid,
                    resource_id=resource.id,
                    database_id=database_id,
                    app_package=app.package,
                )
                job.run_job()
                workflow_id = job.workflow.id
                remote_id = job.workflow.remote_id

                # Save job_id in resource so we can cancel it if necessary.
                resource.set_attribute('job_id', workflow_id)
                session.commit()
                return JsonResponse({'success': True, 'resource_id': resource_id, 'workflow_id': workflow_id,
                                     'remote_id': remote_id})
            except Exception as e:
                log.exception(str(e))
                return JsonResponse({'success': False,
                                     'message': 'An unexpected error has occurred. '
                                                'Please contact Aquaveo and try again later.'
                                     })
    finally:
        session and session.close()


def get_flow_path_json(request):
    """
    Ajax controller that retrieves data after modpath jobs and workflow finish.
    Returns:
        JsonResponse with geojson data.
    """
    ws = app.get_user_workspace(request.user).path
    remote_id = request.POST.get('remote_id')
    remote_folder = os.path.join(ws, remote_id)
    json_file = os.path.join(remote_folder, 'prepare_modpath_job', 'flow_path.json')

    # Checks for file that was transferred from condor
    if not os.path.isfile(json_file):
        log.exception(str("No flow path json file exists"))
        return JsonResponse({'success': False, 'message': "An unexpected error has occurred. Try again please."})

    with open(json_file) as f:
        data = json.load(f)

    # Clean up files
    shutil.rmtree(remote_folder)

    return JsonResponse({'success': True, 'data': data})


def get_job_id(resource_id, session, wait_time):
    resource = session.query(ModflowModelResource).get(resource_id)
    max_time_to_wait = wait_time
    processing_time = 0
    while resource.get_attribute('job_id') == '' and processing_time < max_time_to_wait:
        time.sleep(1)
        processing_time += 1
        resource = session.query(ModflowModelResource).get(resource_id)

    return resource.get_attribute('job_id')
