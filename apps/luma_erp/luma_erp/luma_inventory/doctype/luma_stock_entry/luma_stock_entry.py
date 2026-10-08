import frappe
from frappe.model.document import Document


class LumaStockEntry(Document):
	def validate(self) -> None:
		if not self.items:
			frappe.throw("A stock entry must contain at least one item.")

		if self.entry_type == "Receipt" and self.source_warehouse:
			frappe.throw("A receipt cannot have a source warehouse.")
		if self.entry_type == "Receipt" and not self.target_warehouse:
			frappe.throw("A receipt requires a target warehouse.")
		if self.entry_type == "Issue" and self.target_warehouse:
			frappe.throw("An issue cannot have a target warehouse.")
		if self.entry_type == "Issue" and not self.source_warehouse:
			frappe.throw("An issue requires a source warehouse.")
		if self.entry_type == "Transfer" and (
			not self.source_warehouse or not self.target_warehouse
		):
			frappe.throw("A transfer requires source and target warehouses.")
		if (
			self.entry_type == "Transfer"
			and self.source_warehouse
			and self.source_warehouse == self.target_warehouse
		):
			frappe.throw("Source and target warehouses must be different.")

		self.total_quantity = 0
		for item in self.items:
			if item.qty <= 0:
				frappe.throw("Stock quantity must be greater than zero.")
			self.total_quantity += item.qty

	def before_insert(self) -> None:
		self.status = "Draft"

	def on_submit(self) -> None:
		self._apply_movement(1)
		self.status = "Submitted"

	def on_cancel(self) -> None:
		self._apply_movement(-1)
		self.status = "Cancelled"

	def _apply_movement(self, direction: int) -> None:
		for item in self.items:
			if self.entry_type == "Receipt":
				self._update_balance(item.item, self.target_warehouse, item.qty * direction)
			elif self.entry_type == "Issue":
				self._update_balance(item.item, self.source_warehouse, -item.qty * direction)
			else:
				self._update_balance(item.item, self.source_warehouse, -item.qty * direction)
				self._update_balance(item.item, self.target_warehouse, item.qty * direction)

	def _update_balance(self, item: str, warehouse: str, quantity: float) -> None:
		balance_name = frappe.db.get_value(
			"Luma Stock Balance",
			{
				"item": item,
				"warehouse": warehouse,
				"organization": self.organization,
			},
			"name",
		)
		if balance_name:
			balance = frappe.get_doc("Luma Stock Balance", balance_name)
		else:
			balance = frappe.get_doc(
				{
					"doctype": "Luma Stock Balance",
					"item": item,
					"warehouse": warehouse,
					"organization": self.organization,
					"quantity": 0,
				}
			)

		new_quantity = balance.quantity + quantity
		if new_quantity < 0:
			frappe.throw(
				f"Insufficient stock for {item} in warehouse {warehouse}."
			)
		balance.quantity = new_quantity
		balance.last_updated = frappe.utils.now_datetime()
		if balance.is_new():
			balance.insert(ignore_permissions=True)
		else:
			balance.save(ignore_permissions=True)
