"""
********************************************************************************
* Name: geoserver_layers_executable.py
* Author: ckrewson
* Created On: February 27, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import unittest
import mock
import os
import warnings
from tethysapp.modflow.job_executables.update_resource_status import run


class UpdateResourceStatusTests(unittest.TestCase):
    def setUp(self):
        # Somehow running unittest will create resourcewarning unclosed file. Do this to suppress the warning
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)

    def tearDown(self):
        tests_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        test_file_path = os.path.join(tests_dir, 'test_files', '12345')
        if os.path.isfile(os.path.join(test_file_path, 'flow_path.json')):
            os.remove(os.path.join(test_file_path, 'flow_path.json'))
            os.rmdir(test_file_path)

    @mock.patch('tethysapp.modflow.job_executables.update_resource_status.ModflowModelResource')
    @mock.patch('tethysapp.modflow.job_executables.update_resource_status.create_engine')
    @mock.patch('tethysapp.modflow.job_executables.update_resource_status.sessionmaker')
    def test_run_update_resource_status(self, _, __, mock_mmr):
        # define parameters
        workflow = 'upload'
        resource_db_url = 'fake/resource/db/url'
        resource_id = '12345'

        run(workflow, resource_db_url, resource_id)
