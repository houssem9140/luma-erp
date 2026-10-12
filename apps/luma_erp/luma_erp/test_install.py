import frappe
from frappe.tests.utils import FrappeTestCase

from luma_erp.install import ROLE_PERMISSIONS, setup_roles_and_permissions


class TestLumaInstallation(FrappeTestCase):
	def test_business_roles_have_permissions(self) -> None:
		setup_roles_and_permissions()

		for role, doctypes in ROLE_PERMISSIONS.items():
			self.assertTrue(frappe.db.exists("Role", role))
			for doctype in doctypes:
				permission = frappe.db.get_value(
					"Custom DocPerm",
					{"parent": doctype, "role": role, "permlevel": 0},
					["read", "write", "create", "submit", "cancel"],
					as_dict=True,
				)
				self.assertIsNotNone(permission)
				self.assertEqual(permission.read, 1)
				self.assertEqual(permission.write, 1)
				self.assertEqual(permission.create, 1)
				self.assertEqual(permission.submit, 1)
				self.assertEqual(permission.cancel, 1)
