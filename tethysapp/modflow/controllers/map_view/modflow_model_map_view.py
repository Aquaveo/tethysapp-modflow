"""
********************************************************************************
* Name: modflow_model_map_view.py
* Author: ckrewson
* Created On: February 13, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
from tethysext.atcore.controllers.map_view import MapView
from tethys_sdk.gizmos import SelectInput
from tethysext.atcore.services.model_file_database import ModelFileDatabase
from tethysext.atcore.services.model_file_database_connection import ModelFileDatabaseConnection
from tethysext.atcore.gizmos.slide_sheet import SlideSheet
from tethys_sdk.permissions import has_permission
from tethysapp.modflow.lib.map_helpers import show_helper_status
from django.shortcuts import reverse
from django.http import JsonResponse
import os
import shutil
import uuid
import zipfile
import collections
import pandas as pd
import shapefile as shp
import json
import geojson
import logging

log = logging.getLogger('tethys.' + __name__)

__all__ = ['ModflowModelMapView']


class ModflowModelMapView(MapView):
    """
    Class Based Controller for modflow model with and without resource_id
    """
    http_method_names = ['get', 'post']
    template_name = 'modflow/map_view/modflow_model_map_view.html'
    STRESS_PERIOD_TRANSLATOR = {1: 'Steady State',
                                7: '7-Yr 1 Mon 6',
                                8: '8-Yr 1 Mon 7',
                                9: '9-Yr 1 Mon 8',
                                13: '13-Yr 1 Mon 12',
                                55: '55-Yr 5 Mon 6',
                                56: '56-Yr 5 Mon 7',
                                57: '57-Yr 5 Mon 8',
                                61: '61-Yr 5 Mon 12',
                                }

    def get_model_db(self, request, resource, *args, **kwargs):
        """
        Hook to get managers. Avoid removing or modifying items in context already to prevent unexpected behavior.

        Args:
            request (HttpRequest): The request.
            resource (Resource): Resource instance or None.

        Returns:
            model_db (ModelDatabase): ModelDatabase instance.
            map_manager (MapManager): Map Manager instance
        """  # noqa: E501
        # If resource_id is given, mapview will be created with specific model instance
        if resource:
            database_id = resource.get_attribute('database_id')
            model_db = ModelFileDatabase(self._app, database_id=database_id)

        # If resource_id is not given, general mapview with all model boundaries will be created
        else:
            model_db = ModelFileDatabaseConnection(db_dir=self._app.get_app_workspace().path)

        return model_db

    def get_managers(self, request, resource, *args, **kwargs):
        """
        Hook to create mangers for specific model instances for modflow model map view
        or general instance for model selection map view

        Args:
            request (HttpRequest): The request.
            resource (ModflowModelResource): Modflow Model Resource or none, depending on model or selection map_view
        """
        gs_engine = self._app.get_spatial_dataset_service(self.geoserver_name, as_engine=True)

        # If resource_id is given, mapview will be created with specific model instance
        if resource:
            model_version = resource.get_attribute('model_version')
            database_id = resource.get_attribute('database_id')

            model_db = ModelFileDatabase(self._app, database_id=database_id)
            model_file_db_connection = model_db.model_db_connection
            spatial_manager = self._SpatialManager(gs_engine, model_file_db_connection, model_version)
            map_manager = self._MapManager(spatial_manager=spatial_manager, model_db=model_db)

        # If resource_id is not given, general mapview with all model boundaries will be created
        else:
            model_db = ModelFileDatabaseConnection(db_dir=self._app.get_app_workspace().path)
            spatial_manager = self._SpatialManager(gs_engine, model_db, 'filler')
            map_manager = self._MapManager(spatial_manager=spatial_manager, model_db=model_db)

        return model_db, map_manager

    def get_context(self, request, session, resource, context, model_db, *args, **kwargs):
        """
        Hook to add additional content to context. Avoid removing or modifying items in context already to prevent unexpected behavior.

        Args:
            request (HttpRequest): The request.
            session (sqlalchemy.Session): the session.
            resource (Resource): the resource for this request.
            context (dict): The context dictionary.
            model_db (ModelDatabase): ModelDatabase instance associated with this request.

        Returns:
            dict: modified context dictionary.
        """  # noqa: E501
        # Run super class get context to get context from MapView
        context = super().get_context(request, session, resource, context, model_db, *args, **kwargs)
        # create legend scales if resource_id is given
        if resource:
            low_red_color_scale = {'val_no_data': '#fffff1',
                                   'val0': '#FF0000',
                                   'val1': '#FF3000',
                                   'val2': '#FF7000',
                                   'val3': '#FFA200',
                                   'val4': '#FFD000',
                                   'val5': '#FFFF00',
                                   'val6': '#A2D05C',
                                   'val7': '#45A2B9',
                                   'val8': '#0080FF',
                                   'val9': '#003ea3',
                                   'val10': '#003ea3'}

            low_blue_color_scale = {'val_no_data': '#fffff1',
                                    'val0': '#003ea3',
                                    'val1': '#0080FF',
                                    'val2': '#45A2B9',
                                    'val3': '#A2D05C',
                                    'val4': '#FFFF00',
                                    'val5': '#FFD000',
                                    'val6': '#FFA200',
                                    'val7': '#FF7000',
                                    'val8': '#FF7000',
                                    'val9': '#FF0000',
                                    'val10': '#FF0000'}

            # Creating legend and adding to context (i.e {'legend': {'layer': {value0: 'color0', value1: 'color1}}})
            legends = []
            for layer_groups in context['layer_groups']:
                if layer_groups['id'] != 'custom_layers':
                    for layer in layer_groups['layers']:
                        legend_key = layer['data']['layer_id']
                        if ":" in legend_key:
                            legend_key = legend_key.replace(":", "_")

                        legend_info = {
                            'legend_id': legend_key,
                            'title': layer['legend_title'],
                            'divisions': dict()
                        }

                        # Uses param ENV to create the scale
                        divisions = layer['options']['params']['ENV'].split(";")
                        if 'WEL-flux' in layer['options']['params']['LAYERS'] or 'EVT-' in \
                                layer['options']['params']['LAYERS']:
                            if len(divisions) == 1:
                                color_scale = low_red_color_scale
                            else:
                                color_scale = low_blue_color_scale
                        else:
                            color_scale = low_red_color_scale
                        for division in divisions:
                            division = division.split(":")
                            if division[0][:11] != 'val_no_data':
                                legend_info['divisions'][float(division[1])] = color_scale[division[0]]
                        legend_info['divisions'] = collections.OrderedDict(
                            sorted(legend_info['divisions'].items())
                        )

                        legends.append(legend_info)
                    # Collase all layer groups
                    layer_groups['collapsed'] = True

            length_unit = resource.get_attribute('model_units')
            time_unit = resource.get_attribute('time_unit')
            if 'layer_dropdown_toggle' in context:
                context['layer_dropdown_toggle']['on_label'] = 'Public'
                context['layer_dropdown_toggle']['off_label'] = 'Private'

            context['show_helpers'] = show_helper_status(request, 'modflow_model')
            # Override Layer Tab
            context['layer_tab_name'] = 'Model Details'
            publication = resource.get_attribute('publication')
            publication_link = resource.get_attribute('publication_link')
            nlay = resource.get_attribute('nlay')
            if not nlay:
                nlay = 1
            nper = resource.get_attribute('nper')
            # max_sp = resource.get_attribute('max_stress_period')
            sp_list = [0, 6, 7, 8, 12, 54, 55, 56, 60]
            if not nper:
                nper = 1
            show_layer_selector = nlay > 1
            show_stress_period_selector = nper > 1
            layer_options = []
            for i in range(nlay):
                layer_options.append((i+1, i+1))
            stress_period_options = []
            for i in range(nper):
                if i in sp_list:
                    stress_period_options.append((i+1, self.STRESS_PERIOD_TRANSLATOR[i+1]))
            show_depletion_tool = False
            if "_DRN-" in resource.get_attribute('geoserver_layers') \
                or "_SFR-" in resource.get_attribute('geoserver_layers') \
                    or "_RIV-" in resource.get_attribute('geoserver_layers'):
                show_depletion_tool = True
            layer_selector = SelectInput(name='layer_selector', initial=1, options=layer_options, display_text='Layer')
            stress_period_selector = SelectInput(name='sp_selector', initial=1, options=stress_period_options,
                                                 display_text='Stress Period')

            default_sp = str(list(self.STRESS_PERIOD_TRANSLATOR.keys()))
            default_sp = default_sp.replace('[', '').replace(']', '')
            context['layer_options'] = layer_options
            context['stress_period_options'] = stress_period_options
            context['nper'] = nper + 1
            context['nlay'] = nlay + 1
            context['default_sp'] = default_sp
            context['publication'] = publication
            context['publication_link'] = publication_link
            context['layer_tab_name'] = 'Model Details'
            context['tools_tab_name'] = 'Tools'
            context['well_influence_tool_name'] = 'Simulate well(s) effects on groundwater and/or surface water'
            context['flow_path_tool_name'] = 'Delineate groundwater flow path'
            context['results_tab_name'] = 'Results'
            context['show_custom_layer'] = True
            context['show_layer_selector'] = show_layer_selector
            context['show_stress_period_selector'] = show_stress_period_selector
            context['layer_selector'] = layer_selector
            context['stress_period_selector'] = stress_period_selector

            flow_path_slide_sheet = SlideSheet(id='flow-path-slide-sheet',
                                               title='Flow Path',
                                               content_template='modflow/slide_sheet/flow_path.html',
                                               )

            pump_impact_slide_sheet = SlideSheet(id='pump-impact-slide-sheet',
                                                 title='Simulate Well Influence',
                                                 content_template='modflow/slide_sheet/pump_impact.html',
                                                 transient_model=show_stress_period_selector,
                                                 nlay=nlay + 1,
                                                 nper=nper,
                                                 layer_options=layer_options,
                                                 default_sp=default_sp,
                                                 time_unit=time_unit,
                                                 show_depletion_tool=show_depletion_tool,
                                                 )
            context.update({'flow_path_slide_sheet': flow_path_slide_sheet,
                            'legends': legends,
                            'pump_impact_slide_sheet': pump_impact_slide_sheet,
                            'length_unit': length_unit,
                            'time_unit': time_unit})
        # if no resource_id, template and map title are changed for model_selection_map_view
        else:
            self.template_name = 'modflow/map_view/model_selection_map_view.html'
            context['nav_title'] = 'Modflow Models'
            context['show_custom_layer'] = False
            context['show_helpers'] = show_helper_status(request, 'model_selection')

        return context

    def default_back_url(self, request, *args, **kwargs):
        """
        only used on modflow model map view so users can go back to model selection map view

        Args:
            request (HttpRequest): The request.

        Returns:
            redirects to the back controller
        """  # noqa: E501
        return reverse('modflow:home')

    def get_permissions(self, request, permissions, model_db, *args, **kwargs):
        """
        Hook to modify permissions.

        Args:
            request (HttpRequest): The request.
            permissions (dict): The permissions dictionary with boolean values.
            model_db (ModelDatabase): ModelDatabase instance associated with this request.

        Returns:
            dict: modified permisssions dictionary.
        """
        admin_user = has_permission(request, 'has_app_admin_role')
        permissions.update({'admin_user': admin_user})
        if has_permission(request, 'view_all_resources'):
            permissions['can_use_plot'] = True
            permissions['can_use_action'] = True
            permissions['can_use_geocode'] = True
            permissions['can_view'] = True

        return permissions

    def well_upload(self, request, *args, **kwargs):
        """
        POST method for uploading wells for pump impact.

        Args:
            request (HttpRequest): The request.
        Returns:
            JsonResponse with geojson for wells
        """
        user_ws = self._app.get_user_workspace(request.user).path
        zip_file = request.FILES.get('pump-file-upload')

        # Write file to workspace temporarily
        workdir = os.path.join(user_ws, str(uuid.uuid4()))

        if not os.path.isdir(workdir):
            os.mkdir(workdir)

        # Write in-memory file to disk
        filename = os.path.join(workdir, zip_file.name)
        with open(filename, 'wb') as f:
            for chunk in zip_file.chunks():
                f.write(chunk)

        # Unzip
        if zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename, 'r') as z:
                z.extractall(workdir)

        well_geojson = None
        try:
            # Check if shapefile or csv
            for f in os.listdir(workdir):
                extension = f.split(".")[-1]
                if extension == 'shp':
                    well_geojson = self.parse_shapefile(user_ws, zip_file)
                elif extension == 'csv' or extension == 'xlsx':
                    path = os.path.join(workdir, f)
                    well_geojson = self.well_csv(path, extension)
        except Exception as e:
            log.exception(str(e))
            return JsonResponse({'success': False, 'message': 'Invalid data. Check Inputs for formatting'})
        finally:
            # Clean up
            shutil.rmtree(workdir)

        if not well_geojson:
            return JsonResponse({'success': False,
                                 'message': 'Only zip folders with .shp files or .csv/.xlsx files allowed'})

        return JsonResponse({'success': True, 'geojson': well_geojson})

    @staticmethod
    def well_csv(file, extension):
        """
        method for uploading a well spreadsheet.

        Args:
            file (filepath): file path to the well spreadsheet.
            extension (str): csv or xlsx extension
        Returns:
            Geojson for wells
        """
        if extension == 'csv':
            data = pd.read_csv(file)
        else:
            data = pd.read_excel(file, 'Sheet1', index_col=None)

        data_dict = data.to_dict(orient='records')
        features = []
        well_number = 1
        for well in data_dict:
            valid_geometry = True
            coord_dict = []
            i = 0
            flowrate = 0
            depth = 0
            points = ''
            for key, value in well.items():
                # Column B is Flowrate
                if i == 1:
                    flowrate = value
                # Column C is Depth
                elif i == 2:
                    depth = value
                # Column D is Location
                elif i == 3:
                    points = value
                i += 1
            points = points.split(",")
            if len(points) == 1:
                well_type = "Point"
            # Skip if we detect a line here.
            elif len(points) == 2:
                valid_geometry = False
            else:
                well_type = "Polygon"
            if valid_geometry:
                for point in points:
                    lat, lon = point.strip().split(" ")
                    coord_dict.append([float(lon), float(lat)])
                if well_type == 'Point':
                    coordinates = coord_dict[0]
                else:
                    coordinates = [coord_dict]
                feature_dict = {"geometry": {"coordinates": coordinates, "type": well_type},
                                "properties": {"ID": well_number,
                                               "Flowrate": flowrate,
                                               "Depth": depth,
                                               },
                                "type": "Feature"}
                features.append(feature_dict)
                well_number += 1
        geojson_dicts = {
            'type': 'FeatureCollection',
            'features': features
        }

        # Convert to geojson objects
        geojson_str = json.dumps(geojson_dicts)
        geojson_objs = geojson.loads(geojson_str)
        return geojson_objs

    @staticmethod
    def parse_shapefile(user_workspace, in_memory_file):
        """
        Parse shapefile, serialize into GeoJSON, and validate.
        Args:
            user_workspace(File Path): File path to the user workspace.
            in_memory_file (InMemoryUploadedFile): A zip archive containing the shapefile that has been uploaded.

        Returns:
            dict: Dictionary equivalent of GeoJSON.
        """
        workdir = None

        if not in_memory_file:
            return None

        try:
            # Write file to workspace temporarily
            workdir = os.path.join(user_workspace, str(uuid.uuid4()))

            if not os.path.isdir(workdir):
                os.mkdir(workdir)

            # Write in-memory file to disk
            filename = os.path.join(workdir, in_memory_file.name)
            with open(filename, 'wb') as f:
                for chunk in in_memory_file.chunks():
                    f.write(chunk)

            # Unzip
            if zipfile.is_zipfile(filename):
                with zipfile.ZipFile(filename, 'r') as z:
                    z.extractall(workdir)

            # Convert shapes to geojson
            features = []
            for f in os.listdir(workdir):
                if '.shp' not in f:
                    continue

                path = os.path.join(workdir, f)
                reader = shp.Reader(path)
                fields = reader.fields[1:]
                field_names = [field[0] for field in fields]

                for sr in reader.shapeRecords():
                    attributes = dict(zip(field_names, sr.record))
                    geometry = sr.shape.__geo_interface__
                    features.append({
                        'type': 'Feature',
                        'geometry': geometry,
                        'properties': attributes
                    })

            geojson_dicts = {
                'type': 'FeatureCollection',
                'features': features
            }

            # Convert to geojson objects
            geojson_str = json.dumps(geojson_dicts)
            geojson_objs = geojson.loads(geojson_str)

            # Validate
            if not geojson_objs.is_valid:
                raise RuntimeError('Invalid geojson from "shapefile" parameter: {}'.format(geojson_dicts))

        except shp.ShapefileException:
            raise ValueError('Invalid shapefile provided.')
        except Exception as e:
            raise RuntimeError('An error has occured while parsing the shapefile: {}'.format(e))

        finally:
            # Clean up
            workdir and shutil.rmtree(workdir)

        return geojson_objs

    def layer_name_change(self, request, session, resource, back_url):
        """
        POST method for changing layer names in the database.

        Args:
            request (HttpRequest): The request.
            session(postgres session): postgres session for the model resource
            resource(ModflowModelResource): Resource object for the resource

        Returns:
            JsonResponse
        """
        # TODO: Should this be in atcore?
        layer_name = request.POST.get('layer_name')
        group_name = request.POST.get('group_name')
        new_public = request.POST.get('new_name')
        layer_id = request.POST.get('layer_id')
        if not group_name:
            geoserver_groups = json.loads(resource.get_attribute('geoserver_groups'))
            geoserver_groups[layer_name]['public_name'] = new_public
            resource.set_attribute('geoserver_groups', json.dumps(geoserver_groups))
        elif group_name == 'custom_layers':
            # Find layer_name location to rename
            custom_layers = []
            for custom_layer in resource.get_attribute(group_name):
                if custom_layer['layer_id'] == layer_id:
                    custom_layer['display_name'] = new_public
                custom_layers.append(custom_layer)
            resource.set_attribute(group_name, custom_layers)
        else:
            geoserver_layers = json.loads(resource.get_attribute('geoserver_layers'))
            if group_name != 'Boundary' and group_name != 'Head':
                geoserver_layers['Packages'][group_name][layer_name]['public_name'] = new_public
            else:
                geoserver_layers[group_name][layer_name]['public_name'] = new_public
            resource.set_attribute('geoserver_layers', json.dumps(geoserver_layers))
        session.commit()

        return JsonResponse({'success': True})

    def remove_layer(self, request, session, resource, back_url):
        """
        POST method for removing layer or layer groups in the database.

        Args:
            request (HttpRequest): The request.
            session(postgres session): postgres session for the model resource
            resource(ModflowModelResource): Resource object for the resource

        Returns:
            JsonResponse
        """
        layer_name = request.POST.get('layer_name')
        group_name = request.POST.get('group_name')
        geoserver_layers = json.loads(resource.get_attribute('geoserver_layers'))

        if group_name:
            if group_name != 'Boundary' and group_name != 'Head':
                if group_name in geoserver_layers['Packages']:
                    if layer_name:
                        if layer_name in geoserver_layers['Packages'][group_name]:
                            geoserver_layers['Packages'][group_name].pop(layer_name, None)
                    else:
                        geoserver_layers['Packages'].pop(group_name, None)
            else:
                if layer_name:
                    if layer_name in geoserver_layers[group_name]:
                        geoserver_layers[group_name].pop(layer_name, None)
                else:
                    if group_name in geoserver_layers:
                        geoserver_layers.pop(group_name, None)
        else:
            # When trying to delete layer groups, layer_name = layer group names and group_name is empty.
            group_name = layer_name
            if group_name != 'Boundary' and group_name != 'Head':
                geoserver_layers['Packages'].pop(group_name, None)
            else:
                if group_name in geoserver_layers:
                    geoserver_layers.pop(group_name, None)

        resource.set_attribute('geoserver_layers', json.dumps(geoserver_layers))

        session.commit()

        return JsonResponse({'success': True})

    def layer_public_toggle_change(self, request, session, resource, back_url):
        """
        POST method for changing layer names in the database.

        Args:
            request (HttpRequest): The request.
            session(postgres session): postgres session for the model resource
            resource(ModflowModelResource): Resource object for the resource

        Returns:
            JsonResponse
        """
        layer_name = request.POST.get('layer_name')
        group_name = request.POST.get('group_name')
        state = request.POST.get('state').lower() == 'true'
        layer_uuid = request.POST.get('layer_uuid', '')

        if not group_name:
            geoserver_groups = json.loads(resource.get_attribute('geoserver_groups'))
            geoserver_groups[layer_name]['active'] = state
            resource.set_attribute('geoserver_groups', json.dumps(geoserver_groups))
        elif group_name == 'custom_layers':
            layer_uuid = request.POST.get('layer_uuid')
            new_custom_layers = []
            for custom_layer in resource.get_attribute(group_name):
                if custom_layer['uuid'] == layer_uuid:
                    custom_layer['active'] = state
                new_custom_layers.append(custom_layer)
            resource.set_attribute(group_name, new_custom_layers)
        else:
            geoserver_layers = json.loads(resource.get_attribute('geoserver_layers'))
            if group_name != 'Boundary' and group_name != 'Head':
                geoserver_layers['Packages'][group_name][layer_name]['active'] = state
            else:
                geoserver_layers[group_name][layer_name]['active'] = state
            resource.set_attribute('geoserver_layers', json.dumps(geoserver_layers))
        session.commit()

        return JsonResponse({'success': True})

    def save_spatial_data(self, request, session, resource, back_url):
        data = request.POST.get('data', '')
        data = data.split('&')
        feature_id = 0
        time_series = ''
        for data_point in data:
            if 'feature-id' in data_point:
                feature_id = data_point.split('=')[1]
            elif 'Time' in data_point:
                time_series += data_point.split('=')[1] + ","
            elif 'Pumping' in data_point:
                time_series += data_point.split('=')[1] + ";"
        if time_series[-1] == ";":
            time_series = time_series[:-1]
        return JsonResponse({'success': True, 'feature_id': feature_id, 'time_series': time_series})
