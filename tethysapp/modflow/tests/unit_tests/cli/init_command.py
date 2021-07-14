"""
********************************************************************************
* Name: init_command
* Author: ckrewson and mlebaron
* Created On: November 14, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import mock
import unittest
import tethysapp.modflow.cli.init_command as init_command
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class InitCommandTests(unittest.TestCase):

    def setUp(self):
        self.mock_arguments = mock.MagicMock(gsurl="http://admin:geoserver@localhost:8181/geoserver/rest")

    def tearDown(self):
        pass

    @mock.patch('tethysapp.modflow.cli.init_command.GeoServerSpatialDatasetEngine')
    @mock.patch('tethysapp.modflow.cli.init_command.ModflowSpatialManager')
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_init(self, mock_print, mock_gsm, _):
        init_command.init_modflow(self.mock_arguments)
        print_value = mock_print.getvalue()
        mock_gsm().create_workspace.assert_called()
        mock_gsm().create_all_styles.called_with(overwrite=True)
        self.assertIn("Successfully initialized Modflow GeoServer workspace", print_value)
        self.assertIn("Successfully initialized Modflow GeoServer styles.", print_value)
        self.assertIn("Successfully initialized Modflow.", print_value)

    @mock.patch('tethysapp.modflow.cli.init_command.GeoServerSpatialDatasetEngine')
    @mock.patch('tethysapp.modflow.cli.init_command.ModflowSpatialManager')
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_init_workspace_error(self, mock_print, mock_gsm, _):
        mock_gsm().create_workspace.side_effect = Exception()
        init_command.init_modflow(self.mock_arguments)
        print_value = mock_print.getvalue()
        self.assertIn("An error occurred during workspace creation", print_value)

    @mock.patch('tethysapp.modflow.cli.init_command.GeoServerSpatialDatasetEngine')
    @mock.patch('tethysapp.modflow.cli.init_command.ModflowSpatialManager')
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_init_style_error(self, mock_print, mock_gsm, _):
        mock_gsm().create_all_styles.side_effect = Exception()
        init_command.init_modflow(self.mock_arguments)
        print_value = mock_print.getvalue()
        self.assertIn("An error occurred during style creation", print_value)
