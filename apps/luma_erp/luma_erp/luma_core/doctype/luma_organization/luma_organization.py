import frappe
from frappe.model.document import Document


class LumaOrganization(Document):
	def validate(self) -> None:
		self.organization_code = self.organization_code.strip().upper()
		if not self.organization_code.isalnum():
			frappe.throw("Organization Code must contain only letters and numbers.")

		self.organization_name = self.organization_name.strip()
		if len(self.organization_name) < 2:
			frappe.throw("Organization Name must contain at least two characters.")
