from tethysapp.modflow.app import Modflow as app
from django.http import JsonResponse
from django.shortcuts import render
import json
import requests
from xml.etree import ElementTree
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from tethysapp.modflow.lib.map_helpers import transform
import uuid
from tethysext.atcore.models.app_users.user_setting import UserSetting
from tethysext.atcore.models.app_users import AppUser


def check_point_status(request):
    try:
        point_location = json.loads(request.GET['point_location'])
        layer_id = json.loads(request.GET['layer_id'])
        inprj = json.loads(request.GET['inprj'])
        gs_engine = app.get_spatial_dataset_service(app.GEOSERVER_NAME, as_engine=True)
        geoserver_link = gs_engine.endpoint.replace('rest', '')
        # Prevent // at the end of the link
        if geoserver_link[-2:] == "//":
            geoserver_link = geoserver_link[:-1]
        geoserver_wfs = geoserver_link + 'modflow/ows?service=WFS&version=1.0.0&request=GetFeature&typeName={}' \
                                         '&maxFeatures=1'.format(layer_id)
        xml_data = requests.get(geoserver_wfs)
        tree = ElementTree.fromstring(xml_data.content)
        # split to get outprj. the attrib has the following format: http://..#2901
        outprj = tree[1][0][0][0].attrib['srsName'].split('#')[1]
        x = float(point_location[1])
        y = float(point_location[0])
        x, y = transform(x, y, str(inprj), str(outprj))
        point = Point(x, y)
        xml_polygon = tree[1][0][0][0][0][0][0][0][0].text.split(' ')
        polygon_list = []
        for boundary_point in xml_polygon:
            split_point = boundary_point.split(',')
            polygon_list.append((float(split_point[0]), float(split_point[1])))
        polygon = Polygon(polygon_list)
        inside_polygon_status = polygon.contains(point)
    except Exception as e:
        print(str(e))
        inside_polygon_status = False
    return JsonResponse({'success': True, 'status': inside_polygon_status})


def check_well_depth(request):
    try:
        point_location = json.loads(request.GET['point_location'])
        layer_id = json.loads(request.GET['layer_id'])
        inprj = json.loads(request.GET['inprj'])
        depth = json.loads(request.GET['depth'])
        gs_engine = app.get_spatial_dataset_service(app.GEOSERVER_NAME, as_engine=True)
        geoserver_link = gs_engine.endpoint.replace('rest', '')
        # Prevent // at the end of the link
        if geoserver_link[-2:] == "//":
            geoserver_link = geoserver_link[:-1]

        # Get output Projection
        geoserver_wfs = geoserver_link + 'modflow/ows?service=WFS&version=1.0.0&request=GetFeature&typeName={}' \
                                         '&maxFeatures=1&'.format(layer_id)
        model_thickness = ''
        xml_data = requests.get(geoserver_wfs)
        tree = ElementTree.fromstring(xml_data.content)
        # split to get outprj. the attrib has the following format: http://..#2901
        outprj = tree[1][0][0][0].attrib['srsName'].split('#')[1]

        # Reproject point to output projection
        x = float(point_location[1])
        y = float(point_location[0])
        x, y = transform(x, y, str(inprj), str(outprj))
        point = Point(x, y)

        # Find intersects Polygon
        cql_filter = 'cql_filter=INTERSECTS(the_geom, {})'.format(point)

        geoserver_wfs = geoserver_link + 'modflow/ows?service=WFS&version=1.0.0&request=GetFeature&typeName={}' \
                                         '&maxFeatures=1&{}'.format(layer_id, cql_filter)
        xml_data = requests.get(geoserver_wfs)

        # Parse out Bottom Elevation
        tree = ElementTree.fromstring(xml_data.content)
        model_thickness = float(tree[1][0][5].text)
        if model_thickness > depth:
            inside_model = True
        else:
            inside_model = False
    except Exception as e:
        print(str(e))
        inside_model = False
    return JsonResponse({'success': True, 'status': inside_model, 'thickness': model_thickness})


def update_help_modal_status(request):
    try:
        status = request.GET['status'].lower() == 'true'
        page_name = request.GET['page_name']
        variable = 'show_helper_' + page_name

        # Get user
        session = None
        try:
            create_session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
            session = create_session()

            current_user = session.query(AppUser).filter(AppUser.username == request.user.username).first()
            if current_user:
                show_helper_setting = UserSetting(key=variable, value=status)

                # Check if setting existed
                current_setting = session.query(UserSetting).filter(AppUser.username == request.user.username).\
                    filter(UserSetting.key == variable).first()
                if current_setting:
                    # Update the record
                    current_setting.value = status
                else:
                    # Create new record
                    current_user.settings.append(show_helper_setting)
                session.commit()
        finally:
            session and session.close()

    except Exception as e:
        print(str(e))
        # Show help model by default if something went wrong
        status = True

    return JsonResponse({'success': True, 'status': status})


def insert_layer_data(request):
    uuid_string = str(uuid.uuid1())

    layer_group = {'id': 'Well_Influence_Tool_' + uuid_string,
                   'display_name': 'Well Influence Tool',
                   'control': 'checkbox',
                   'visible': 'true',
                   'layers': [
                       {'legend_title': 'Stream Leakage',
                        'layer_options': {'visible': 'true'},
                         'data': {'layer_id': 'Stream_Leakage_' + uuid_string,
                                  'layer_variable': 'leakage'}},
                       {'legend_title': 'Streamflow',
                        'layer_options': {'visible': 'true'},
                        'data': {'layer_id': 'Streamflow_' + uuid_string, 'layer_variable': 'streamflow'}},
                   ]}
    return render(request, 'atcore/components/custom_layer_content.html', {'layer_group': layer_group})


def pump_schedule_data(request):
    unit = request.GET['unit']
    time_unit = request.GET['time_unit']
    if unit == "gpm":
        pump_unit = "gallon"
        pump_time_unit = "minute"
    else:
        pump_unit = unit.split("/")[0]
        pump_time_unit = unit.split("/")[1]
    time_column = "Time (" + time_unit + ")"
    pump_column = "Pumping Rate (" + pump_unit + "/" + pump_time_unit + ")"
    columns = [time_column, pump_column]
    well_id = int(request.GET['well_id'])
    title = 'Well #' + str(well_id) + ' Pumping Schedule'
    data = request.GET.get('data', '')
    rows = list()
    if data:
        data = data.split("_")
        for data_point in data:
            data_point = data_point.split(',')
            if len(data_point) > 1:
                rows.append({time_column: data_point[0], pump_column: data_point[1]})
            else:
                rows.append({time_column: "", pump_column: ""})
    else:
        rows.append({time_column: '', pump_column: ''})
    feature_id = well_id
    plot_columns = (time_column, pump_column)
    return render(request, 'atcore/resource_workflows/components/spatial_dataset_form.html',
                  {'columns': columns, 'max_rows': 100, 'dataset_title': title, 'rows': rows, 'feature_id': feature_id,
                   'plot_columns': plot_columns})
