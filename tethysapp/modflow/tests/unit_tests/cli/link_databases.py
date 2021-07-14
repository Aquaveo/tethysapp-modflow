"""
********************************************************************************
* Name: init_command
* Author: nswain
* Created On: July 26, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import mock
import unittest
import tethysapp.modflow.cli.link_databases as ld
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class LinkDatabasesTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch('tethysapp.modflow.cli.link_databases.create_engine')
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_link_databases_no_models(self, mock_print, mock_create_engine):
        mock_result = mock.MagicMock()
        mock_result.__iter__.return_value = []
        mock_create_engine().execute.return_value = mock_result
        mock_arguments = mock.MagicMock(service_name="test_db")

        ld.link_databases(mock_arguments)

        print_value = mock_print.getvalue()
        self.assertIn('No results found', print_value)
        mock_result.close.assert_called()
        mock_create_engine().execute.assert_called()

    @mock.patch('tethys_apps.utilities.create_ps_database_setting')
    @mock.patch('tethysapp.modflow.cli.link_databases.create_engine')
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_link_databases_create_success(self, mock_print, mock_create_engine, mock_cpds):
        mock_result = mock.MagicMock()
        mock_result.__iter__.return_value = ['eggs']
        mock_create_engine().execute.return_value = mock_result
        mock_cpds.return_value = True
        mock_arguments = mock.MagicMock(service_name="test_db")

        ld.link_databases(mock_arguments)

        print_value = mock_print.getvalue()
        self.assertNotIn('No results found', print_value)
        self.assertIn('Successfully linked Modflow DB', print_value)

    @mock.patch('tethys_apps.utilities.create_ps_database_setting')
    @mock.patch('tethysapp.modflow.cli.link_databases.create_engine')
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_link_databases_create_failure(self, mock_print, mock_create_engine, mock_cpds):
        mock_result = mock.MagicMock()
        mock_result.__iter__.return_value = ['eggs']
        mock_create_engine().execute.return_value = mock_result
        mock_cpds.return_value = False
        mock_arguments = mock.MagicMock(service_name="test_db")

        ld.link_databases(mock_arguments)

        print_value = mock_print.getvalue()
        self.assertNotIn('No results found', print_value)
        self.assertIn('Could not link the database', print_value)
