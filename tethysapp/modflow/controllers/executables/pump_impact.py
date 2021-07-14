"""
********************************************************************************
* Name: pump_impact.py
* Author: ckrewson
* Created On: February 18, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import os
import logging
import json
import statistics
import shutil
from tethysext.atcore.services.model_file_database import ModelFileDatabase
from modflow_adapter.models.app_users.modflow_model_resource import ModflowModelResource
from tethysapp.modflow.app import Modflow as app
from modflow_adapter.services.modflow_spatial_manager import ModflowSpatialManager
from django.http import JsonResponse
from tethysapp.modflow.condor_workflows.drawdown_workflow import DrawdownWorkflow
from tethysapp.modflow.condor_workflows.stream_depletion_workflow import StreamDepletionWorkflow
from tethysapp.modflow.condor_workflows.run_all_tools_workflow import RunAllToolsWorkflow
from guardian.utils import get_anonymous_user
import time

log = logging.getLogger('tethys.' + __name__)


def parseIntSet(nputstr=""):
    selection = set()
    invalid = set()
    # tokens are comma seperated values
    tokens = [x.strip() for x in nputstr.split(',')]

    for i in tokens:
        if len(i) > 0:
            if i[:1] == "<":
                i = "1-%s" % (i[1:])
        try:
            # typically tokens are plain old integers
            selection.add(int(i))
        except ValueError:
            # if not, then it might be a range
            try:
                token = [int(k.strip()) for k in i.split('-')]
                if len(token) > 1:
                    token.sort()
                    # we have items seperated by a dash
                    # try to build a valid range
                    first = token[0]
                    last = token[len(token)-1]
                    for x in range(first, last+1):
                        selection.add(x)
            except ValueError:
                # not an int and not a range...
                invalid.add(i)
    # Report invalid tokens before returning valid selection
    if len(invalid) > 0:
        print("Invalid set: " + str(invalid))
    selection_string = str(selection)
    selection_string = selection_string.replace("{", "").replace("}", "").replace(", ", "_")
    return selection_string


def pump_impact(request):
    """
    Ajax controller that prepares and submits the new pump impact jobs and workflow.
    """
    session = None

    try:
        session_id = request.session.session_key
        resource_id = request.POST.get('resource_id')
        pumps = request.POST.get('data')
        tool = request.POST.get('tool')
        cancel_status = request.POST.get('cancel', '')
        stream_package = request.POST.get('package', '')
        if stream_package == "":
            stream_package = "_"
        layer = parseIntSet(request.POST.get('layer', '0'))
        stress_period = parseIntSet(request.POST.get('stress_period_output', '0'))
        data_input = request.POST.get('input')
        if not resource_id:
            return JsonResponse({'success': False, 'message': 'No resource ID given. Check URL for ID.'})

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

            return JsonResponse({'success': True, 'message': 'Well Influence Tool has been cancelled.'})
        else:
            xll = resource.get_attribute('xll')
            yll = resource.get_attribute('yll')
            rotation = resource.get_attribute('rotation')
            model_units = resource.get_attribute('model_units')
            model_version = resource.get_attribute('model_version')
            srid = resource.get_attribute('srid')
            database_id = resource.get_attribute('database_id')

            # Writing geojson file for pumps to be passed to condor worker
            model_db = ModelFileDatabase(app=app, database_id=database_id)
            pump_json_file = os.path.join(model_db.directory, "well_impact.json")
            geojson = open(pump_json_file, "w")
            geojson.write(pumps + "\n")
            geojson.close()

            # setting up spatial manager to get model file list, and modflow executables
            gs_engine = app.get_spatial_dataset_service(app.GEOSERVER_NAME, as_engine=True)

            spatial_manager = ModflowSpatialManager(geoserver_engine=gs_engine,
                                                    model_file_db_connection=model_db.model_db_connection,
                                                    modflow_version=model_version)

            modflow_exe = os.path.join(spatial_manager.EXE_PATH, model_version)

            model_file_list = spatial_manager.model_file_db.list()

            # Loop through model file database for needed files
            wel_file = '_'
            hds_file = '_'
            # cbb_file = '_'
            nam_file = ''
            for file in model_file_list:
                # TODO: figure out .mfn problems
                if file.split(".")[-1] == 'nam':
                    nam_file = file
                if file.split(".")[-1] == 'hds':
                    hds_file = file
                if file.split(".")[-1] == 'wel':
                    wel_file = file
                # if file.split(".")[-1] == 'cbb':
                #     cbb_file = file

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
                if tool == 'drawdown':
                    job = DrawdownWorkflow(
                        user=user,
                        workspace=user_workspace_path,
                        session_id=session_id,
                        xll=xll,
                        yll=yll,
                        rotation=rotation,
                        db_dir=model_db.directory,
                        model_units=model_units,
                        model_version=model_version,
                        modflow_exe=modflow_exe,
                        nam_file=nam_file,
                        hds_file=hds_file,
                        wel_file=wel_file,
                        srid=srid,
                        resource_id=resource.id,
                        database_id=database_id,
                        app_package=app.package,
                        contour_levels=data_input,
                        export_layer_string=layer,
                        export_sp_string=stress_period,
                    )
                elif tool == 'stream_depletion':
                    job = StreamDepletionWorkflow(
                        user=user,
                        workspace=user_workspace_path,
                        session_id=session_id,
                        xll=xll,
                        yll=yll,
                        rotation=rotation,
                        db_dir=model_db.directory,
                        model_units=model_units,
                        model_version=model_version,
                        modflow_exe=modflow_exe,
                        nam_file=nam_file,
                        wel_file=wel_file,
                        srid=srid,
                        resource_id=resource.id,
                        database_id=database_id,
                        app_package=app.package,
                        stream_package=stream_package,
                        std_minimum_change=data_input,
                        export_layer_string=layer,
                        export_sp_string=stress_period,
                    )
                else:
                    data_input = data_input.split(";")
                    contour_levels = data_input[0]
                    std_minimum_change = data_input[1]
                    job = RunAllToolsWorkflow(
                        user=user,
                        workspace=user_workspace_path,
                        session_id=session_id,
                        xll=xll,
                        yll=yll,
                        rotation=rotation,
                        db_dir=model_db.directory,
                        model_units=model_units,
                        model_version=model_version,
                        modflow_exe=modflow_exe,
                        nam_file=nam_file,
                        wel_file=wel_file,
                        srid=srid,
                        resource_id=resource.id,
                        database_id=database_id,
                        app_package=app.package,
                        stream_package=stream_package,
                        std_minimum_change=std_minimum_change,
                        export_layer_string=layer,
                        export_sp_string=stress_period,
                        contour_levels=contour_levels,
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
                                     'message': 'An unexpected error has occurred.'
                                                ' Please contact Aquaveo and try again later.'
                                     })
    finally:
        session and session.close()


def get_pump_impact_json(request):
    """
    Ajax controller that retrieves data after pump impact jobs and workflow finish.
    Returns:
        JsonResponse with data and scale for the legends
    """
    ws = app.get_user_workspace(request.user).path
    remote_id = request.POST.get('remote_id')
    tool = request.POST.get('tool')
    remote_folder = os.path.join(ws, remote_id)
    if tool == 'drawdown':
        legend_ordered = {}
        tool = 'run_all_tools'
        drawdown_folder = os.path.join(remote_folder, '{}_job'.format(tool))
        data = {}
        drawdown_data = {}
        for file in os.listdir(drawdown_folder):
            if file.startswith('well_impact_'):
                if file.endswith('.json'):
                    stress_period = int(file.replace('.json', "").split("_")[-1]) + 1
                    layer = int(file.replace('.json', "").split("_")[-2]) + 1
                    with open(os.path.join(drawdown_folder, file)) as f:
                        drawdown_data.setdefault(layer, {})[stress_period] = json.load(f)

        if not drawdown_data:
            log.exception(str("No drawdown json file exists"))
            return JsonResponse({'success': False, 'message': "An unexpected error has occurred. Try again please."})

        data['drawdown'] = drawdown_data

        drawdown_dataset = []
        for drawdown_layer in data['drawdown']:
            for drawdown_sp in data['drawdown'][drawdown_layer]:
                for drawdown_feature in data['drawdown'][drawdown_layer][drawdown_sp]['features']:
                    drawdown_dataset.append(float(drawdown_feature["properties"]["level"]))

        # drawdown_scale = generate_custom_color_ramp_divisions_std(drawdown_dataset, 9)
        # Fix data for drawdown
        drawdown_scale = remove_duplicate_items_from_list(drawdown_dataset)

        legend_ordered['drawdown'] = drawdown_scale
        shutil.rmtree(remote_folder)
        return JsonResponse({'success': True, 'data': data, 'legend': drawdown_scale})

    elif tool == 'stream_depletion':
        legend_ordered = {}
        data = {}
        streamflow_folder = os.path.join(remote_folder, '{}_job'.format(tool))
        streamflowout_data = {}
        for file in os.listdir(streamflow_folder):
            if file.startswith('streamflowout_'):
                if file.endswith('.json'):
                    stress_period = int(file.replace('.json', "").split("_")[-1]) + 1
                    layer = int(file.replace('.json', "").split("_")[-2]) + 1
                    with open(os.path.join(streamflow_folder, file)) as f:
                        streamflowout_data.setdefault(layer, {})[stress_period] = json.load(f)

        if not streamflowout_data:
            log.exception(str("No streamflow json file exists"))
            return JsonResponse({'success': False, 'message': "An unexpected error has occurred. Try again please."})
        data['streamflow_data'] = streamflowout_data

        stream_flow_dataset = []
        for streamflow_layer in data['streamflow_data']:
            for streamflow_sp in data['streamflow_data'][streamflow_layer]:
                for stream_feature in data['streamflow_data'][streamflow_layer][streamflow_sp]['features']:
                    stream_flow_dataset.append(float(stream_feature["properties"]["SF_Diff"]))

        streamflowout_scale = generate_custom_color_ramp_divisions_interval(stream_flow_dataset, 9)

        legend_ordered['streamflow'] = streamflowout_scale

        stream_flow_percentage_dataset = []
        for streamflow_layer in data['streamflow_data']:
            for streamflow_sp in data['streamflow_data'][streamflow_layer]:
                for stream_feature in data['streamflow_data'][streamflow_layer][streamflow_sp]['features']:
                    stream_flow_percentage_dataset.append(float(stream_feature["properties"]["SF_Diff_Per"]))

        streamflowout_percentage_scale = generate_custom_color_ramp_divisions_interval(stream_flow_percentage_dataset,
                                                                                       9)
        legend_ordered['streamflow_percentage'] = streamflowout_percentage_scale

        shutil.rmtree(remote_folder)

        return JsonResponse({'success': True, 'data': data, 'legend': legend_ordered})
    else:
        legend_ordered = {}
        tool = 'run_all_tools'
        drawdown_folder = os.path.join(remote_folder, '{}_job'.format(tool))
        data = {}
        drawdown_data = {}
        for file in os.listdir(drawdown_folder):
            if file.startswith('well_impact_'):
                if file.endswith('.json'):
                    stress_period = int(file.replace('.json', "").split("_")[-1]) + 1
                    layer = int(file.replace('.json', "").split("_")[-2]) + 1
                    with open(os.path.join(drawdown_folder, file)) as f:
                        drawdown_data.setdefault(layer, {})[stress_period] = json.load(f)

        if not drawdown_data:
            log.exception(str("No drawdown json file exists"))
            return JsonResponse({'success': False, 'message': "An unexpected error has occurred. Try again please."})

        data['drawdown'] = drawdown_data

        drawdown_dataset = []
        for drawdown_layer in data['drawdown']:
            for drawdown_sp in data['drawdown'][drawdown_layer]:
                for drawdown_feature in data['drawdown'][drawdown_layer][drawdown_sp]['features']:
                    drawdown_dataset.append(float(drawdown_feature["properties"]["level"]))

        # drawdown_scale = generate_custom_color_ramp_divisions_std(drawdown_dataset, 9)
        # Fix data for drawdown
        drawdown_scale = remove_duplicate_items_from_list(drawdown_dataset)

        legend_ordered['drawdown'] = drawdown_scale

        streamflow_folder = os.path.join(remote_folder, '{}_job'.format(tool))
        streamflowout_data = {}
        for file in os.listdir(streamflow_folder):
            if file.startswith('streamflowout_'):
                if file.endswith('.json'):
                    stress_period = int(file.replace('.json', "").split("_")[-1]) + 1
                    layer = int(file.replace('.json', "").split("_")[-2]) + 1
                    with open(os.path.join(streamflow_folder, file)) as f:
                        streamflowout_data.setdefault(layer, {})[stress_period] = json.load(f)

        if not streamflowout_data:
            log.exception(str("No streamflow json file exists"))
            return JsonResponse({'success': False, 'message': "An unexpected error has occurred. Try again please."})
        data['streamflow_data'] = streamflowout_data

        stream_flow_dataset = []
        for streamflow_layer in data['streamflow_data']:
            for streamflow_sp in data['streamflow_data'][streamflow_layer]:
                for stream_feature in data['streamflow_data'][streamflow_layer][streamflow_sp]['features']:
                    stream_flow_dataset.append(float(stream_feature["properties"]["SF_Diff"]))

        streamflowout_scale = generate_custom_color_ramp_divisions_interval(stream_flow_dataset, 9)

        legend_ordered['streamflow'] = streamflowout_scale

        stream_flow_percentage_dataset = []
        for streamflow_layer in data['streamflow_data']:
            for streamflow_sp in data['streamflow_data'][streamflow_layer]:
                for stream_feature in data['streamflow_data'][streamflow_layer][streamflow_sp]['features']:
                    stream_flow_percentage_dataset.append(float(stream_feature["properties"]["SF_Diff_Per"]))

        streamflowout_percentage_scale = generate_custom_color_ramp_divisions_interval(stream_flow_percentage_dataset,
                                                                                       9)
        legend_ordered['streamflow_percentage'] = streamflowout_percentage_scale
        shutil.rmtree(remote_folder)
        return JsonResponse({'success': True, 'data': data, 'legend': legend_ordered})


def generate_custom_color_ramp_divisions_std(dataset, num_divisions=9):
    """
    Generate custom elevation divisions.

    Args:
        dataset: given dataset
        num_divisison(int): number of divisions. -- odd number

    Returns:
        data_list: list of std deviation range.
    """
    data_list = []
    if len(dataset) > 2:
        mean_data = statistics.mean(dataset)
        std_data = statistics.stdev(dataset)
        max_stddev = 2

        for division in range(1, int(num_divisions / 2) + 1):
            left_data = mean_data - float(max_stddev / num_divisions / 2) * division * std_data
            right_data = mean_data + float(max_stddev / num_divisions / 2) * division * std_data
            data_list.append(left_data)
            data_list.append(right_data)
        data_list.append(mean_data)
        data_list.sort()

    return data_list


def generate_custom_color_ramp_divisions_interval(dataset, interval=9):
    """
    Generate custom elevation divisions.

    Args:
        dataset: given dataset
        interval(int): number of interval.

    Returns:
        data_list: list of std deviation range.
    """
    data_list = []
    if len(dataset) > 2:
        min_value = min(dataset)
        max_value = max(dataset)
        spacing = float((max_value - min_value)/(interval-1))

        for increment in range(0, interval-1):
            data = min_value + spacing*increment
            data_list.append(data)
        data_list.append(max_value)
        data_list.sort()

    return data_list


def get_job_id(resource_id, session, wait_time):
    resource = session.query(ModflowModelResource).get(resource_id)
    max_time_to_wait = wait_time
    processing_time = 0
    while resource.get_attribute('job_id') == '' and processing_time < max_time_to_wait:
        time.sleep(1)
        processing_time += 1
        resource = session.query(ModflowModelResource).get(resource_id)

    return resource.get_attribute('job_id')


def remove_duplicate_items_from_list(data):
    seen = set()
    seen_add = seen.add
    return [x for x in data if not (x in seen or seen_add(x))]
