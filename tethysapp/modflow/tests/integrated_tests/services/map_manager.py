"""
********************************************************************************
* Name: map_manager.py
* Author: ckrewson
* Created On: September 06, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import unittest
import mock
import json
from tethysext.atcore.services.model_file_database import ModelFileDatabase
from modflow_adapter.services.modflow_spatial_manager import ModflowSpatialManager
from tethys_gizmos.gizmo_options import MapView
from modflow_adapter.models.app_users.modflow_model_resource import ModflowModelResource
from tethysapp.modflow.services.map_manager import ModflowMapManager

from tethysapp.modflow.tests import TEST_DB_URL
from sqlalchemy.engine import create_engine
from tethysext.atcore.models.app_users import AppUser, AppUsersBase
from django.test import RequestFactory
from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.tests.factories.django_user import UserFactory
from sqlalchemy.orm.session import Session


def setUpModule():
    global transaction, connection, engine

    # Connect to the database and create the schema within a transaction
    engine = create_engine(TEST_DB_URL)
    connection = engine.connect()
    transaction = connection.begin()
    AppUsersBase.metadata.create_all(connection)


def tearDownModule():
    # Roll back the top level transaction and disconnect from the database
    transaction.rollback()
    connection.close()
    engine.dispose()


class ModflowMapManagerTests(unittest.TestCase):  # TODO: GAGE FIX BROKEN TESTS

    def setUp(self):
        self.mock_spatial_manager = mock.MagicMock(spec=ModflowSpatialManager)
        self.mock_model_db = mock.MagicMock(spec=ModelFileDatabase)
        self.mmm = ModflowMapManager(
            spatial_manager=self.mock_spatial_manager,
            model_db=self.mock_model_db
        )
        self.mmm.spatial_manager.flopy_model = mock.MagicMock()

        self.transaction = connection.begin_nested()
        self.session = Session(connection)
        self.request_factory = RequestFactory()
        self.django_user = UserFactory()
        self.django_user.is_staff = True
        self.django_user.is_superuser = True
        self.django_user.save()
        self.app_user = AppUser(
            username=self.django_user.username,
            role=Roles.ORG_ADMIN,
            is_active=True,
        )
        self.session.add(self.app_user)
        self.request_factory = RequestFactory()

        self.resource = ModflowModelResource(
            name="test_organization"
        )

        self.session.add(self.resource)
        self.database_id = '123456'
        self.resource.set_attribute('database_id', self.database_id)
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()

    def test_get_map_preview_url(self):
        self.mock_spatial_manager.get_unique_item_name.side_effect = [
            'mb_layer', 'mb_style'
        ]
        self.mock_spatial_manager.get_wms_endpoint.return_value = 'mock_endpoint'

        with mock.patch('tethysapp.modflow.services.map_manager.ModflowMapManager.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = [300, 400, 100, 800]  # hw_ratio = 0.5
            mmm = ModflowMapManager(
                spatial_manager=self.mock_spatial_manager,
                model_db=self.mock_model_db
            )

            ret = mmm.get_map_preview_url()

        self.assertIn('mock_endpoint', ret)
        self.assertIn('service=WMS', ret)
        self.assertIn('request=GetMap', ret)
        self.assertIn('layers=mb_layer', ret)
        self.assertIn('styles=mb_style', ret)
        self.assertIn('height=300', ret)
        self.assertIn('width=150', ret)
        self.assertIn('bbox=300,400,100,800', ret)
        self.assertIn('format=image%2Fpng', ret)

    def test_get_map_preview_url_hw_ratio_gt_one(self):
        self.mock_spatial_manager.get_unique_item_name.side_effect = [
            'mb_layer', 'mb_style'
        ]
        self.mock_spatial_manager.get_wms_endpoint.return_value = 'mock_endpoint'

        with mock.patch('tethysapp.modflow.services.map_manager.ModflowMapManager.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = [400, 300, 800, 100]  # hw_ratio = 2.0
            mmm = ModflowMapManager(
                spatial_manager=self.mock_spatial_manager,
                model_db=self.mock_model_db
            )

            ret = mmm.get_map_preview_url()

        self.assertIn('mock_endpoint', ret)
        self.assertIn('service=WMS', ret)
        self.assertIn('request=GetMap', ret)
        self.assertIn('layers=mb_layer', ret)
        self.assertIn('styles=mb_style', ret)
        self.assertIn('height=150', ret)
        self.assertIn('width=300', ret)
        self.assertIn('bbox=400,300,800,100', ret)
        self.assertIn('format=image%2Fpng', ret)

    def test_get_map_preview_url_no_extent(self):
        with mock.patch('tethysapp.modflow.services.map_manager.ModflowMapManager.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.return_value = None
            mmm = ModflowMapManager(
                spatial_manager=self.mock_spatial_manager,
                model_db=self.mock_model_db
            )

            ret = mmm.get_map_preview_url()

        self.assertEqual('', ret)

    @mock.patch('tethysapp.modflow.services.map_manager.log')
    def test_get_map_preview_url_exception(self, mock_log):
        with mock.patch('tethysapp.modflow.services.map_manager.ModflowMapManager.map_extent',
                        new_callable=mock.PropertyMock) as mock_map_extent:
            mock_map_extent.side_effect = Exception
            mmm = ModflowMapManager(
                spatial_manager=self.mock_spatial_manager,
                model_db=self.mock_model_db
            )

            ret = mmm.get_map_preview_url()

        self.assertEqual('', ret)
        mock_log.exception.assert_called()

    @mock.patch('tethysapp.modflow.services.map_manager.app')
    @mock.patch('tethysapp.modflow.services.map_manager.has_permission')
    def test_compose_map_resource(self, mock_perms, mock_app):
        mock_request = mock.MagicMock()
        mock_extent = [-1, -1, 1, 1]
        mock_layer = mock.MagicMock()
        mock_meta = mock.MagicMock()
        mock_view = mock.MagicMock()
        resource_id = '12345'
        map_view_type = 'modflow_model'
        self.mmm.spatial_manager.get_wms_endpoint = mock.MagicMock()
        self.mmm.get_map_extent = mock.MagicMock(return_value=(mock_view, mock_extent))
        self.mmm.compose_package_layers = mock.MagicMock(return_value=(mock_layer, mock_meta))
        self.mmm.compose_head_raster_layer = mock.MagicMock(return_value=(mock_layer, mock_meta))
        self.mmm.compose_model_boundary_layer = mock.MagicMock(return_value=(mock_layer, mock_meta))
        mock_layers = {"Boundary": {"Boundary_layer": {"public_name": 'Boundary_public', "active": True}}}
        mock_groups = {"Model": {"public_name": 'Boundary_public', "active": True}}

        mock_app.get_persistent_store_database()().query().get.return_value = mock.MagicMock(
            _attributes=json.dumps({'geoserver_layers': json.dumps(mock_layers),
                                    'geoserver_groups': json.dumps(mock_groups)}),
            name='test_layer',
            id='654321'
            )

        mock_app.get_custom_setting.return_value = 'mYaP1k3y'
        map_view, model_extent, metadata = self.mmm.compose_map(request=mock_request, resource_id=resource_id)

        self.mmm.spatial_manager.get_wms_endpoint.assert_called()
        self.mmm.compose_model_boundary_layer.assert_called_with(self.mmm.get_wms_endpoint(),
                                                                 "Boundary_layer",
                                                                 model_extent,
                                                                 "Boundary_public",
                                                                 resource_id,
                                                                 True,
                                                                 map_view_type=map_view_type)

        self.assertIsInstance(map_view, MapView)
        self.assertEqual(mock_extent, model_extent)
        self.assertEqual(2, len(metadata))
        self.assertEqual(1, len(map_view['layers']))
        self.assertEqual(mock_view, map_view['view'])
        self.assertEqual(11, len(map_view['basemap']))

    @mock.patch('tethysapp.modflow.services.map_manager.app')
    @mock.patch('tethysapp.modflow.services.map_manager.MVView')
    @mock.patch('tethysapp.modflow.services.map_manager.has_permission')
    def test_compose_map_no_resource(self, mock_perms, mock_view, mock_app):
        mock_request = mock.MagicMock()
        mock_extent = [-90, 90, -180, 180]
        mock_layer = mock.MagicMock()
        mock_meta = mock.MagicMock()
        map_view_type = 'modflow_selection'
        self.mmm.spatial_manager.get_wms_endpoint = mock.MagicMock()
        self.mmm.get_map_extent = mock.MagicMock(return_value=(mock_view, mock_extent))
        self.mmm.compose_model_boundary_layer = mock.MagicMock(return_value=(mock_layer, mock_meta))
        mock_app.get_custom_setting.side_effect = [-90, 90, -180, 180, 'mYaP1k3y']
        mock_attrs = {"database_id": "123456"}
        mock_resource = mock.MagicMock(
            _attributes=json.dumps(mock_attrs),
            name='test_boundary',
            id='654321'
        )
        mock_app.get_persistent_store_database()().query().all.return_value = [mock_resource]

        map_view, model_extent, metadata = self.mmm.compose_map(request=mock_request)

        self.mmm.spatial_manager.get_wms_endpoint.assert_called()
        self.mmm.compose_model_boundary_layer.assert_called_with(self.mmm.get_wms_endpoint(),
                                                                 "{}:{}-{}_{}".format(
                                                                     self.mmm.spatial_manager.WORKSPACE,
                                                                     self.mmm.spatial_manager.WORKSPACE,
                                                                     '123456',
                                                                     self.mmm.spatial_manager.VL_MODEL_BOUNDARY),
                                                                 model_extent,
                                                                 mock_resource.name,
                                                                 mock_resource.id,
                                                                 True,
                                                                 map_view_type=map_view_type)

        self.assertIsInstance(map_view, MapView)
        self.assertEqual(mock_extent, model_extent)
        self.assertEqual(1, len(metadata))
        self.assertEqual(1, len(map_view['layers']))
        self.assertEqual(11, len(map_view['basemap']))

    @mock.patch('tethysapp.modflow.services.map_manager.app')
    @mock.patch('tethysapp.modflow.services.map_manager.MVView')
    @mock.patch('tethysapp.modflow.services.map_manager.has_permission')
    def test_compose_map_resource_no_bing_api_key(self, mock_perms, mock_view, mock_app):
        mock_request = mock.MagicMock()
        mock_extent = [-90, 90, -180, 180]
        mock_layer = mock.MagicMock()
        mock_meta = mock.MagicMock()
        map_view_type = 'modflow_selection'
        self.mmm.spatial_manager.get_wms_endpoint = mock.MagicMock()
        self.mmm.get_map_extent = mock.MagicMock(return_value=(mock_view, mock_extent))
        self.mmm.compose_model_boundary_layer = mock.MagicMock(return_value=(mock_layer, mock_meta))
        mock_app.get_custom_setting.side_effect = [-90, 90, -180, 180, None]
        mock_attrs = {"database_id": "123456"}
        mock_resource = mock.MagicMock(
            _attributes=json.dumps(mock_attrs),
            name='test_boundary',
            id='654321'
        )
        mock_app.get_persistent_store_database()().query().all.return_value = [mock_resource]

        map_view, model_extent, metadata = self.mmm.compose_map(request=mock_request)

        self.mmm.spatial_manager.get_wms_endpoint.assert_called()
        self.mmm.compose_model_boundary_layer.assert_called_with(self.mmm.get_wms_endpoint(),
                                                                 "{}:{}-{}_{}".format(
                                                                     self.mmm.spatial_manager.WORKSPACE,
                                                                     self.mmm.spatial_manager.WORKSPACE,
                                                                     '123456',
                                                                     self.mmm.spatial_manager.VL_MODEL_BOUNDARY),
                                                                 model_extent,
                                                                 mock_resource.name,
                                                                 mock_resource.id,
                                                                 True,
                                                                 map_view_type=map_view_type)

        self.assertIsInstance(map_view, MapView)
        self.assertEqual(mock_extent, model_extent)
        self.assertEqual(1, len(metadata))
        self.assertEqual(1, len(map_view['layers']))
        self.assertEqual(11, len(map_view['basemap']))

    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.build_wms_layer')
    def test_compose_model_boundary_layer_modflow_selection(self, mock_wms):
        self.mmm.spatial_manager.WORKSPACE = 'test'
        endpoint = 'http://www.example.com/geoserver/wms'
        mock_layer = 'test:test-{}-model-boundary'.format(self.database_id)
        mock_public_name = "boundary_public"
        mock_extent = [-1, -1, 1, 1]
        mock_resource_id = '654321'
        expected_value = 'mv_layer'
        mock_wms.return_value = 'mv_layer'
        mv_layer = self.mmm.compose_model_boundary_layer(
            endpoint=endpoint,
            boundary_layer=mock_layer,
            extent=mock_extent,
            public_name=mock_public_name,
            resource_id=mock_resource_id,
            map_view_type='modflow_selection',
            public='checked'
        )

        self.assertEqual(mv_layer, expected_value)
        mock_wms.assert_called_with(endpoint='http://www.example.com/geoserver/wms',
                                    env='val0:0;val1:1;val_no_data:-15', extent=[-1, -1, 1, 1],
                                    geometry_attribute='the_geom', has_action=True,
                                    layer_name='test:test-123456-model-boundary',
                                    layer_title='boundary_public', layer_variable='654321',
                                    plottable=True, public='checked', selectable=True, visible=True)

    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.build_wms_layer')
    def test_compose_model_boundary_layer_modflow_model(self, mock_wms):
        self.mmm.spatial_manager.WORKSPACE = 'test'
        endpoint = 'http://www.example.com/geoserver/wms'
        mock_layer = 'test:test-{}-model-boundary'.format(self.database_id)
        mock_public_name = "boundary_public"
        mock_extent = [-1, -1, 1, 1]
        expected_value = 'mv_layer'
        mock_wms.return_value = expected_value

        mv_layer = self.mmm.compose_model_boundary_layer(
            endpoint=endpoint,
            boundary_layer=mock_layer,
            extent=mock_extent,
            public_name=mock_public_name,
            resource_id=None,
            map_view_type='modflow_model',
            public='checked'
        )

        self.assertEqual(mv_layer, expected_value)
        mock_wms.assert_called_with(endpoint='http://www.example.com/geoserver/wms',
                                    env='val0:0;val1:1;val_no_data:-15', extent=[-1, -1, 1, 1],
                                    geometry_attribute='the_geom', has_action=False,
                                    layer_name='test:test-123456-model-boundary', layer_title='boundary_public',
                                    layer_variable=None, plottable=False, public='checked', selectable=False,
                                    visible=True)

    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.build_wms_layer')
    def test_compose_package_layers(self, mock_wms):
        endpoint = 'http://www.example.com/geoserver/wms'
        mock_gs_name = "DIS_layer"
        mock_public_name = 'DIS_public'
        mock_min = 0
        mock_max = 100
        mock_extent = [-1, -1, 1, 1]
        expected_value = 'mv_layer'
        mock_wms.return_value = 'mv_layer'
        mv_layer = self.mmm.compose_package_layers(
            endpoint=endpoint,
            geoserver_name=mock_gs_name,
            maximum=mock_min,
            minimum=mock_max,
            public_name=mock_public_name,
            extent=mock_extent,
            public='checked'
        )
        self.assertEqual(expected_value, mv_layer)
        mock_wms.assert_called_with(endpoint='http://www.example.com/geoserver/wms',
                                    env='val_no_data:0;val0:100.0;val1:88.88889;val2:77.77778;val3:66.66667;'
                                        'val4:55.55556;val5:44.44444;val6:33.33333;val7:22.22222;val8:11.11111;'
                                        'val9:0.0', extent=[-1, -1, 1, 1], layer_name='DIS_layer',
                                    layer_title='DIS_public', layer_variable='DIS_public', public='checked',
                                    visible=False)

    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.build_wms_layer')
    def test_compose_package_layers_resource_negative_minimum(self, mock_wms):
        endpoint = 'http://www.example.com/geoserver/wms'
        mv_layer_expected = 'wms_mv_layer'
        mock_wms.return_value = mv_layer_expected
        mv_layer = self.mmm.compose_package_layers(
            endpoint=endpoint,
            geoserver_name='DIS_layer',
            maximum=0,
            minimum=10,
            public_name='DIS_Public',
            public='checked'
        )

        self.assertEqual(mv_layer_expected, mv_layer)

    @mock.patch('tethysext.atcore.services.map_manager.MapManagerBase.build_wms_layer')
    def test_compose_head_raster_layer(self, mock_wms):
        endpoint = 'http://www.example.com/geoserver/wms'
        mock_gs_name = "Head_layer"
        mock_public_name = 'Head_public'
        mock_min = 0
        mock_max = 100
        mock_extent = [-1, -1, 1, 1]
        mv_layer_expected = 'wms_mv_layer'
        mock_wms.return_value = mv_layer_expected
        mv_layer = self.mmm.compose_head_raster_layer(
            endpoint=endpoint,
            layer=mock_gs_name,
            maximum=mock_min,
            minimum=mock_max,
            public_name=mock_public_name,
            extent=mock_extent,
            public='checked'
        )

        self.assertEqual(mv_layer, mv_layer_expected)
        mock_wms.assert_called_with(endpoint='http://www.example.com/geoserver/wms',
                                    env='val1:100.00000;val2:88.88889;val3:77.77778;val4:66.66667;val5:55.55556;'
                                        'val6:44.44444;val7:33.33333;val8:22.22222;val9:11.11111;val10:0.00000',
                                    extent=[-1, -1, 1, 1], layer_name='Head_layer', layer_title='Head_public',
                                    layer_variable='Head_public', public='checked', visible=False)
