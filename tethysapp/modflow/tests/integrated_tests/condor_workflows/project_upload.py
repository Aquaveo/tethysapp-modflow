"""
********************************************************************************
* Name: project_upload
* Author: nswain
* Created On: July 31, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import mock
import unittest
from modflow_adapter.models.app_users.modflow_model_resource import ModflowModelResource
from tethysapp.modflow.condor_workflows.project_upload import ProjectUploadWorkflow


class ProjectUploadTests(unittest.TestCase):

    def setUp(self):
        self.user = mock.MagicMock()
        self.workspace = 'condor/workspace'
        self.workflow_name = 'workflow_name'
        self.input_archive_path = '/tmp/abc.zip'
        self.srid = 1001
        self.xll = 100
        self.yll = 200
        self.model_units = 'feet'
        self.model_version = 'mfnwt'
        self.resource_db_url = 'postgresql://admin:pass@localhost:5432/modflow_res.db'
        self.resource_id = '2323'
        self.scenario_id = 1
        self.model_db = mock.MagicMock()
        self.gs_engine = mock.MagicMock()
        self.app_package = 'test'
        self.puw = ProjectUploadWorkflow(user=self.user, workspace=self.workspace, workflow_name=self.workflow_name,
                                         input_archive_path=self.input_archive_path, xll=self.xll,
                                         yll=self.yll, model_units=self.model_units, model_version=self.model_version,
                                         srid=self.srid, resource_db_url=self.resource_db_url,
                                         resource_id=self.resource_id, scenario_id=self.scenario_id,
                                         model_db=self.model_db, gs_engine=self.gs_engine, app_package=self.app_package)

    def tearDown(self):
        pass

    @mock.patch('tethysapp.modflow.condor_workflows.project_upload.app')
    @mock.patch('tethysapp.modflow.condor_workflows.project_upload.CondorWorkflowJobNode')
    def test_prepare(self, mock_job, mock_app):
        mock_job_manager = mock.MagicMock()
        mock_workflow = mock.MagicMock()
        mock_job_manager.create_job.return_value = mock_workflow
        mock_app.get_job_manager.return_value = mock_job_manager
        self.puw.prepare()
        call_args = mock_job.call_args_list
        self.assertEqual(2, len(call_args[0]))
        self.assertIn('attributes', call_args[0][1])
        self.assertIn('remote_input_files', call_args[0][1])
        self.assertEqual('prepare_geoserver_layer_job', call_args[0][1]['name'])
        mock_workflow.save.assert_called()

    @mock.patch('tethysapp.modflow.condor_workflows.project_upload.create_engine')
    @mock.patch('tethysapp.modflow.condor_workflows.project_upload.sessionmaker')
    def test_run_job(self, mock_sessionmaker, _):
        mock_session = mock_sessionmaker()()
        mock_resource = mock_session.query().get()
        self.puw.prepare = mock.MagicMock()
        self.puw.workflow = mock.MagicMock()

        self.puw.run_job()

        mock_resource.set_status.assert_called_with(ModflowModelResource.ROOT_STATUS_KEY,
                                                    ModflowModelResource.STATUS_PENDING)
        mock_session.commit.assert_called()
        mock_session.close.assert_called()
        self.puw.prepare.assert_called()
        self.puw.workflow.execute.assert_called()
