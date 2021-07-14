import unittest
from tethysapp.modflow.services.licenses import ModflowLicenses


class LicensesTests(unittest.TestCase):

    def setUp(self):
        self.licenses = ModflowLicenses()
        self.invalid_license = 'invalid_license'

    def tearDown(self):
        pass

    def test_must_have_consultant(self):
        self.assertTrue(self.licenses.must_have_consultant(ModflowLicenses.STANDARD))
        self.assertFalse(self.licenses.must_have_consultant(ModflowLicenses.CONSULTANT))
        self.assertRaises(ValueError, self.licenses.must_have_consultant, ModflowLicenses.ADVANCED)
        self.assertRaises(ValueError, self.licenses.must_have_consultant, ModflowLicenses.PROFESSIONAL)
        self.assertRaises(ValueError, self.licenses.must_have_consultant, self.invalid_license)
