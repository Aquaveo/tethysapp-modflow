"""
********************************************************************************
* Name: modpath_executable.py
* Author: ckrewson
* Created On: February 27, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import unittest
import flopy
import os
import shutil
import warnings
from tethysapp.modflow.job_executables.modpath_executable import transform, modpath_cell_prop, run as run_mp


class ModpathExecutableTests(unittest.TestCase):
    def setUp(self):
        self.tests_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        base_well_file = os.path.join(self.tests_dir, 'test_files', 'test_base.wel')
        new_well_file = os.path.join(self.tests_dir, 'test_files', 'test.wel')
        shutil.copy(base_well_file, new_well_file)
        base_head_file = os.path.join(self.tests_dir, 'test_files', 'test_base.hds')
        new_head_file = os.path.join(self.tests_dir, 'test_files', 'test.wel')
        shutil.copy(base_head_file, new_head_file)
        base_cbb_file = os.path.join(self.tests_dir, 'test_files', 'test_base.cbb')
        new_cbb_file = os.path.join(self.tests_dir, 'test_files', 'test.cbb')
        shutil.copy(base_cbb_file, new_cbb_file)
        # Somehow running unittest will create resourcewarning unclosed file. Do this to suppress the warning
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)

    def tearDown(self):
        if os.path.isfile(os.path.join(self.tests_dir, 'flow_path.json')):
            os.remove(os.path.join(self.tests_dir, 'flow_path.json'))

    def test_run_modpath(self):
        # define parameters
        test_file_path = os.path.join(self.tests_dir, 'test_files')
        exe_name = os.path.join(test_file_path, 'mfnwt')
        exe_mp_name = os.path.join(test_file_path, 'mp7')
        modflow_nam = 'test.mfn'
        model_prj = '32612'
        xll = '439760'
        yll = '4452290'
        lon = -111.658531
        lat = 40.233845
        data_prj = '4326'
        depth = 1
        depth_field = 'Depth'
        session_id = '12345'
        workflow_id = '678910'
        user_ws = test_file_path

        run_mp(workflow_id=workflow_id, session_id=session_id, user_ws=user_ws, modflow_exe=exe_name,
               modpath_exe=exe_mp_name, modpath_version='modpath7', data_path=test_file_path, modflow_nam=modflow_nam,
               model_epsg=model_prj, xll=xll, yll=yll, lon=lon, lat=lat, depth=depth, geo_prj=data_prj,
               depth_field=depth_field)

        self.assertFalse(os.path.isfile(os.path.join(test_file_path, '12345', 'flow_path.json')))

    def test_run_modpath_wrong_depth_field(self):
        # define parameters
        test_file_path = os.path.join(self.tests_dir, 'test_files')
        exe_name = os.path.join(test_file_path, 'mfnwt')
        exe_mp_name = os.path.join(test_file_path, 'mp7')
        modflow_nam = 'test.mfn'
        model_prj = '32612'
        xll = '439760'
        yll = '4452290'
        lon = -111.658531
        lat = 40.233845
        data_prj = '4326'
        depth = 1
        depth_field = 'Depth_Wrong'
        session_id = '12345'
        workflow_id = '678910'
        user_ws = test_file_path

        run_mp(workflow_id=workflow_id, session_id=session_id, user_ws=user_ws, modflow_exe=exe_name,
               modpath_exe=exe_mp_name, modpath_version='modpath7', data_path=test_file_path, modflow_nam=modflow_nam,
               model_epsg=model_prj, xll=xll, yll=yll, lon=lon, lat=lat, depth=depth, geo_prj=data_prj,
               depth_field=depth_field)

        self.assertFalse(os.path.isfile(os.path.join(test_file_path, '12345', 'flow_path.json')))

    def test_run_modpath_outside_model(self):
        # define parameters
        test_file_path = os.path.join(self.tests_dir, 'test_files')
        exe_name = os.path.join(test_file_path, 'mfnwt')
        exe_mp_name = os.path.join(test_file_path, 'mp7')
        modflow_nam = 'test.mfn'
        model_prj = '2901'
        xll = 1281239.1093863
        yll = 591339.76535665
        lon = -112.031998
        lat = 46.199763
        data_prj = '4326'
        depth = 100
        depth_field = 'Depth'
        session_id = '12345'
        workflow_id = '678910'
        user_ws = test_file_path

        self.assertRaises(
            Exception,
            run_mp,
            workflow_id=workflow_id, session_id=session_id, user_ws=user_ws, modflow_exe=exe_name,
            modpath_exe=exe_mp_name, modpath_version='modpath7', data_path=test_file_path, modflow_nam=modflow_nam,
            model_epsg=model_prj, xll=xll, yll=yll, lon=lon, lat=lat, depth=depth, geo_prj=data_prj,
            depth_field=depth_field
        )

    def test_modpath_cell_prop(self):
        test_file_path = os.path.join(self.tests_dir, 'test_files')
        exe_name = os.path.join(test_file_path, 'mfnwt')
        modflow_nam = 'test.mfn'
        model_prj = '32612'
        xll = '439760'
        yll = '4452290'
        lon = -111.658531
        lat = 40.233845
        data_prj = '4326'
        depth = 1
        base_name = os.path.splitext(modflow_nam)[0]
        head_file = os.path.join(test_file_path, base_name + '.hds')
        head = flopy.utils.HeadFile(head_file)
        ml = flopy.modflow.Modflow.load(modflow_nam, model_ws=test_file_path, check=False, exe_name=exe_name)
        prj = flopy.utils.reference.getproj4(model_prj)
        sr = flopy.utils.reference.SpatialReference(delr=ml.dis.delr, delc=ml.dis.delc, xll=float(xll),
                                                    yll=float(yll), proj4_str=prj)
        ml.sr = sr
        x, y = transform(lon, lat, data_prj, model_prj)
        cell_prop = modpath_cell_prop(ml, head, float(x), float(y), float(depth))

        self.assertEqual(cell_prop, [4, 7, 0.6867099560942257, 0.3801875244365028, 0.577812910079956])

    def test_modpath_cell_prop_too_deep(self):
        test_file_path = os.path.join(self.tests_dir, 'test_files')
        exe_name = os.path.join(test_file_path, 'mfnwt')
        modflow_nam = 'test.mfn'
        model_prj = '32612'
        xll = '439760'
        yll = '4452290'
        lon = -111.658531
        lat = 40.233845
        data_prj = '4326'
        depth = 100000
        base_name = os.path.splitext(modflow_nam)[0]
        head_file = os.path.join(test_file_path, base_name + '.hds')
        head = flopy.utils.HeadFile(head_file)
        ml = flopy.modflow.Modflow.load(modflow_nam, model_ws=test_file_path, check=False, exe_name=exe_name)
        prj = flopy.utils.reference.getproj4(model_prj)
        sr = flopy.utils.reference.SpatialReference(delr=ml.dis.delr, delc=ml.dis.delc, xll=float(xll),
                                                    yll=float(yll), proj4_str=prj)
        ml.sr = sr
        x, y = transform(lon, lat, data_prj, model_prj)
        cell_prop = modpath_cell_prop(ml, head, float(x), float(y), float(depth))

        self.assertEqual(cell_prop, [4, 7, 0.6867099560942257, 0.3801875244365028, 0.0])

    def test_transform(self):
        model_prj = '32612'
        lon = -111.658531
        lat = 40.233845
        data_prj = '4326'
        x, y = transform(lon, lat, data_prj, model_prj)

        self.assertEqual(x, 443980.00376589573)
        self.assertEqual(y, 4453920.196819904)

    def test_transform_proj4(self):
        model_prj = '+proj=utm +zone=12 +ellps=WGS84 +datum=WGS84 +units=m +no_defs '
        lon = -111.658531
        lat = 40.233845
        data_prj = '+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs '
        x, y = transform(lon, lat, data_prj, model_prj)

        self.assertEqual(x, 443980.00376589573)
        self.assertEqual(y, 4453920.196819904)
