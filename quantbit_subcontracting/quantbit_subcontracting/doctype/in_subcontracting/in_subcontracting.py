# Copyright (c) 2024, Quantbit Technology Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from mapro.manufacuring_mode.doctype.process_definition.process_definition import qtyupdate

class InSubcontracting(Document):
	def on_submit(self):
		self.add_batch_order()
		self.update_qty_from_out()
		# self.add_quality_inspection_entry()
		# self.add_manufacture_stock_entry()

	def add_batch_order(self):
		pd = frappe.get_value("Job Offer Process", (self.out_item[0]).process_def_id, 'process_defination')
		bo_doc = frappe.new_doc("Process Order")
		if self.department:
			department_doc = frappe.get_doc("Manufacturing Department", self.department)
			bo_doc.wip_warehouse = department_doc.wip_warehouse
			bo_doc.fg_warehouse = department_doc.fg_warehouse
			bo_doc.scrap_warehouse = department_doc.scrap_warehouse
			bo_doc.src_warehouse = department_doc.src_warehouse
		bo_doc.job_offer = (self.out_item[0]).process_def_id
		bo_doc.process_name = pd
		bo_doc.status = "Draft"
		bo_doc.department = self.department
		bo_doc.quantity = (self.in_material[0]).quantity
		bo_doc.materials_qty = self.raw_products_qty
		bo_doc.materials_amount = (self.in_material[0]).amount
		bo_doc.finished_products_qty = self.finished_products_qty
		bo_doc.finished_products_amount = self.finished_products_amount
		
		for mt_doc in self.in_material:
			bo_doc.append("materials",{
				'item':mt_doc.item,
				'yeild':mt_doc.yeild,
				'rate':mt_doc.rate,
				'uom':mt_doc.uom,
				'quantity':mt_doc.quantity,
				'amount':mt_doc.amount,
				'item_name':mt_doc.item_name,
				'in_qty':mt_doc.in_qty,
				'manufacturing_rate':mt_doc.manufacturing_rate,
				'basic_value':mt_doc.basic_value,
				'sale_value':mt_doc.sale_value,
				'operation_cost':mt_doc.operation_cost,
				'valuation_rate':mt_doc.valuation_rate,
				'total_cost':mt_doc.total_cost,
				'batch_no':mt_doc.batch_no,
				'warehouse':mt_doc.warehouse,
			})
		
		for k in self.operation_cost:
			bo_doc.append("operation_cost",{
					"operations": k.operations,
					"cost": k.cost
				},
			)
		
		bo_doc.total_operation_cost = ((self.total_operation_cost * self.raw_products_qty)/100)

		for fin in self.in_items:
			bo_doc.append("finished_products",{
				'item':fin.finished_item,
				'yeild':fin.yeild,
				'rate':fin.rate,
				'uom': "KGS",
				'quantity':fin.qty,
				'amount':fin.amount,
				'item_name':fin.finished_item_name,
				'batch_no':fin.batch_no,
				'warehouse':self.wip_warehouse
			})
		bo_doc.subcontracting = 1

		for mt_doc in self.get('scrap'):
				bo_doc.append("scrap",{
				'item':mt_doc.item,
				'yeild':mt_doc.yeild,
				'rate':mt_doc.rate,
				'uom':mt_doc.uom,
				'quantity':mt_doc.quantity,
				'amount':mt_doc.amount,
				'item_name':mt_doc.item_name,
				'in_qty':mt_doc.in_qty,
				'manufacturing_rate':mt_doc.manufacturing_rate,
				'basic_value':mt_doc.basic_value,
				'sale_value':mt_doc.sale_value,
				'operation_cost':mt_doc.operation_cost,
				'valuation_rate':mt_doc.valuation_rate,
				'total_cost':mt_doc.total_cost,
				'batch_no':mt_doc.batch_no,
				'warehouse':self.wip_warehouse,
			})
		bo_doc.custom_in_subcontracting = self.name
		bo_doc.save()
		bo_doc.qtyupdate()
		bo_doc.save()

	@frappe.whitelist()
	def update_qty_from_out(self):
		for ref_cha in self.in_items:
			ref_doc = frappe.get_doc("Out Subcontracting", ref_cha.ref_challan)
			for itm in ref_doc.get("material"):
				remaining_qty = (itm.quantity - itm.production_done_quantity + 1)
				# if self.raw_products_qty <= float(remaining_qty):
				if itm.item == ref_cha.raw_item:
					if remaining_qty >= float(ref_cha.raw_qty):
						itm.production_done_quantity = itm.production_done_quantity + float(ref_cha.raw_qty)
						ref_doc.save()
						ref_doc.submit()
					else:
						frappe.throw(str(ref_cha.raw_qty))
						frappe.throw(f"Raw item quantity exceeds remaining quantity for batch {itm.batch_no}.")
		for itm in ref_doc.get("material"):
			remaining_qty = (itm.quantity - itm.production_done_quantity + 1)
			if remaining_qty >= float(self.scrap_qty):
				itm.production_done_quantity = itm.production_done_quantity + float(self.scrap_qty)
				ref_doc.save()
				ref_doc.submit()
			else:
				frappe.msgprint(str(remaining_qty))
				frappe.throw(f"Raw item quantity exceeds remaining quantity for batch {itm.batch_no}.")

	@frappe.whitelist()
	def get_total(self):
		tot_fin_qty = tot_raw_qty = tot_amount = 0
		for itm in self.get("in_items"):
			tot_fin_qty += itm.qty
			tot_raw_qty += itm.raw_qty
			tot_amount += itm.amount
		self.raw_products_qty = tot_raw_qty
		self.finished_products_qty = tot_fin_qty
		self.finished_products_amount = tot_amount

		return {
			'raw_products_qty': self.raw_products_qty,
			'finished_products_qty': self.finished_products_qty,
			'finished_products_amount': self.finished_products_amount
    	}
	
	def get_out_subcontracting_data(self,ref_list):
		self.in_material.clear()
		for ref in ref_list:
			po_doc = frappe.get_doc("Out Subcontracting",ref)
			for mt_doc in po_doc.get("material"):
				self.append("in_material",{
					'item':mt_doc.item,
					'yeild':mt_doc.yeild,
					'rate':mt_doc.rate,
					'uom':mt_doc.uom,
					'quantity':mt_doc.quantity,
					'amount':mt_doc.amount,
					'item_name':mt_doc.item_name,
					'in_qty':mt_doc.in_qty,
					'manufacturing_rate':mt_doc.manufacturing_rate,
					'basic_value':mt_doc.basic_value,
					'sale_value':mt_doc.sale_value,
					'operation_cost':mt_doc.operation_cost,
					'valuation_rate':mt_doc.valuation_rate,
					'total_cost':mt_doc.total_cost,
					'batch_no':mt_doc.batch_no,
					'warehouse':mt_doc.warehouse,
				})
	
	def operation_cost_table(self,process_def_doc,tot_op_cost = 0):
		self.operation_cost.clear()
		for operation_c in process_def_doc.get('operation_cost'):
			tot_op_cost += ((operation_c.definition_cost)/((process_def_doc.quantity/self.in_material[0].quantity)))
			self.append('operation_cost',{
				'operations':operation_c.operations,
				'cost': ((operation_c.definition_cost)/((process_def_doc.quantity/self.in_material[0].quantity)))
			})
		return tot_op_cost

	def get_scarp_table(self,process_def_doc):
		tot_scrap_qty = tot_scrap_amount =0
		self.scrap.clear()
		for mt_doc in process_def_doc.get('scrap'):
			tot_scrap_qty += mt_doc.quantity
			tot_scrap_amount += (self.tot_amount/100)*mt_doc.yeild
			self.append("scrap",{
			'item':mt_doc.item,
			'yeild':mt_doc.yeild,
			'rate': mt_doc.rate,
			'uom':mt_doc.uom,
			'quantity':mt_doc.quantity,
			'amount':mt_doc.quantity * mt_doc.rate,
			'item_name':mt_doc.item_name,
			'in_qty':mt_doc.in_qty,
			'manufacturing_rate':mt_doc.manufacturing_rate,
			'basic_value':mt_doc.basic_value,
			'sale_value':mt_doc.sale_value,
			'operation_cost':mt_doc.operation_cost,
			'valuation_rate':mt_doc.valuation_rate,
			'total_cost':mt_doc.total_cost,
			'batch_no':mt_doc.batch_no,
			'warehouse':mt_doc.warehouse,
		})
		return tot_scrap_qty, tot_scrap_amount
				
	@frappe.whitelist()
	def get_finished_item_list(self):
		process_def_list = []
		tot_op_cost = raw_products_qty = finished_products_qty = total_finished_raw = finished_products_amount = tot_scrap_amount = tot_scrap_qty = 0
		ref_list,prod_out,raw_item,batch, c = [],[],[],[], 0
		
		for process in self.out_item:
			if process.check:
				process_def_list.append(process.process_def_id)
				ref_list.append(process.ref_challan)
				prod_out.append(process.production_quantity)
				raw_item.append(process.raw_item_code)
				batch.append(process.batch_id)

		self.get_out_subcontracting_data(ref_list)
		self.in_items.clear()
		for process_def in process_def_list:
			process_def_doc = frappe.get_doc("Job Offer Process",process_def)
			tot_op_cost = self.operation_cost_table(process_def_doc)
			tot_scrap_qty, tot_scrap_amount = self.get_scarp_table(process_def_doc)	
			self.tot_amount = tot_op_cost + self.in_material[0].amount - tot_scrap_amount

			for finished in process_def_doc.get('finished_products'):
				total_finished_raw += ((finished.quantity)/(process_def_doc.quantity/prod_out[c]))
			total_amount_per_qty = self.tot_amount / total_finished_raw

			for finished in process_def_doc.get('finished_products'):
				raw_products_qty += float(finished.yeild/prod_out[c])
				finished_products_qty += float(((finished.quantity)/(process_def_doc.quantity/prod_out[c])))
				finished_products_amount += float(((finished.quantity)/(process_def_doc.quantity/prod_out[c])) * total_amount_per_qty)
				item_ = frappe.get_doc("Item", {'name': finished.item}, 'item_name','stock_uom')
				self.append('in_items',{
					"ref_challan": ref_list[c],
					"raw_item": raw_item[c],
					"batch_id": batch[c],
					"finished_item": finished.item,
					"finished_item_name": item_.item_name,
					'uom': 'KGS',
					'batch_no': finished.batch_no,
					"yeild": finished.yeild,
					"rate": total_amount_per_qty,
					# "rate": ((self.tot_amount/100)*finished.yeild)/((finished.quantity)/(process_def_doc.quantity/prod_out[c])),
					"qty": ((finished.quantity)/(process_def_doc.quantity/prod_out[c])),
					"raw_qty": ((finished.quantity)/(process_def_doc.quantity/prod_out[c])),
					"amount": ((finished.quantity)/(process_def_doc.quantity/prod_out[c])) * total_amount_per_qty
				})
			c+=1

		self.tot_amount = self.tot_amount
		self.total_manufacturing_cost = self.tot_amount + tot_scrap_amount
		self.scrap_qty = tot_scrap_qty
		self.scrap_amount = tot_scrap_amount
		self.total_operation_cost = tot_op_cost
		self.raw_products_qty = raw_products_qty
		self.finished_products_qty = finished_products_qty
		self.finished_products_amount = finished_products_amount

	@frappe.whitelist()
	def get_updated_values(self):
		srp_amt = srp_qty = op_cst = total_fsh_raw = fshd_amt = fshd_qty = fshd_rqty= 0
		for srp in self.scrap:
			srp_qty = srp_qty + srp.quantity
			srp_amt = srp_amt + srp.amount
		for op in self.operation_cost:
			op_cst = op_cst + op.cost
		self.tot_amount = op_cst + self.in_material[0].amount - srp_amt
		for fsh in self.get('in_items'):
			total_fsh_raw += fsh.raw_qty
		total_amount_per_qty = self.tot_amount / total_fsh_raw
		for fshd in self.in_items:
			fshd.rate = total_amount_per_qty
			fshd.amount = fshd.raw_qty * total_amount_per_qty
			fshd_qty += fshd.qty
			fshd_rqty += fshd.raw_qty
			fshd_amt += fshd.raw_qty * total_amount_per_qty

		self.tot_amount = self.tot_amount
		self.total_manufacturing_cost = self.tot_amount + srp_amt
		self.scrap_qty = srp_qty
		self.scrap_amount = srp_amt
		self.total_operation_cost = op_cst
		self.raw_products_qty = fshd_rqty
		self.finished_products_qty = fshd_qty
		self.finished_products_amount = fshd_amt
		

	def add_manufacture_stock_entry(self):
		for d in self.get("in_items"):
			doc = frappe.new_doc("Stock Entry")
			doc.stock_entry_type = "Manufacture"
			doc.set_posting_time = True
			doc.posting_date = self.posting_date
			for j in self.get("out_item"):
				if j.ref_challan == d.ref_challan:
					doc.append(
						"items",
						{
							"item_code": j.raw_item_code,
							"qty": j.production_quantity,
							"uom": j.uom,
							"s_warehouse": self.source_warehouse,
							"batch_no": d.batch_id
						},
					)
			doc.append(
				"items",
				{
					"item_code": d.finished_item,
					"qty": d.qty,
					"uom": 'KGS',
					"t_warehouse": self.wip_warehouse,
					"is_finished_item": True
				},
			)	
			for k in self.get("operation_cost"):
				doc.append("additional_costs",{
						"expense_account": k.operations,
						"description": k.operations,
						# "amount": k.cost,
						"amount": (k.cost * d.qty)/self.finished_products_qty,
					},
				)
			doc.custom_in_subcontracting = self.name
			doc.insert()
			doc.save()
			doc.submit()
			frappe.msgprint("Manufacture entry successfully inserted")


	@frappe.whitelist()
	def get_item_list(self):
		sql_query = """
					SELECT 
						os.name,
						osi.batch_no,
						osi.item,
						osi.item_name,
						osi.quantity,
						osi.production_done_quantity,
						osi.uom,
						os.process_order
					FROM 
						`tabMaterial Items` AS osi 
					LEFT JOIN 
						`tabOut Subcontracting` AS os 
						ON os.name = osi.parent
					WHERE 
						os.supplier = %s AND osi.quantity > (osi.production_done_quantity) AND os.docstatus = 1
					"""
		params = [self.supplier]
		data = frappe.db.sql(sql_query, tuple(params), as_dict=True)
		self.out_item.clear()
		if data:
			for i in data:
				# item.append(i['raw_item_code'])
				self.append("out_item",{
					"ref_challan": i['name'],
					"batch_id": i['batch_no'],
					"raw_item_code": i['item'],
					"raw_item_name": i['item_name'],
					"production_quantity": i['quantity'],
					"production_done_quantity": i['production_done_quantity'],
					"process_def_id": i['process_order'],
					"uom": i['uom']
				})
		else:
			frappe.msgprint("No Out is done against this Supplier.Check Supplier")


# @frappe.whitelist()
# def get_finished_item_list(self):
# 	process_def_list = []
# 	tot_op_cost = raw_products_qty = finished_products_qty = finished_products_amount = 0
# 	ref_list,prod_out,raw_item,batch, c = [],[],[],[], 0
	
# 	for process in self.out_item:
# 		if process.check:
# 			process_def_list.append(process.process_def_id)
# 			ref_list.append(process.ref_challan)
# 			prod_out.append(process.production_quantity)
# 			raw_item.append(process.raw_item_code)
# 			batch.append(process.batch_id)

# 	self.in_material.clear()
# 	for ref in ref_list:
# 		po_doc = frappe.get_doc("Out Subcontracting",ref)
# 		for mt_doc in po_doc.get("material"):
# 			self.append("in_material",{
# 				'item':mt_doc.item,
# 				'yeild':mt_doc.yeild,
# 				'rate':mt_doc.rate,
# 				'uom':mt_doc.uom,
# 				'quantity':mt_doc.quantity,
# 				'amount':mt_doc.amount,
# 				'item_name':mt_doc.item_name,
# 				'in_qty':mt_doc.in_qty,
# 				'manufacturing_rate':mt_doc.manufacturing_rate,
# 				'basic_value':mt_doc.basic_value,
# 				'sale_value':mt_doc.sale_value,
# 				'operation_cost':mt_doc.operation_cost,
# 				'valuation_rate':mt_doc.valuation_rate,
# 				'total_cost':mt_doc.total_cost,
# 				'batch_no':mt_doc.batch_no,
# 				'warehouse':mt_doc.warehouse,
# 			})

# 	self.in_items.clear()
# 	for process_def in process_def_list:
# 		process_def_doc = frappe.get_doc("Job Offer Process",process_def)
# 		for finished in process_def_doc.get('finished_products'):
# 			raw_products_qty += float((prod_out[c]/100)*finished.yeild)
# 			finished_products_qty += float((prod_out[c]/100)*finished.quantity)
# 			finished_products_amount += float(((prod_out[c]/100)*finished.quantity)*finished.rate)
# 			item_ = frappe.get_doc("Item", {'name': finished.item}, 'item_name','stock_uom')
# 			uom = item_.stock_uom
# 			self.append('in_items',{
# 				"ref_challan": ref_list[c],
# 				"raw_item": raw_item[c],
# 				"batch_id": batch[c],
# 				"finished_item": finished.item,
# 				"finished_item_name": item_.item_name,
# 				'uom': 'KGS',
# 				"yeild": finished.yeild,
# 				"rate":finished.rate,
# 				"qty": ((prod_out[c]/100)*finished.quantity),
# 				"raw_qty": ((prod_out[c]/100)*finished.yeild),
# 				"amount": (((prod_out[c]/100)*finished.quantity)*finished.rate)
# 			})
# 		c+=1
# 		for operation_c in process_def_doc.get('operation_cost'):
# 			self.operation_cost.clear()
# 			tot_op_cost += operation_c.cost
# 			self.append('operation_cost',{
# 				'operations':operation_c.operations,
# 				'cost': operation_c.cost
# 			})
# 	self.total_operation_cost = tot_op_cost
# 	self.raw_products_qty = raw_products_qty
# 	self.finished_products_qty = finished_products_qty
# 	self.finished_products_amount = finished_products_amount
# def add_quality_inspection_entry(self):
# 	for d in self.get("in_items"):
# 		doc = frappe.new_doc("Quality Inspection")
# 		doc.item_code = d.finished_item
# 		doc.batch_no = d.batch_id
# 		doc.sample_size = d.qty
# 		doc.inspection_type = "Incoming"
# 		doc.reference_type = "Stock Entry"