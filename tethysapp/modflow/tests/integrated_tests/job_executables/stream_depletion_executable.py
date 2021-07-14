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
from tethysapp.modflow.job_executables.stream_depletion_executable import run as run_mf
import filecmp


class StreamDepletionExecutableTests(unittest.TestCase):
    def setUp(self):
        self.tests_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        base_well_file = os.path.join(self.tests_dir, 'test_files', 'test_base.wel')
        new_well_file = os.path.join(self.tests_dir, 'test_files', 'test.wel')
        shutil.copy(base_well_file, new_well_file)
        base_cbb_file = os.path.join(self.tests_dir, 'test_files', 'test_base.cbb')
        self.new_cbb_file = os.path.join(self.tests_dir, 'test_files', 'test.cbb')
        shutil.copy(base_cbb_file, self.new_cbb_file)
        self.current_dir = os.getcwd()
        # Somehow running unittest will create resourcewarning unclosed file. Do this to suppress the warning
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)

    def tearDown(self):
        delete_files = ['well_impact.json', 'streamflowout.json', 'streamleakage.json']
        for file in delete_files:
            if os.path.isfile(os.path.join(self.current_dir, file)):
                os.remove(os.path.join(self.current_dir, file))

    def test_run_stream_depletion_polygon(self):
        # define parameters
        test_file_path = os.path.join(self.tests_dir, 'test_files')
        exe_name = os.path.join(test_file_path, 'mfnwt')
        modflow_nam = 'test.mfn'
        model_prj = '32612'
        xll = '439760'
        yll = '4452290'
        data_prj = '4326'
        modflow_wel = os.path.join(test_file_path, 'test.wel')
        run_mf(modflow_exe=exe_name, data_path=test_file_path, modflow_nam=modflow_nam, modflow_wel=modflow_wel,
               model_prj=model_prj, xll=xll, yll=yll, geo_prj=data_prj, budget_base=self.new_cbb_file,
               shape_type="Polygon", details="All")
        sol_leakgage_file = os.path.join(self.tests_dir, 'test_files', 'streamleakage_sol.json')
        output_leakage_file = os.path.join(self.current_dir, 'streamleakage.json')
        sol_streamflow_file = os.path.join(self.tests_dir, 'test_files', 'streamflowout_sol.json')
        output_streamflow_file = os.path.join(self.current_dir, 'streamflowout.json')

        self.assertTrue(filecmp.cmp(sol_leakgage_file, output_leakage_file), 'Leakage json file has changed')
        self.assertTrue(filecmp.cmp(sol_streamflow_file, output_streamflow_file), 'Leakage json file has changed')
