# Copyright (c) 2024, Quantbit Technology Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import erpnext
from frappe.model.document import Document
from erpnext.stock.utils import get_combine_datetime
from frappe.query_builder.functions import Sum



class OutSubcontracting(Document):	
	def on_submit(self):
		self.stock_transfer_stock_entry('material', 'item', 'quantity', 'batch_no', 'source_warehouse', 'target_warehouse', 'cost_center')

	@frappe.whitelist()
	def stock_transfer_stock_entry(self, table, item_code, quantity, batch_no, source_warehouse, target_warehouse, cost_center):
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Transfer"
		se.company = self.company
		se.set_posting_time = True
		se.posting_date = self.posting_date
		for d in self.get(table):
			if d.get(quantity):
				if d.get(batch_no):
					if d.get(cost_center):
						cst =  d.get(cost_center)
						se.append("items",
								{
									"item_code": d.get(item_code),
									"qty": d.get(quantity),
									"s_warehouse": self.get(source_warehouse),
									"t_warehouse": self.get(target_warehouse),
									"batch_no": d.get(batch_no),
									"cost_center": cst
								})
					else:
						frappe.throw("Cost Center is Mandatory")
				else:
					frappe.throw("Batch No is Mandatory")
			else:
				frappe.throw("Quantity is Mandatory")
		se.custom_out_subcontracting = self.name
		se.cost_center = cst
		if se.items:
			se.insert()
			se.save()
			se.submit()


	@frappe.whitelist()
	def update_batch_no(self):
		po_doc = frappe.get_doc("Job Offer Process",self.process_order)
		###################
		basic_rate = self.get_batch_incoming_rate(self.material[0].item, po_doc.src_warehouse, self.material[0].batch_no, self.posting_date, self.posting_time)
		self.material[0].rate = basic_rate if basic_rate is not None else 0
		self.material[0].amount = self.material[0].quantity * (basic_rate if basic_rate is not None else 0)

	def get_batch_incoming_rate(self, item_code, warehouse, batch_no, posting_date, posting_time, creation=None):
		import datetime

		sle = frappe.qb.DocType("Stock Ledger Entry")

		posting_datetime = get_combine_datetime(posting_date, posting_time)
		if not creation:
			posting_datetime = posting_datetime + datetime.timedelta(milliseconds=1)

		timestamp_condition = sle.posting_datetime < posting_datetime
		if creation:
			timestamp_condition |= (sle.posting_datetime == get_combine_datetime(posting_date, posting_time)) & (
				sle.creation < creation
			)

		batch_details = (
			frappe.qb.from_(sle)
			.select(Sum(sle.stock_value_difference).as_("batch_value"), Sum(sle.actual_qty).as_("batch_qty"))
			.where(
				(sle.item_code == item_code)
				& (sle.warehouse == warehouse)
				& (sle.batch_no == batch_no)
				& (sle.is_cancelled == 0)
			)
			.where(timestamp_condition)
		).run(as_dict=True)

		if batch_details and batch_details[0].batch_qty:
			return batch_details[0].batch_value / batch_details[0].batch_qty

	@frappe.whitelist()
	def get_material_transfer_list(self):
		self.material.clear()
		po_doc = frappe.get_doc("Job Offer Process",self.process_order)
		for mt_doc in po_doc.get("materials"):
			################################################
			amount = self.get_batch_incoming_rate(mt_doc.item, po_doc.src_warehouse, mt_doc.batch_no, self.posting_date, self.posting_time)
			self.append("material",{
				'item':mt_doc.item,
				'yeild':mt_doc.yeild,
				'rate':amount if amount else 0.0,
				'uom':mt_doc.uom,
				'quantity':mt_doc.quantity,
				'amount':mt_doc.quantity * amount if amount else 0.0,
				'item_name':mt_doc.item_name,
				'in_qty':mt_doc.in_qty,
				'manufacturing_rate':mt_doc.manufacturing_rate,
				'basic_value':mt_doc.basic_value,
				'sale_value':mt_doc.sale_value,
				'operation_cost':mt_doc.operation_cost,
				'valuation_rate':mt_doc.valuation_rate,
				'total_cost':mt_doc.total_cost,
				'batch_no':mt_doc.batch_no,
				'warehouse':po_doc.fg_warehouse,
			})
	
	@frappe.whitelist()
	def update_company_address(self):
		if self.company:
			comp_add_data = frappe.get_doc("Address", {"address_title": self.company})
			self.company_address = comp_add_data.name
			self.company_gstin = comp_add_data.gstin
			self.comp_address = f"{comp_add_data.address_line1}\n{comp_add_data.address_line2}\n{comp_add_data.city}\n{comp_add_data.state}\n{comp_add_data.country}"
			self.shipping_address_name = comp_add_data.name
		else:
			frappe.throw("No Company Selected")

	@frappe.whitelist()
	def update_supplier_address(self):
		if self.supplier:
			comp_add_data = frappe.get_doc("Address", {"address_title": self.supplier_name})
			self.supplier_address = comp_add_data.name
			self.supplier_gstin = comp_add_data.gstin
			self.sup_adderss = f"{comp_add_data.address_line1}\n{comp_add_data.address_line2}\n{comp_add_data.city}\n{comp_add_data.state}\n{comp_add_data.country}"
			# self.dispatch_address_name = comp_add_data.name
			self.gst_category = comp_add_data.gst_category

			sup_data = frappe.get_doc("Supplier",self.supplier)
			if sup_data.is_transporter == 1:
				self.transporter = self.supplier
				self.transporter_name = self.supplier_name
				self.gst_transporter_id = sup_data.gst_transporter_id

			self.place_of_supply = f"{comp_add_data.gst_state_number} - {comp_add_data.gst_state}"
		else:
			frappe.throw("No Supplier Selected")
	

	def before_save(self):
		tot_taxable_amount = 0.00
		tot_amount = tot_weight = 0
		for i in self.material:
			item_doc = frappe.get_doc("Item", {'name':i.item})
			tax_rate = frappe.get_value("Item Tax Template", {'name':item_doc.taxes[0].item_tax_template}, 'gst_rate')
			comp_state = frappe.get_value("Address", {"address_title": self.company}, 'state')
			supp_state = frappe.get_value("Address", {"address_title": self.supplier}, 'state')

			tot_amount += i.amount
			# tot_weight += (i.quantity * i.weight_per_unit)

			if comp_state == supp_state:
				i.cgst_rate = i.sgst_rate = (tax_rate/2)
				i.cgst_amount = i.sgst_amount = round((i.amount/100)*(i.cgst_rate),2)
				i.taxable_value = i.cgst_amount + i.sgst_amount
				tot_taxable_amount += i.taxable_value
			else:
				i.igst_rate = tax_rate
				i.igst_amount = round((i.amount/100)*(i.igst_rate),2)
				i.taxable_value = i.igst_amount
				tot_taxable_amount += i.taxable_value

		if comp_state == supp_state:
			filter ={'is_inter_state': 0, 'is_reverse_charge': 0,'gst_state': comp_state}
			tot_taxable_amount = tot_taxable_amount/2
		else:
			filter ={'is_inter_state': 1, 'is_reverse_charge': 0,'gst_state': comp_state}

		tax_cat_list = frappe.get_value("Tax Category",filter,'name')
		
		self.taxes_and_charges = frappe.get_value("Sales Taxes and Charges Template", {'tax_category': tax_cat_list, 'company': self.company}, 'name')
		if self.taxes_and_charges == None:
			frappe.msgprint("Template Not Found")
		else:
			taxes_charges_doc = frappe.get_doc("Sales Taxes and Charges Template",{'name':self.taxes_and_charges})
			for tx in taxes_charges_doc.taxes:
				tot_amount += tot_taxable_amount
				self.taxes.clear()
				self.append("taxes",{
					"charge_type": tx.charge_type,
					"account_head": tx.account_head,
					"description": tx.description,
					"cost_center": tx.cost_center,
					"tax_amount": tot_taxable_amount,
					"total": round(tot_amount,2)
				})

		self.total_weight = tot_weight
		self.total_amount = tot_amount
		self.rounded_total = round(tot_amount)



# @frappe.whitelist()
# def get_data(self, item_code, batch_id):
# 	item = frappe.get_doc("Item", item_code)
# 	for i in self.items:
# 		if i.raw_item_code == item_code and i.batch_id == batch_id:
# 			i.weight_per_unit = item.weight_per_unit
# 			i.uom = item.weight_uom
# 			i.description = item.description
# 			i.gst_hsn_code = item.gst_hsn_code
# 			bin_doc = frappe.get_doc("Bin", {"item_code": item_code, "warehouse": self.source_warehouse})
# 			i.available_quantity = bin_doc.actual_qty
# 			i.rate = bin_doc.valuation_rate

# @frappe.whitelist()
# def update_warehouse(self):
	# self.target_warehouse = frappe.get_value("Supplier",{'name':self.supplier},'custom_default_warehouse')

# def on_cancel(self):
# 	po = frappe.get_doc("Job Offer Process",self.process_order)
# 	raw_qty = sum(qty.quantity for qty in self.material)
# 	po.quantity += raw_qty
# 	po.save()
# 	po.submit()

# po = frappe.get_doc("Job Offer Process",self.process_order)
# raw_qty = sum(qty.quantity for qty in self.material)
# if raw_qty <= po.quantity:
# 	pass
# 	po.quantity -= raw_qty
# 	po.save()
# else:
# 	frappe.throw(f"Material Quantity Exced The Limit Of Process Order. The Limit is {po.quantity}")

################################################
# if mt_doc.batch_no:
# 	bal = frappe.get_all("Stock Ledger Entry",filters={'item_code':mt_doc.item, 'warehouse':po_doc.src_warehouse,'batch_no':mt_doc.batch_no})
# 	if bal:
# 		balance = frappe.get_doc("Stock Ledger Entry",bal[0]['name'],{'stock_value','qty_after_transaction','stock_value_difference','valuation_rate'})
# 		# amount = (float(balance.stock_value) + float(balance.stock_value_difference))/(float(balance.qty_after_transaction) - mt_doc.quantity)
# 		amount = balance.valuation_rate
# 	else:
# 		frappe.throw("No Data Avilable For Respective Batch or Warehouse")
# else:
# 	bal = frappe.get_all("Stock Ledger Entry",filters={'item_code':mt_doc.item, 'warehouse':po_doc.src_warehouse,'batch_no':mt_doc.batch_no})
# 	if bal:
# 		balance = frappe.get_doc("Stock Ledger Entry",bal[0]['name'],{'stock_value','qty_after_transaction','stock_value_difference','valuation_rate'})
# 		# amount = (float(balance.stock_value) + float(balance.stock_value_difference))/(float(balance.qty_after_transaction) - mt_doc.quantity)
# 		amount = balance.valuation_rate
# 	else:
# 		frappe.throw("No Data Avilable For Respective Batch or Warehouse")

###################
# if self.material[0].batch_no:
# 	bal = frappe.get_all("Stock Ledger Entry",filters={'item_code':self.material[0].item, 'warehouse':po_doc.src_warehouse,'batch_no':self.material[0].batch_no})
# 	if bal:
# 		balance = frappe.get_doc("Stock Ledger Entry",bal[0]['name'],{'stock_value','qty_after_transaction','stock_value_difference','valuation_rate'})
# 		# basic_rate = (float(balance.stock_value) + float(balance.stock_value_difference))/(float(balance.qty_after_transaction) - self.material[0].quantity)
# 		basic_rate = balance.valuation_rate
# 	else:
# 		frappe.throw("No Data Avilable For Respective Batch or Warehouse")
# else:
# 	bal = frappe.get_all("Stock Ledger Entry",filters={'item_code':self.material[0].item, 'warehouse':po_doc.src_warehouse,'batch_no': self.material[0].batch_no})
# 	if bal:
# 		balance = frappe.get_doc("Stock Ledger Entry",bal[0]['name'],{'stock_value','qty_after_transaction','stock_value_difference','valuation_rate'})
# 		# basic_rate = (float(balance.stock_value) + float(balance.stock_value_difference))/(float(balance.qty_after_transaction) - self.material[0].quantity)
# 		basic_rate = balance.valuation_rate
# 	else:
# 		frappe.throw("No Data Avilable For Respective Batch or Warehouse")