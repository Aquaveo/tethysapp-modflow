"""
********************************************************************************
* Name: modflow_model_map_view.py
* Author: ckrewson
* Created On: January 30, 2019
* Copyright: (c) Aquaveo 2019s
********************************************************************************
"""
import mock

from django.test import RequestFactory
from sqlalchemy.orm.session import Session
from tethys_sdk.testing import TethysTestCase
from tethys_sdk.base import TethysAppBase
from tethysapp.modflow.controllers.map_view.modflow_model_map_view import ModflowModelMapView
from tethysext.atcore.models.app_users import AppUser, Organization, Resource, AppUsersBase

from sqlalchemy.engine import create_engine
from tethysapp.modflow.tests import TEST_DB_URL


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


class ModflowModelMapViewTests(TethysTestCase):

    def setUp(self):
        self.database_name = 'primary_db'
        self.geoserver_name = 'primary_gs'
        self.transaction = connection.begin_nested()
        self.session = Session(connection)
        self.mock_app = mock.MagicMock(spec=TethysAppBase)
        self.mock_resource = mock.MagicMock()
        self.mv = ModflowModelMapView(
            _app=self.mock_app,
            _AppUser=mock.MagicMock(spec=AppUser),
            _Organization=mock.MagicMock(spec=Organization),
            _Resource=mock.MagicMock(spec=Resource),
            geoserver_name=self.geoserver_name,
            _persistent_store_name=self.database_name,
        )
        self.request_factory = RequestFactory()

    def tearDown(self):
        self.session.close()
        self.transaction.rollback()

    # @mock.patch('tethysapp.modflow.controllers.map_view.modflow_model_map_view.ModelFileDatabaseConnection')
    # @mock.patch('tethysapp.modflow.controllers.map_view.modflow_model_map_view.ModflowSpatialManager')
    # @mock.patch('tethysapp.modflow.controllers.map_view.modflow_model_map_view.ModflowMapManager')
    # def test_get_managers_no_resource(self, mock_mmm, mock_msm, mock_mfdb):
    #     mock_request = self.request_factory.get('/foo/bar/map-view/')
    #     self.mock_app.get_app_workspace.return_value = mock.MagicMock(path='/fake/path')
    #
    #     self.mv.get_managers(
    #         request=mock_request,
    #         resource=None,
    #     )
    #
    #     mock_mmm.assert_called()
    #     mock_mfdb.assert_called()
    #     mock_msm.assert_called()
    #
    #     md_call_args = mock_mfdb.call_args_list
    #     self.assertEqual('/fake/path', md_call_args[0][1]['db_dir'])
    #
    # @mock.patch('tethysapp.modflow.controllers.map_view.modflow_model_map_view.ModelFileDatabase')
    # @mock.patch('tethysapp.modflow.controllers.map_view.modflow_model_map_view.ModflowSpatialManager')
    # @mock.patch('tethysapp.modflow.controllers.map_view.modflow_model_map_view.ModflowMapManager')
    # def test_get_managers_resource(self, mock_mmm, mock_msm, mock_mfd):
    #     mock_request = self.request_factory.get('/foo/bar/map-view/')
    #     mock_attrs = ['mfnwr', '12345']
    #     mock_resource = mock.MagicMock()
    #     mock_resource.get_attribute.side_effect = mock_attrs
    #
    #     mock_msm.flopy_model.return_value = True
    #
    #     self.mv.get_managers(
    #         request=mock_request,
    #         resource=mock_resource
    #     )
    #
    #     mock_mmm.assert_called()
    #     mock_mfd.assert_called()
    #     mock_msm.assert_called()

    # def test_get_context_resource(self):
    #     mock_request = self.request_factory.get('/foo/bar/map-view/')
    #     mock_context = {'layer_groups': [{
    #                         'layers': [{
    #                              'legend_title': 'test_legend_title',
    #                              'options': {
    #                                  'params': {
    #                                      'ENV': 'val0:0;val_no_data:-10'
    #                                  }
    #                              }
    #                         }]
    #                     }]}
    #     mock_db = mock.MagicMock()
    #     mock_map_manager = mock.MagicMock()
    #     mock_resource = mock.MagicMock()
    #     mock_session = mock.MagicMock()
    #     resource_id = '12345'
    #     self.mv.get_context(
    #         request=mock_request,
    #         session=mock_session,
    #         context=mock_context,
    #         resource=mock_resource,
    #         resource_id=resource_id,
    #         model_db=mock_db,
    #         map_manager=mock_map_manager
    #     )
    #
    #     self.assertIn('legend', mock_context)
    #     self.assertIn('test_legend_title', mock_context['legend'])
    #     self.assertIn(0.0, mock_context['legend']['test_legend_title'])

    # @mock.patch('/home/hoangtran/tethysext-atcore/tethysext/atcore/controllers/map_view.py:41')
    # @mock.patch('tethysext.atcore.services.model_file_database_connection.ModelFileDatabaseConnection')
    # def test_get_context_no_resource(self, mock_msm):
    #     mock_request = self.request_factory.get('/foo/bar/map-view/')
    #     mock_context = {}
    #     mock_db = mock.MagicMock()
    #     mock_resource = None
    #     mock_session = mock.MagicMock()
    #     self.mock_app.get_app_workspace.return_value = mock.MagicMock(path="test_path")
    #     self.mv.get_context(
    #         request=mock_request,
    #         session=mock_session,
    #         context=mock_context,
    #         resource=mock_resource,
    #         model_db=mock_db,
    #     )
    #
    #     self.assertIsNotNone(self.mv.template_name)
    #     self.assertIsNotNone(self.mv.map_title)

    @mock.patch('tethysapp.modflow.controllers.map_view.modflow_model_map_view.reverse')
    def test_default_back_url(self, mock_reverse):
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        self.mv.default_back_url(
            request=mock_request
        )

        call_args = mock_reverse.call_args_list
        self.assertEqual('modflow:home', call_args[0][0][0])

    @mock.patch('tethysapp.modflow.controllers.map_view.modflow_model_map_view.has_permission')
    def test_get_permissions_admin_view_all_resources(self, mock_hp):
        mock_hp.side_effect = [True, True]
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_permissions = {'admin_user': False, 'can_use_plot': False, 'can_use_geocode': False, 'can_view': False}
        mock_db = mock.MagicMock()
        mock_mm = mock.MagicMock()

        self.mv.get_permissions(
            request=mock_request,
            permissions=mock_permissions,
            model_db=mock_db,
            map_manager=mock_mm
        )

        mock_hp.assert_called()
        self.assertTrue(mock_permissions['can_use_plot'])
        self.assertTrue(mock_permissions['can_use_geocode'])
        self.assertTrue(mock_permissions['can_view'])
        self.assertTrue(mock_permissions['admin_user'])

    @mock.patch('tethysapp.modflow.controllers.map_view.modflow_model_map_view.has_permission')
    def test_get_permissions_view_all_resources(self, mock_hp):
        mock_hp.side_effect = [False, True]
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_permissions = {'admin_user': False, 'can_use_plot': False, 'can_use_geocode': False, 'can_view': False}
        mock_db = mock.MagicMock()
        mock_mm = mock.MagicMock()

        self.mv.get_permissions(
            request=mock_request,
            permissions=mock_permissions,
            model_db=mock_db,
            map_manager=mock_mm
        )

        mock_hp.assert_called()
        self.assertTrue(mock_permissions['can_use_plot'])
        self.assertTrue(mock_permissions['can_use_geocode'])
        self.assertTrue(mock_permissions['can_view'])
        self.assertFalse(mock_permissions['admin_user'])

    @mock.patch('tethysapp.modflow.controllers.map_view.modflow_model_map_view.has_permission')
    def test_get_permissions_no_view_all_resources(self, mock_hp):
        mock_hp.side_effect = [False, False]
        mock_request = self.request_factory.get('/foo/bar/map-view/')
        mock_permissions = {'admin_user': False, 'can_use_plot': False, 'can_use_geocode': False, 'can_view': False}
        mock_db = mock.MagicMock()
        mock_mm = mock.MagicMock()

        self.mv.get_permissions(
            request=mock_request,
            permissions=mock_permissions,
            model_db=mock_db,
            map_manager=mock_mm
        )

        mock_hp.assert_called()
        self.assertFalse(mock_permissions['can_use_plot'])
        self.assertFalse(mock_permissions['can_use_geocode'])
        self.assertFalse(mock_permissions['can_view'])
        self.assertFalse(mock_permissions['admin_user'])
