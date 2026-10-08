import frappe
from frappe.model.document import Document


class LumaWarehouse(Document):
	def validate(self) -> None:
		self.warehouse_code = self.warehouse_code.strip().upper()
		self.warehouse_name = self.warehouse_name.strip()

		if not self.warehouse_code.isalnum():
			frappe.throw("Warehouse Code must contain only letters and numbers.")
