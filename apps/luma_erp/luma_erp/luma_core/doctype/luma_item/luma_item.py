import frappe
from frappe.model.document import Document


class LumaItem(Document):
	def validate(self) -> None:
		self.item_code = self.item_code.strip().upper()
		self.item_name = self.item_name.strip()
		self.stock_uom = self.stock_uom.strip()

		if not self.item_code.isalnum():
			frappe.throw("Item Code must contain only letters and numbers.")
		if self.standard_rate < 0:
			frappe.throw("Standard Rate cannot be negative.")
