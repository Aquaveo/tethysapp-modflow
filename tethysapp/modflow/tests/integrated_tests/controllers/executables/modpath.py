"""
********************************************************************************
* Name: modpath.py
* Author: ckrewson
* Created On: February 27, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import mock
import json
import unittest
from tethysapp.modflow.controllers.executables.modpath import modpath


class ModpathTests(unittest.TestCase):

    def setUp(self):
        self.mock_request = mock.MagicMock(user='admin')

    def tearDown(self):
        pass

    @mock.patch('tethysapp.modflow.controllers.executables.modpath.os')
    @mock.patch('tethysapp.modflow.controllers.executables.modpath.app')
    @mock.patch('tethysapp.modflow.controllers.executables.modpath.json')
    @mock.patch('tethysapp.modflow.controllers.executables.modpath.ModelFileDatabase')
    @mock.patch('tethysapp.modflow.controllers.executables.modpath.ModflowSpatialManager')
    @mock.patch('tethysapp.modflow.controllers.executables.modpath.ModpathWorkflow')
    def test_modpath(self, mock_mw, mock_msm, mock_md, mock_json, mock_app, mock_os):
        mock_lon = '-180'
        mock_lat = '-90'
        mock_resource_id = '6789'
        mock_session_id = '12345'
        mock_depth = '100'
        mock_xll = '100000'
        mock_yll = '-100000'
        mock_model_units = 'feet'
        mock_model_version = 'mfnwt'
        mock_srid = '2901'
        mock_db_id = '54321'
        m_md = mock_md()
        m_md.initialize.return_value = True
        m_md.directory = 'fake/directory'
        mock_app.package = 'test'
        mock_os.path.isfile.return_value = True
        self.mock_request.session.session_key.return_value = mock_session_id
        self.mock_request.POST.get.side_effect = [mock_resource_id, mock_lon, mock_lat, mock_depth]
        mock_session = mock.MagicMock()
        mock_session.query().get.return_value = mock.MagicMock()
        mock_session.query().get().get_attribute.side_effect = [mock_xll, mock_yll, mock_model_units,
                                                                mock_model_version, mock_srid, mock_db_id]
        mock_app.get_persistent_store_database().return_value = mock_session
        mock_engine = mock.MagicMock()
        mock_app.get_spatial_dataset_service.return_value = mock_engine
        mock_msm().EXE_PATH = 'fake/path/to/executables'
        mock_msm().model_file_db.list.return_value = ['test.nam']
        mock_app.get_user_workspace.return_value = mock.MagicMock(path='fake/path/to/user_ws')
        mock_json.load.return_value = 'data'
        self.mock_request.user = mock.MagicMock(username='admin')
        mock_mw().workflow = mock.MagicMock(id='123', remote_id='456')

        ret = modpath(
            request=self.mock_request,
        )

        mock_md.assert_called()
        mock_msm.assert_called()
        mock_mw.asser_called_with(user='admin',
                                  session_id=mock_session_id,
                                  lat=mock_lat,
                                  lon=mock_lon,
                                  depth=mock_depth,
                                  xll=mock_xll,
                                  yll=mock_yll,
                                  db_dir=m_md.directory,
                                  model_units=mock_model_units,
                                  model_version=mock_model_version,
                                  modflow_exe='fake/path/to/executables/mfnwt',
                                  modpath_exe='fake/path/to/executables/mp7',
                                  nam_file='test.nam',
                                  srid=mock_srid,
                                  resource_id=mock_resource_id,
                                  database_id=mock_db_id,
                                  app_package='test',)
        content = json.loads(ret.content.decode('utf-8'))
        self.assertTrue(content['success'])

    # def test_modpath_no_resource_id(self):
    #     mock_lon = '-180'
    #     mock_lat = '-90'
    #     mock_resource_id = None
    #     mock_session_id = '12345'
    #     mock_depth = '100'
    #     self.mock_request.session.session_key.return_value = mock_session_id
    #     self.mock_request.POST.get.side_effect = [mock_resource_id, mock_lon, mock_lat, mock_depth]
    #
    #     ret = modpath(
    #         request=self.mock_request,
    #     )
    #
    #     content = json.loads(ret.content.decode('utf-8'))
    #     self.assertFalse(content['success'])

    # def test_modpath_no_depth(self):
    #     mock_lon = '-180'
    #     mock_lat = '-90'
    #     mock_resource_id = '6789'
    #     mock_session_id = '12345'
    #     mock_depth = None
    #     self.mock_request.session.session_key.return_value = mock_session_id
    #     self.mock_request.POST.get.side_effect = [mock_resource_id, mock_lon, mock_lat, mock_depth]
    #
    #     ret = modpath(
    #         request=self.mock_request,
    #     )
    #
    #     content = json.loads(ret.content.decode('utf-8'))
    #     self.assertFalse(content['success'])

        @mock.patch('tethysapp.modflow.controllers.executables.modpath.os')
        @mock.patch('tethysapp.modflow.controllers.executables.modpath.app')
        @mock.patch('tethysapp.modflow.controllers.executables.modpath.json')
        @mock.patch('tethysapp.modflow.controllers.executables.modpath.ModelFileDatabase')
        @mock.patch('tethysapp.modflow.controllers.executables.modpath.ModflowSpatialManager')
        @mock.patch('tethysapp.modflow.controllers.executables.modpath.ModpathWorkflow')
        def test_modpath_no_json_file(self, mock_mw, mock_msm, mock_md, mock_json, mock_app, mock_os):
            mock_lon = '-180'
            mock_lat = '-90'
            mock_resource_id = '6789'
            mock_session_id = '12345'
            mock_depth = '100'
            mock_xll = '100000'
            mock_yll = '-100000'
            mock_model_units = 'feet'
            mock_model_version = 'mfnwt'
            mock_srid = '2901'
            mock_db_id = '54321'
            m_md = mock_md()
            m_md.initialize.return_value = True
            m_md.directory = 'fake/directory'
            mock_app.package = 'test'
            mock_os.path.isfile.return_value = False
            self.mock_request.session.session_key.return_value = mock_session_id
            self.mock_request.POST.get.side_effect = [mock_resource_id, mock_lon, mock_lat, mock_depth]
            mock_session = mock.MagicMock()
            mock_session.query().get.return_value = mock.MagicMock()
            mock_session.query().get().get_attribute.side_effect = [mock_xll, mock_yll, mock_model_units,
                                                                    mock_model_version, mock_srid, mock_db_id]
            mock_app.get_persistent_store_database().return_value = mock_session
            mock_engine = mock.MagicMock()
            mock_app.get_spatial_dataset_service.return_value = mock_engine
            mock_msm().EXE_PATH = 'fake/path/to/executables'
            mock_msm().model_file_db.list.return_value = ['test.nam']
            mock_app.get_user_workspace.return_value = mock.MagicMock(path='fake/path/to/user_ws')
            mock_json.load.return_value = 'data'

            ret = modpath(
                request=self.mock_request,
            )

            mock_md.assert_called_with(app=mock_app, database_id=mock_db_id)
            mock_msm.assert_called_with(geoserver_engine=mock_engine,
                                        model_file_db_connection=mock_md().model_db_connection,
                                        modflow_version=mock_model_version)
            mock_mw.asser_called_with(user='admin',
                                      session_id=mock_session_id,
                                      lat=mock_lat,
                                      lon=mock_lon,
                                      depth=mock_depth,
                                      xll=mock_xll,
                                      yll=mock_yll,
                                      db_dir=m_md.directory,
                                      model_units=mock_model_units,
                                      model_version=mock_model_version,
                                      modflow_exe='fake/path/to/executables/mfnwt',
                                      modpath_exe='fake/path/to/executables/mp7',
                                      nam_file='test.nam',
                                      srid=mock_srid,
                                      resource_id=mock_resource_id,
                                      database_id=mock_db_id,
                                      app_package='test', )
            content = json.loads(ret.content.decode('utf-8'))
            self.assertFalse(content['success'])
