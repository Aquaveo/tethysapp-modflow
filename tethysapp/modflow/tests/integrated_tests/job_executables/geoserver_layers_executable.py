"""
********************************************************************************
* Name: geoserver_layers_executable.py
* Author: ckrewson and htran
* Created On: February 27, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import unittest
import mock
import os
import warnings
from tethysapp.modflow.job_executables.geoserver_layers_executable import run


class GeoserverLayersExecutableTests(unittest.TestCase):
    def setUp(self):
        # Somehow running unittest will create resourcewarning unclosed file. Do this to suppress the warning
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)

    def tearDown(self):
        tests_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        test_file_path = os.path.join(tests_dir, 'test_files', '12345')
        if os.path.isfile(os.path.join(test_file_path, 'flow_path.json')):
            os.remove(os.path.join(test_file_path, 'flow_path.json'))
            os.rmdir(test_file_path)

    @mock.patch('tethysapp.modflow.job_executables.geoserver_layers_executable.ModelFileDatabaseConnection')
    @mock.patch('tethysapp.modflow.job_executables.geoserver_layers_executable.GeoServerSpatialDatasetEngine')
    @mock.patch('tethysapp.modflow.job_executables.geoserver_layers_executable.ModflowSpatialManager')
    @mock.patch('tethysapp.modflow.job_executables.geoserver_layers_executable.create_engine')
    @mock.patch('tethysapp.modflow.job_executables.geoserver_layers_executable.sessionmaker')
    def test_run_geoserver_layer_executable(self, _, __, mock_msm, mock_gs, mock_mfdc):
        # define parameters
        resource_db_url = 'fake/resource/db/url'
        resource_id = '12345'
        db_url = 'fake/db/url'
        xll = '100000'
        yll = '200000'
        model_units = 'feet'
        model_version = 'mfnwt'
        srid = '2901'
        minx = '-180'
        maxx = '180'
        miny = '-90'
        maxy = '90'
        geoserver_endpoint = 'fake/endpoint'
        geoserver_public_endpoint = 'fake/endpoint'
        geoserver_username = 'test'
        geoserver_password = 'test'
        geoserver_job_type = 'ALL'
        status_key = 'PENDING'

        run(resource_db_url, resource_id, db_url, xll, yll, model_units, model_version, srid, minx, maxx, miny, maxy,
            geoserver_endpoint, geoserver_public_endpoint, geoserver_username, geoserver_password, geoserver_job_type,
            status_key)

    @mock.patch('tethysapp.modflow.job_executables.geoserver_layers_executable.ModelFileDatabaseConnection')
    @mock.patch('tethysapp.modflow.job_executables.geoserver_layers_executable.GeoServerSpatialDatasetEngine')
    @mock.patch('tethysapp.modflow.job_executables.geoserver_layers_executable.ModflowSpatialManager')
    @mock.patch('tethysapp.modflow.job_executables.geoserver_layers_executable.create_engine')
    @mock.patch('tethysapp.modflow.job_executables.geoserver_layers_executable.sessionmaker')
    def test_run_geoserver_layer_executable_meters(self, _, __, mock_msm, mock_gs, mock_mfdc):
        # define parameters
        resource_db_url = 'fake/resource/db/url'
        resource_id = '12345'
        db_url = 'fake/db/url'
        xll = '100000'
        yll = '200000'
        model_units = 'meters'
        model_version = 'mfnwt'
        srid = '2901'
        minx = '-180'
        maxx = '180'
        miny = '-90'
        maxy = '90'
        geoserver_endpoint = 'fake/endpoint'
        geoserver_public_endpoint = 'fake/endpoint'
        geoserver_username = 'test'
        geoserver_password = 'test'
        geoserver_job_type = 'ALL'
        status_key = 'PENDING'

        run(resource_db_url, resource_id, db_url, xll, yll, model_units, model_version, srid, minx, maxx, miny, maxy,
            geoserver_endpoint, geoserver_public_endpoint, geoserver_username, geoserver_password, geoserver_job_type,
            status_key)
