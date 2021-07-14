"""
********************************************************************************
* Name: map_manager
* Author: ckrewson
* Created On: February 13, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import logging
from tethys_sdk.permissions import has_permission
from tethys_gizmos.gizmo_options import MapView, MVView
from tethysext.atcore.services.map_manager import MapManagerBase
from modflow_adapter.models.app_users.modflow_model_resource import ModflowModelResource
from tethysapp.modflow.app import Modflow as app
import json

log = logging.getLogger(__name__)


class ModflowMapManager(MapManagerBase):
    """
    Object that orchestrates the map layers and resources for MODFLOW app.
    """
    MAX_ZOOM = 28
    MIN_ZOOM = 4
    DEFAULT_ZOOM = 13

    # TODO: fix method
    def get_map_preview_url(self):
        """
        Get url for map preview image.

        Returns:
            str: preview image url.
        """
        # Get model boundary name and style
        model_boundary_layer = self.spatial_manager.get_unique_item_name(
            item_name=self.spatial_manager.VL_MODEL_BOUNDARY,
            model_file_db=self.model_db
        )

        model_boundary_style = self.spatial_manager.get_unique_item_name(self.spatial_manager.VL_MODEL_BOUNDARY)

        # Default image url
        layer_preview_url = ''  # TODO: Get a nice default image

        try:
            extent = self.map_extent

            # Calculate preview layer height and width ratios
            if extent:
                # Calculate image dimensions
                long_dif = abs(extent[0] - extent[2])
                lat_dif = abs(extent[1] - extent[3])
                hw_ratio = float(long_dif) / float(lat_dif)
                max_dim = 300

                if hw_ratio < 1:
                    width_resolution = int(hw_ratio * max_dim)
                    height_resolution = max_dim
                else:
                    height_resolution = int(max_dim / hw_ratio)
                    width_resolution = max_dim

                wms_endpoint = self.spatial_manager.get_wms_endpoint()

                layer_preview_url = ('{}?'
                                     'service=WMS&'
                                     'version=1.1.0&'
                                     'request=GetMap&'
                                     'layers={}&'
                                     'styles={}&'
                                     'bbox={},{},{},{}&'
                                     'width={}&'
                                     'height={}&'
                                     'srs=EPSG:4326&'
                                     'format=image%2Fpng').format(wms_endpoint,
                                                                  model_boundary_layer,
                                                                  model_boundary_style,
                                                                  extent[0], extent[1], extent[2], extent[3],
                                                                  width_resolution, height_resolution)
        except Exception:
            log.exception('An error occurred while trying to generate the preview image.')

        return layer_preview_url

    def compose_map(self, request, resource_id=None, scenario_id=0, *args, **kwargs):
        """
        Compose the MapView object.

        Args:
            request (HttpRequest): A Django request object.
            resource_id(str)(optional): Give resource id for modflow model map view
            scenario_id(str)(optional): Scenario ID
        Returns:
            MapView, 4-list, list: The MapView, map extent, and layer groups.
        """
        try:
            # Get endpoint
            endpoint = self.spatial_manager.get_wms_endpoint()
            layers = []
            layer_groups = []

            show_public_toggle = has_permission(request, 'toggle_public_layers')

            # If resource_id is given, compose map creates a modflow model view for specific model
            if resource_id:
                head_layers = []
                boundary_group = []
                create_boundary_group = True
                custom_layer_group = []
                # Get default view and extent for model
                view, model_extent = self.get_map_extent()

                Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
                session = Session()

                # Get resource attributes by querying the resource with database_id
                resource = session.query(ModflowModelResource).get(resource_id)
                attributes = json.loads(resource._attributes)

                geoserver_layers = json.loads(attributes['geoserver_layers'])
                geoserver_groups = json.loads(attributes['geoserver_groups'])

                for group in geoserver_layers:
                    if group == 'Boundary' or group == 'Grid':
                        for geoserver_name in geoserver_layers[group]:
                            public = get_public_status(geoserver_layers[group][geoserver_name])
                            if show_public_toggle:
                                public_name = geoserver_layers[group][geoserver_name]['public_name']
                                if group == 'Boundary':
                                    layer = self.compose_model_boundary_layer(endpoint, geoserver_name, model_extent,
                                                                              public_name, str(resource_id), public,
                                                                              map_view_type='modflow_model')
                                else:
                                    layer = self.compose_model_grid_layer(endpoint, geoserver_name, model_extent,
                                                                          public_name, str(resource_id), public)
                                layers.append(layer)
                                boundary_group.append(layer)
                            elif geoserver_layers[group][geoserver_name]['active']\
                                    and geoserver_groups['Model']['active']:
                                public_name = geoserver_layers[group][geoserver_name]['public_name']
                                if group == 'Boundary':
                                    layer = self.compose_model_boundary_layer(endpoint, geoserver_name, model_extent,
                                                                              public_name, str(resource_id), public,
                                                                              map_view_type='modflow_model')
                                else:
                                    layer = self.compose_model_grid_layer(endpoint, geoserver_name, model_extent,
                                                                          public_name, str(resource_id), public)
                                layers.append(layer)
                                boundary_group.append(layer)
                        if boundary_group and create_boundary_group:
                            # Create model boundary layer group
                            public_group = get_public_status(geoserver_groups['Model'])
                            if public_group:
                                public_group = True
                            else:
                                public_group = False
                            layer_groups.append(
                                self.build_layer_group(
                                    id=group,
                                    display_name=geoserver_groups['Model']['public_name'],
                                    layers=boundary_group,
                                    layer_control='checkbox',
                                    visible=True,
                                    public=public_group
                                )
                            )
                            create_boundary_group = False
                    if group == 'Head':
                        for geoserver_name in geoserver_layers[group]:
                            public = get_public_status(geoserver_layers[group][geoserver_name])
                            if show_public_toggle:
                                minimum = float(geoserver_layers[group][geoserver_name]['minimum'])
                                maximum = float(geoserver_layers[group][geoserver_name]['maximum'])
                                public_name = geoserver_layers[group][geoserver_name]['public_name']
                                layer = self.compose_head_raster_layer(endpoint, geoserver_name, minimum, maximum,
                                                                       public_name, public, extent=model_extent,
                                                                       visible=True)

                                layers.append(layer)
                                head_layers.append(layer)
                            elif geoserver_layers[group][geoserver_name]['active'] \
                                    and geoserver_groups[group]['active']:
                                minimum = float(geoserver_layers[group][geoserver_name]['minimum'])
                                maximum = float(geoserver_layers[group][geoserver_name]['maximum'])
                                public_name = geoserver_layers[group][geoserver_name]['public_name']
                                layer = self.compose_head_raster_layer(endpoint, geoserver_name, minimum, maximum,
                                                                       public_name, public, extent=model_extent,
                                                                       visible=True)

                                layers.append(layer)
                                head_layers.append(layer)

                        if head_layers:
                            # Create model boundary layer group
                            public_group = geoserver_groups[group]['active']
                            if public_group:
                                public_group = True
                            else:
                                public_group = False
                            layer_groups.append(
                                self.build_layer_group(
                                    id=group,
                                    display_name=geoserver_groups[group]['public_name'],
                                    layers=head_layers,
                                    layer_control='radio',
                                    visible=False,
                                    public=public_group
                                )
                            )
                    if group == 'Packages':
                        for package in geoserver_layers[group]:
                            package_layers = []

                            for index, geoserver_name in enumerate(geoserver_layers[group][package]):
                                # Enable layer if it is the first one
                                visible = index == 0

                                if show_public_toggle:
                                    minimum = float(geoserver_layers[group][package][geoserver_name]['minimum'])
                                    maximum = float(geoserver_layers[group][package][geoserver_name]['maximum'])
                                    public_name = geoserver_layers[group][package][geoserver_name]['public_name']
                                    public = geoserver_layers[group][package][geoserver_name]['active']
                                    if public:
                                        public = True
                                    else:
                                        public = False

                                    layer = self.compose_package_layers(endpoint, geoserver_name, minimum, maximum,
                                                                        public_name, public, extent=model_extent,
                                                                        visible=visible)
                                    layers.append(layer)
                                    package_layers.append(layer)
                                elif geoserver_layers[group][package][geoserver_name]['active'] and \
                                        geoserver_groups[package]['active']:
                                    minimum = float(geoserver_layers[group][package][geoserver_name]['minimum'])
                                    maximum = float(geoserver_layers[group][package][geoserver_name]['maximum'])
                                    public_name = geoserver_layers[group][package][geoserver_name]['public_name']
                                    public = geoserver_layers[group][package][geoserver_name]['active']
                                    if public:
                                        public = True
                                    else:
                                        public = False
                                    layer = self.compose_package_layers(endpoint, geoserver_name, minimum, maximum,
                                                                        public_name, public, extent=model_extent,
                                                                        visible=visible)
                                    layers.append(layer)
                                    package_layers.append(layer)
                            if package_layers:
                                # Create model boundary layer group
                                public_group = geoserver_groups[package]['active']
                                if public_group:
                                    public_group = True
                                else:
                                    public_group = False
                                layer_groups.append(
                                    self.build_layer_group(
                                        id=package,
                                        display_name=geoserver_groups[package]['public_name'],
                                        layers=package_layers,
                                        layer_control='radio',
                                        visible=False,
                                        public=public_group
                                    )
                                )
                if 'custom_layers' in attributes:
                    custom_layers = attributes['custom_layers']
                    custom_layer_group = []
                    for custom_layer in custom_layers:
                        layer_id = custom_layer['layer_id']
                        layer_display_name = custom_layer['display_name']
                        service_link = custom_layer['service_link']
                        service_type = custom_layer['service_type']
                        service_layer_name = custom_layer['service_layer_name']
                        if 'active' in custom_layer:
                            public = custom_layer['active']
                        else:
                            public = True
                        # Compose layer
                        if service_type == 'WMS':
                            mv_layer = self.build_wms_layer(
                                endpoint=service_link,
                                extent=model_extent,
                                layer_name=service_layer_name,
                                layer_title=layer_display_name,
                                layer_variable='',
                                visible=False,
                                selectable=True,
                                tiled=True,
                                public=public,
                                layer_id=layer_id,
                            )
                            layers.append(mv_layer)
                            custom_layer_group.append(mv_layer)
                        elif service_type == 'TileArcGISRest':
                            mv_layer = self.build_arc_gis_layer(
                                endpoint=service_link,
                                extent=model_extent,
                                layer_name=service_layer_name,
                                layer_title=layer_display_name,
                                layer_variable='',
                                visible=False,
                                selectable=True,
                                tiled=True,
                                public=public,
                                layer_id=layer_id,
                            )
                            layers.append(mv_layer)
                            custom_layer_group.append(mv_layer)
                    if 'active' in custom_layers:
                        public_group = custom_layers['active']
                    else:
                        public_group = True
                    layer_groups.append(
                        self.build_layer_group(
                            id='custom_layers',
                            display_name='Custom Layer',
                            layers=custom_layer_group,
                            layer_control='checkbox',
                            visible=True,
                            public=public_group,
                        )
                    )
                else:
                    layer_groups.append(
                        self.build_layer_group(
                            id='custom_layers',
                            display_name='Custom Layer',
                            layers=[],
                            layer_control='checkbox',
                            visible=True,
                        )
                    )
            # If no resource_id, compose map of all model boundaries
            else:
                boundary_layers = {}
                Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
                session = Session()

                # Get resource_id and name by querying the resource with database_id
                resources = session.query(ModflowModelResource).all()
                for resource in resources:
                    attributes = json.loads(resource._attributes)
                    db_id = attributes['database_id'].replace("_", "-")
                    boundary_layers[resource.name] = \
                        {'layer': "{}:{}-{}_{}".format(self.spatial_manager.WORKSPACE,
                                                       self.spatial_manager.WORKSPACE, db_id,
                                                       self.spatial_manager.VL_MODEL_BOUNDARY),
                         'id': resource.id}

                minx = app.get_custom_setting('minx_extent')
                miny = app.get_custom_setting('miny_extent')
                maxx = app.get_custom_setting('maxx_extent')
                maxy = app.get_custom_setting('maxy_extent')
                if minx and miny and maxx and maxy:
                    model_extent = [float(minx), float(miny), float(maxx), float(maxy)]
                else:
                    model_extent = [-116, 44, -103, 49]

                boundary_group = []

                # Compose a model boundary layer for each model boundary
                for public_name in boundary_layers:
                    layer = self.compose_model_boundary_layer(endpoint, boundary_layers[public_name]['layer'],
                                                              model_extent, public_name,
                                                              str(boundary_layers[public_name]['id']), True,
                                                              map_view_type='modflow_selection')
                    layers.append(layer)
                    boundary_group.append(layer)

                # Create model boundary layer group
                layer_groups.append(
                    self.build_layer_group(
                        id='model_boundaries',
                        display_name='Available Models',
                        layers=boundary_group,
                        layer_control='checkbox',
                        visible=True
                    )
                )
                # Compute center
                center = self.DEFAULT_CENTER
                if model_extent and len(model_extent) >= 4:
                    center_x = (model_extent[0] + model_extent[2]) / 2.0
                    center_y = (model_extent[1] + model_extent[3]) / 2.0
                    center = [center_x, center_y]

                # Construct the default view
                view = MVView(
                    projection='EPSG:4326',
                    center=center,
                    zoom=self.DEFAULT_ZOOM,
                    maxZoom=self.MAX_ZOOM,
                    minZoom=self.MIN_ZOOM
                )

            esri_layer_names = [
                'NatGeo_World_Map',
                'USA_Topo_Maps',
                'World_Imagery',
                'World_Shaded_Relief',
                'World_Street_Map',
                'World_Topo_Map',
            ]
            esri_layers = [{'ESRI': {'layer': l}} for l in esri_layer_names]
            basemaps = [
                'Stamen',
                {'Stamen': {'layer': 'toner', 'control_label': 'Black and White'}},
                'OpenStreetMap',
                {'XYZ': {'url': 'https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png', 'control_label': 'Wikimedia'}},
                'ESRI',
            ]
            basemaps.extend(esri_layers)

            # Get custom maps settings
            custom_maps_string = app.get_custom_setting('custom_base_maps')
            if custom_maps_string is not None:
                custom_maps = custom_maps_string.strip().split(',')
                i = 0
                for custom_map in custom_maps:
                    # If no name is defined
                    custom_map_check_string = custom_map.replace('://', '')
                    if ':' not in custom_map_check_string:
                        i += 1
                        name = 'Custom' + str(i)
                        link = custom_map
                    else:
                        name = custom_map.split(':', 1)[0]
                        link = custom_map.split(':', 1)[1]
                    if validate_url(link):
                        if link[-1] != "/":
                            link += "/"
                        basemaps.extend([{'XYZ': {'url': link + '{z}/{x}/{y}.png', 'control_label': name}}])

            # Create MapView
            map_view = MapView(
                height='600px',
                width='100%',
                controls=['ZoomSlider', 'Rotate', 'FullScreen'],
                layers=layers,
                view=view,
                basemap=basemaps,
                legend=True,
            )

        # close session
        finally:
            session and session.close()
        return map_view, model_extent, layer_groups

    def compose_model_boundary_layer(self, endpoint, boundary_layer, extent, public_name, resource_id, public,
                                     map_view_type=None):
        """
        Compose layer object for the model boundary layer.

        Args:
            endpoint (str): URL of geoserver wms service.
            boundary_layer (str): Geoserver name for the boundary layer
            extent (list): 4-list of boundary extents
            map_view_type (str): 'modflow_model' or 'modflow_selection',
                determines if layer is selectable and has action
        Returns:
            MVLayer: layer object.
        """
        # Create ENV for geoserver styling
        divisions = {'val0': 0, 'val1': 1}
        val_no_data = -15
        env = self.build_param_string(**divisions)
        env += ";val_no_data:{}".format(val_no_data)
        plottable = selectable = has_action = False
        if map_view_type == 'modflow_selection':
            plottable = selectable = has_action = True  # noqa: F841

        # Compose layer
        mv_layer = self.build_wms_layer(
            endpoint=endpoint,
            extent=extent,
            layer_name=boundary_layer,
            layer_title=public_name,
            layer_variable=replace_colon(resource_id),
            env=env,
            visible=True,
            selectable=selectable,
            has_action=has_action,
            plottable=plottable,  # TODO: REMOVE AFTER DONE WITH PLOTTING FEATURE
            geometry_attribute='the_geom',
            public=public
        )

        return mv_layer

    def compose_model_grid_layer(self, endpoint, grid_layer, extent, public_name, resource_id, public):
        """
        Compose layer object for the model boundary layer.

        Args:
            endpoint (str): URL of geoserver wms service.
            boundary_layer (str): Geoserver name for the boundary layer
            extent (list): 4-list of boundary extents
            map_view_type (str): 'modflow_model' or 'modflow_selection',
                determines if layer is selectable and has action
        Returns:
            MVLayer: layer object.
        """
        # Create ENV for geoserver styling
        divisions = {'val0': 0, 'val1': 1}
        val_no_data = -15
        env = self.build_param_string(**divisions)
        env += ";val_no_data:{}".format(val_no_data)

        # Compose layer
        mv_layer = self.build_wms_layer(
            endpoint=endpoint,
            extent=extent,
            layer_name=grid_layer,
            layer_title=public_name,
            layer_variable=replace_colon(resource_id),
            env=env,
            visible=False,
            selectable=False,
            has_action=False,
            plottable=False,
            geometry_attribute='the_geom',
            public=public
        )

        return mv_layer

    def compose_package_layers(self, endpoint, geoserver_name, minimum, maximum, public_name, public, extent=None,
                               visible=False):
        """
        Compose layer object for the model boundary layer.

        Args:
            endpoint (str): URL of geoserver wms service.
            package (str): package name for flopy model
            attribute (str): a layer attribute for the specific package
            maximum (float): maximum value for ramp divisions
            minimum (float): minimum value for ramp divisions
            minimum (float): minimum value for ramp divisions
            extent (list)(optional): 4-list of boundary extents
        Returns:
            MVLayer: layer object.
        """
        # Set scale minimum to 0 is minimum if needed
        divisions = generate_custom_color_ramp_divisions(
            min_value=minimum,
            max_value=maximum,
            num_divisions=10,
            prefix='val',
            first_division=0,
        )
        env = self.build_param_string(**divisions)
        # Compose layer
        # Need to replace space with underscore because html id tag doesn't allow spaces
        mv_layer = self.build_wms_layer(
            endpoint=endpoint,
            layer_name=geoserver_name,
            layer_title=public_name,
            layer_variable=replace_colon(geoserver_name),
            extent=extent,
            env=env,
            visible=visible,
            public=public
        )

        return mv_layer

    def compose_head_raster_layer(self, endpoint, layer, minimum, maximum, public_name, public, extent=None,
                                  visible=False):
        """
        Compose layer object for the model boundary layer.

        Args:
            endpoint (str): URL of geoserver wms service.
            layer_number (int): Head layer number
            extent (list)(optional): 4-list of boundary extents
        Returns:
            MVLayer: layer object.
        """
        # Compute custom divisions
        divisions = self.generate_custom_color_ramp_divisions(
            min_value=minimum,
            max_value=maximum,
            num_divisions=10,
            prefix='val'
        )

        env = self.build_param_string(**divisions)

        # Compose layer
        mv_layer = self.build_wms_layer(
            endpoint=endpoint,
            layer_name=layer,
            layer_title=public_name,
            layer_variable=replace_colon(layer),
            extent=extent,
            env=env,
            visible=visible,
            public=public
        )

        return mv_layer

    def compose_head_contour_layer(self, endpoint, layer_number, extent=None):
        """
        Compose layer object for the model boundary layer.

        Args:
            endpoint (str): URL of geoserver wms service.
            layer_number (int): Head layer number
            extent (list)(optional): 4-list of boundary extents
        Returns:
            MVLayer: layer object.
        """

        # Compose layer name
        layer_name = self.spatial_manager.get_unique_item_name(
            item_name=self.spatial_manager.VL_HEAD_CONTOUR,
            model_file_db=self.model_db,
            with_workspace=True
        )

        # Create layer name based on modflow layer
        layer_name_number = '{}_layer{}'.format(layer_name, layer_number)
        layer_title = "{} Layer {}".format(self.spatial_manager.VL_HEAD_CONTOUR.replace('_', ' '), layer_number).title()
        layer_variable = "{}_layer{}".format(self.spatial_manager.VL_HEAD_CONTOUR, layer_number)
        # Get head data for the modflow model
        head_info = self.spatial_manager.get_head_info()
        maximum = head_info[layer_number]['maximum']
        minimum = head_info[layer_number]['minimum']

        # Compute custom divisions
        divisions = self.generate_custom_color_ramp_divisions(
            min_value=minimum,
            max_value=maximum,
            num_divisions=10,
            prefix='val',
        )

        env = self.build_param_string(**divisions)

        # Compose layer
        mv_layer = self.build_wms_layer(
            endpoint=endpoint,
            layer_name=layer_name_number,
            layer_title=layer_title,
            layer_variable=replace_colon(layer_variable),
            env=env,
            extent=extent,
            visible=False,
            selectable=True,
            plottable=True,  # TODO: REMOVE AFTER DONE WITH PLOTTING FEATURE
        )

        return mv_layer

    def append_layer_results(self):
        pass


def validate_url(url):
    from urllib.parse import urlparse

    result = urlparse(url)
    if result.scheme == '' and result.netloc == '':
        return False
    else:
        return True


def get_public_status(data):
    if 'active' in data:
        status = data['active']
    if status is None:
        status = True
    return status


def generate_custom_color_ramp_divisions(min_value, max_value, num_divisions, first_division=1,
                                         top_offset=0, bottom_offset=0, nodatavalue=0, prefix='val'):
    """
    Generate custom elevation divisions.

    Args:
        min_value(number): minimum value.
        max_value(number): maximum value.
        num_divisison(int): number of divisions.
        first_division(int): first division number (defaults to 1).
        top_offset(number): offset from top of color ramp (defaults to 0).
        bottom_offset(number): offset from bottom of color ramp (defaults to 0).
        prefix(str): name of division variable prefix (i.e.: 'val' for pattern 'val1').

    Returns:
        dict<name, value>: custom divisions
    """
    divisions = {}
    if min_value == max_value:
        divisions['{}{}'.format(prefix, '0')] = min_value
    else:
        # Equation of a Line
        max_div = first_division + num_divisions - 1
        min_div = first_division
        max_val = float(max_value - top_offset)
        min_val = float(min_value + bottom_offset)
        y2_minus_y1 = max_val - min_val
        x2_minus_x1 = max_div - min_div
        m = y2_minus_y1 / x2_minus_x1
        b = max_val - (m * max_div)
        divisions['val_no_data'] = 0
        for i in range(min_div, max_div + 1):
            if abs(max_val) < 1:
                # For data with small range such as recharge, we'll use 5 significant figures
                value = round(m * i + b, 5)
            else:
                if i == max_div:
                    # Have to add a buffer to make sure everything is contour.
                    value = round(m * i + b + 0.01, 2)
                elif i == 0 and min_val < 0.1:
                    # If first value is small, we'll show 4 decimal points.
                    value = round(m * i + b, 4)
                else:
                    value = round(m * i + b, 2)
            divisions['{}{}'.format(prefix, i)] = value

    return divisions


def replace_colon(text):
    if ":" in text:
        text = text.replace(":", "_")
    return text
