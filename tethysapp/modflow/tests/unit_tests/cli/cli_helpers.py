"""
********************************************************************************
* Name: cli_helperss
* Author: ckrewson and mlebaron
* Created On: November 14, 2018
* Copyright: (c) Aquaveo 2018
********************************************************************************
"""
import os
import tempfile
import mock
import unittest
from tethysapp.modflow.cli import cli_helpers
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


class CliHelperTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_print_error(self, mock_print):
        expected_statement = 'foo'
        cli_helpers.print_error(statement=expected_statement)
        print_value = mock_print.getvalue()
        self.assertIn('\033[91m', print_value)
        self.assertIn(expected_statement, print_value)
        self.assertIn('\033[0m', print_value)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_print_suceess(self, mock_print):
        expected_statement = 'foo'
        cli_helpers.print_success(statement=expected_statement)
        print_value = mock_print.getvalue()
        self.assertIn('\033[92m', print_value)
        self.assertIn(expected_statement, print_value)
        self.assertIn('\033[0m', print_value)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_print_warning(self, mock_print):
        expected_statement = 'foo'
        cli_helpers.print_warning(statement=expected_statement)
        print_value = mock_print.getvalue()
        self.assertIn('\033[93m', print_value)
        self.assertIn(expected_statement, print_value)
        self.assertIn('\033[0m', print_value)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_print_info(self, mock_print):
        expected_statement = 'foo'
        cli_helpers.print_info(statement=expected_statement)
        print_value = mock_print.getvalue()
        self.assertIn('\033[94m', print_value)
        self.assertIn(expected_statement, print_value)
        self.assertIn('\033[0m', print_value)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_print_header(self, mock_print):
        expected_statement = 'foo'
        cli_helpers.print_header(statement=expected_statement)
        print_value = mock_print.getvalue()
        self.assertIn('\033[95m', print_value)
        self.assertIn(expected_statement, print_value)
        self.assertIn('\033[0m', print_value)

    def test_PGPassManager_get_path(self):
        expected_path = os.path.expanduser('~/') + '.pgpass'
        pgpm = cli_helpers.PGPassManager()
        actual_path = pgpm.get_path()
        self.assertEqual(expected_path, actual_path)

    def test_get_content_with_no_file(self):
        pgpm = cli_helpers.PGPassManager()
        pgpm.path = '/foo/bar'
        actual_content = pgpm.get_content()
        self.assertEqual('', actual_content)

    def test_get_content(self):
        _, temp_path = tempfile.mkstemp()
        pgpm = cli_helpers.PGPassManager()
        pgpm.path = temp_path
        actual_content = pgpm.get_content()
        self.assertEqual('', actual_content)

    def test_get_content_with_data(self):
        _, temp_path = tempfile.mkstemp()
        pgpm = cli_helpers.PGPassManager()
        pgpm.path = temp_path
        with open(temp_path, 'w') as f:
            f.write('foo')
        actual_content = pgpm.get_content()
        self.assertEqual('foo', actual_content)

    def test_restore_content(self):
        _, temp_path = tempfile.mkstemp()
        pgpm = cli_helpers.PGPassManager()
        pgpm.path = temp_path
        pgpm.content = 'boo'
        pgpm.restore_content()
        with open(temp_path, 'r') as f:
            actual_content = f.read()
        self.assertEqual('boo', actual_content)

    def test_add_entry_if_not_exists(self):
        _, temp_path = tempfile.mkstemp()
        pgpm = cli_helpers.PGPassManager()
        pgpm.path = temp_path
        pgpm.add_entry_if_not_exists('localhost', '5432', 'db', 'admin', 'pass')
        with open(temp_path, 'r') as f:
            actual_content = f.read()
        self.assertEqual('localhost:5432:db:admin:pass\n', actual_content)

    def test_add_entry_if_not_exists_content_exists(self):
        _, temp_path = tempfile.mkstemp()
        with open(temp_path, 'w') as f:
            f.write('localhost:5432:db:admin:pass')
        pgpm = cli_helpers.PGPassManager()
        pgpm.path = temp_path
        pgpm.content = pgpm.get_content()
        pgpm.add_entry_if_not_exists('localhost', '5432', 'db', 'admin', 'pass')
        with open(temp_path, 'r') as f:
            actual_content = f.read()
        self.assertEqual('localhost:5432:db:admin:pass', actual_content)
