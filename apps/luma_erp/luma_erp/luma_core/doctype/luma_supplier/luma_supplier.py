import frappe
from frappe.model.document import Document


class LumaSupplier(Document):
	def validate(self) -> None:
		self.supplier_code = self.supplier_code.strip().upper()
		self.supplier_name = self.supplier_name.strip()

		if not self.supplier_code.isalnum():
			frappe.throw("Supplier Code must contain only letters and numbers.")
