"""
********************************************************************************
* Name: modpath_workflow
* Author: ckrewson
* Created On: February 27, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import mock
import unittest
from tethysapp.modflow.condor_workflows.modpath_workflow import ModpathWorkflow


class ModpathWorkflowTests(unittest.TestCase):

    def setUp(self):
        self.user = mock.MagicMock()
        self.session_id = '12345'
        self.lat = '-90'
        self.lon = '-180'
        self.depth = '100'
        self.job_name = 'modpath'
        self.safe_job_name = ''.join(s for s in self.job_name if s.isalnum())  #: Safe name with only A-Z 0-9
        self.xll = '10000'
        self.yll = '-10000'
        self.db_dir = '/fake/path'
        self.workspace = '/fake/path'
        self.model_units = 'feet'
        self.model_version = 'mfnwt'
        self.modflow_exe = '/path/to/exe/mfnwt'
        self.modpath_exe = '/path/to/exe/mp7'
        self.nam_file = 'test.nam'
        self.srid = '2901'
        self.resource_id = '12345'
        self.database_id = '6789'
        self.app_package = 'test'
        self.workflow = None
        self.mw = ModpathWorkflow(workspace=self.workspace, user=self.user, session_id=self.session_id, lat=self.lat,
                                  lon=self.lon, depth=self.depth, xll=self.xll, yll=self.yll, db_dir=self.db_dir,
                                  model_units=self.model_units, model_version=self.model_version,
                                  modflow_exe=self.modflow_exe, modpath_exe=self.modpath_exe, srid=self.srid,
                                  nam_file=self.nam_file, resource_id=self.resource_id, database_id=self.database_id,
                                  app_package=self.app_package)

    def tearDown(self):
        pass

    @mock.patch('tethysapp.modflow.condor_workflows.modpath_workflow.app')
    @mock.patch('tethysapp.modflow.condor_workflows.modpath_workflow.CondorWorkflowJobNode')
    def test_prepare(self, mock_job, mock_app):
        mock_job_manager = mock.MagicMock()
        mock_workflow = mock.MagicMock()
        mock_job_manager.create_job.return_value = mock_workflow
        mock_app.get_job_manager.return_value = mock_job_manager
        self.mw.prepare()
        call_args = mock_job.call_args_list
        self.assertEqual(2, len(call_args[0]))
        self.assertIn('remote_input_files', call_args[0][1])
        self.assertEqual('prepare_modpath_job', call_args[0][1]['name'])
        mock_workflow.save.assert_called()

    @mock.patch('tethysapp.modflow.condor_workflows.modpath_workflow.app')
    def test_run_job(self, _):
        self.mw.prepare = mock.MagicMock()
        self.mw.workflow = mock.MagicMock()
        self.mw.run_job()
        self.mw.prepare.assert_called()
        self.mw.workflow.execute.assert_called()
