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
from tethysapp.modflow.cli import makemigrations
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class MakeMigrationsTests(unittest.TestCase):

    def setUp(self):
        self.mock_arguments = mock.MagicMock(
            message="message",
            dburl="postgresql://postgres:pass@localhost:5432/db"
        )

    def tearDown(self):
        pass

    @mock.patch('tethysapp.modflow.cli.makemigrations.ac')
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_make_migrations(self, mock_print, mock_alc):
        makemigrations.makemigrations(self.mock_arguments)
        mock_alc.main.assert_called()
        mc_call_args_list = mock_alc.main.call_args_list
        self.assertIn("dburl=postgresql://postgres:pass@localhost:5432/db", mc_call_args_list[0][0][0])
        self.assertIn("message", mc_call_args_list[0][0][0])
        print_value = mock_print.getvalue()
        self.assertIn('Generating migration for "modflow" with message "message"', print_value)
        self.assertIn('Successfully generated migrations for "modflow"', print_value)

    @mock.patch('tethysapp.modflow.cli.makemigrations.ac')
    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_make_migrations_without_message(self, mock_print, mock_alc):
        self.mock_arguments.message = None
        makemigrations.makemigrations(self.mock_arguments)
        mock_alc.main.assert_called()
        mc_call_args_list = mock_alc.main.call_args_list
        self.assertIn("dburl=postgresql://postgres:pass@localhost:5432/db", mc_call_args_list[0][0][0])
        self.assertNotIn("message", mc_call_args_list[0][0][0])
        print_value = mock_print.getvalue()
        self.assertIn('Generating migration for "modflow"', print_value)
        self.assertIn('Successfully generated migrations for "modflow"', print_value)
