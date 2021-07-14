"""
********************************************************************************
* Name: modpath_executable.py
* Author: ckrewson
* Created On: February 27, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import unittest
import os
import shutil
import warnings
from tethysapp.modflow.job_executables.drawdown_executable import run as run_mf
import filecmp


class DrawdownExecutableTests(unittest.TestCase):
    def setUp(self):
        self.tests_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        base_well_file = os.path.join(self.tests_dir, 'test_files', 'test_base.wel')
        new_well_file = os.path.join(self.tests_dir, 'test_files', 'test.wel')
        shutil.copy(base_well_file, new_well_file)
        base_hds_file = os.path.join(self.tests_dir, 'test_files', 'test_base.hds')
        new_hds_file = os.path.join(self.tests_dir, 'test_files', 'test.hds')
        shutil.copy(base_hds_file, new_hds_file)
        self.current_dir = os.getcwd()
        # Somehow running unittest will create resourcewarning unclosed file. Do this to suppress the warning
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)

    def tearDown(self):
        delete_files = ['well_impact.json', 'drawdown_contour.shp',  'drawdown_contour.prj', 'drawdown_contour.dbf',
                        'drawdown_contour.shx']
        for file in delete_files:
            if os.path.isfile(os.path.join(self.current_dir, file)):
                os.remove(os.path.join(self.current_dir, file))

    def test_run_drawdown(self):
        # define parameters
        tests_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        test_file_path = os.path.join(tests_dir, 'test_files')
        exe_name = os.path.join(test_file_path, 'mfnwt')
        modflow_nam = 'test.mfn'
        model_prj = '32612'
        xll = '439760'
        yll = '4452290'
        data_prj = '4326'
        modflow_hds = os.path.join(test_file_path, 'test.hds')
        modflow_wel = os.path.join(test_file_path, 'test.wel')
        contour_levels = "0.01/1"
        run_mf(modflow_exe=exe_name, data_path=test_file_path, modflow_nam=modflow_nam, modflow_hds=modflow_hds,
               modflow_wel=modflow_wel, model_prj=model_prj, xll=xll, yll=yll, geo_prj=data_prj,
               contour_levels=contour_levels)
        sol_file = os.path.join(self.tests_dir, 'test_files', 'drawdown_contour_sol.json')
        output_file = os.path.join(self.current_dir, 'well_impact.json')
        self.assertTrue(filecmp.cmp(sol_file, output_file), 'Drawdown contour json files are not the same')
