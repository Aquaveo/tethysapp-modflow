"""
********************************************************************************
* Name: modify_modflow_model.py
* Author: ckrewson
* Created On: JFebruary 27, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import mock
import unittest
from tethysapp.modflow.controllers.resources.modify_modflow_model import ModifyModflowModel
from tethysext.atcore.exceptions import ModelDatabaseInitializationError


class ModifyModflowModelTests(unittest.TestCase):

    def setUp(self):
        self.mmm_controller = ModifyModflowModel()
        self.mock_session = mock.MagicMock()
        self.mock_request = mock.MagicMock()
        self.mock_app_user = mock.MagicMock()
        self.mock_resource = mock.MagicMock()

    def tearDown(self):
        pass

    # @mock.patch('tethysapp.modflow.controllers.resources.modify_modflow_model.os')
    # @mock.patch('tethysapp.modflow.controllers.resources.modify_modflow_model.log')
    # @mock.patch('tethysapp.modflow.controllers.resources.modify_modflow_model.app')
    # @mock.patch('tethysapp.modflow.controllers.resources.modify_modflow_model.ProjectUploadWorkflow')
    # @mock.patch('tethysapp.modflow.controllers.resources.modify_modflow_model.ModelFileDatabase')
    # @mock.patch('tethysapp.modflow.controllers.resources.modify_modflow_model.ModflowSpatialManager')
    # def test_handle_resource_finished_processing(self, mock_msm, mock_md, mock_puw, mock_app, mock_log, mock_os):
    #     m_md = mock_md()
    #     m_md.initialize.return_value = True
    #     mock_os.path.exists.return_value = False
    #     mock_app = mock.MagicMock()
    #     self.mmm_controller.geoserver_name = 'gs_name'
    #     self.mmm_controller._app = mock_app
    #     mock_msm().create_extent_for_project.return_value = [180, 90]
    #     self.mock_request.POST.get.side_effect = ['100', '200', 'feet', 'mfnwt']
    #     self.mock_session.query().get.return_value = mock.MagicMock()
    #     mock_layers = {"geoserver_layers": {"Boundary":
    #                    {"Boundary_layer":
    #                     {"public_name": 'Boundary_public', "minimum": 0, "maximum": 100, "active": True}}
    #                    }}
    #     mock_groups = {"geoserver_groups": {"Boundary": {"public_name": 'Boundary_public', "active": True}}}
    #     mock_msm().upload_all_layer_names_to_db.return_value = mock_layers, mock_groups
    #
    #     self.mmm_controller.handle_resource_finished_processing(
    #         session=self.mock_session,
    #         request=self.mock_request,
    #         request_app_user=self.mock_app_user,
    #         resource=self.mock_resource,
    #         editing=False
    #     )
    #
    #     self.mock_resource.set_attribute.assert_called()
    #     mra_call_args = self.mock_resource.set_attribute.call_args_list
    #     self.assertEqual('xll', mra_call_args[0][0][0])
    #     self.assertEqual(100.0, mra_call_args[0][0][1])
    #     self.assertEqual('yll', mra_call_args[1][0][0])
    #     self.assertEqual(200.0, mra_call_args[1][0][1])
    #     self.assertEqual('model_units', mra_call_args[2][0][0])
    #     self.assertEqual('feet', mra_call_args[2][0][1])
    #     self.assertEqual('model_version', mra_call_args[3][0][0])
    #     self.assertEqual('mfnwt', mra_call_args[3][0][1])
    #     self.mock_session.commit.assert_called()
    #
    #     mock_puw.assert_called()
    #     mock_puw_call_args = mock_puw.call_args_list
    #
    #     self.assertEqual(self.mock_request.user, mock_puw_call_args[0][1]['user'])
    #     self.assertEqual(self.mock_resource.name, mock_puw_call_args[0][1]['workflow_name'])
    #     self.assertEqual(self.mock_resource.get_attribute(), mock_puw_call_args[0][1]['srid'])
    #     self.assertEqual(str(self.mock_resource.id), mock_puw_call_args[0][1]['resource_id'])
    #     self.assertEqual(1, mock_puw_call_args[0][1]['scenario_id'])
    #     self.assertEqual(m_md, mock_puw_call_args[0][1]['model_db'])
    #
    #     mock_puw().run_job.assert_called()
    #     mock_log.info.assert_called()
    #     self.mock_session.close.assert_not_called()

    @mock.patch('tethysapp.modflow.controllers.resources.modify_modflow_model.app')
    @mock.patch('tethysapp.modflow.controllers.resources.modify_modflow_model.ModelFileDatabase')
    def test_handle_resource_finished_processing_initialize_error(self, mock_mfd, _):
        m_md = mock_mfd()
        m_md.initialize.return_value = False
        self.assertRaises(
            ModelDatabaseInitializationError,
            self.mmm_controller.handle_resource_finished_processing,
            session=self.mock_session,
            request=self.mock_request,
            request_app_user=self.mock_app_user,
            resource=self.mock_resource,
            editing=False
        )

    def test_handle_resource_finished_processing_invalid(self):
        self.mock_request.POST.get.side_effect = [None, None, None, None]
        self.mock_session.query().get.return_value = mock.MagicMock()
        self.assertRaises(
            Exception,
            self.mmm_controller.handle_resource_finished_processing,
            session=self.mock_session,
            request=self.mock_request,
            request_app_user=self.mock_app_user,
            resource=self.mock_resource,
            editing=False
        )

    @mock.patch('tethysapp.modflow.controllers.resources.modify_modflow_model.SelectInput')
    @mock.patch('tethysapp.modflow.controllers.resources.modify_modflow_model.TextInput')
    def test_get_context(self, mock_ti, mock_si):
        mock_context = {}
        ret = self.mmm_controller.get_context(
            context=mock_context
        )

        mock_ti.assert_called()
        mock_si.assert_called()
        self.assertEqual(len(ret), 7)
