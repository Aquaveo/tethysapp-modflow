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
import tethysapp.modflow.cli.migrate as migrate
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class MigrateTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch('tethysapp.modflow.cli.migrate.ac')
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_migrate(self, mock_print, mock_alc):
        mock_arguments = mock.MagicMock(downgrade=True, dburl="postgresql://postgres:pass@localhost:5432/db")
        migrate.migrate(mock_arguments)
        mock_alc.main.assert_called()
        mc_call_args_list = mock_alc.main.call_args_list
        self.assertIn("dburl=postgresql://postgres:pass@localhost:5432/db", mc_call_args_list[0][0][0])
        self.assertNotIn("message", mc_call_args_list[0][0][0])
        self.assertIn("downgrade", mc_call_args_list[0][0][0])
        print_value = mock_print.getvalue()
        self.assertIn('Applying downgrade migration', print_value)
        self.assertIn('Successfully applied migrations for "modflow"', print_value)

    @mock.patch('tethysapp.modflow.cli.migrate.ac')
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_migrate_upgrade(self, mock_print, mock_alc):
        mock_arguments = mock.MagicMock(downgrade=False, dburl="postgresql://postgres:pass@localhost:5432/db")
        migrate.migrate(mock_arguments)
        mock_alc.main.assert_called()
        mc_call_args_list = mock_alc.main.call_args_list
        self.assertIn("dburl=postgresql://postgres:pass@localhost:5432/db", mc_call_args_list[0][0][0])
        self.assertNotIn("message", mc_call_args_list[0][0][0])
        self.assertIn("upgrade", mc_call_args_list[0][0][0])
        print_value = mock_print.getvalue()
        self.assertIn('Applying upgrade migration', print_value)
        self.assertIn('Successfully applied migrations for "modflow"', print_value)
