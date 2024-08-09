import frappe
# import regex as re
import json
import os

@frappe.whitelist()
def generate_e_bill(docname):
    doc = load_doc("Out Subcontracting", docname)

    sup_data = frappe.get_doc("Address", doc.company_address)
    buy_data = frappe.get_doc("Address", doc.supplier_address)

    igst_amount = sgst_amount = cgst_amount = cess_amount = stcess_amount = 0
    for t in doc.get("taxes"):
        if "SGST" in t.account_head:
            sgst_amount = t.tax_amount
        elif "CGST" in t.account_head:
            cgst_amount = t.tax_amount
        elif "IGST" in t.account_head:
            igst_amount = t.tax_amount
        elif "CESS" in t.account_head:
            cess_amount = t.tax_amount
        elif "STCESS" in t.account_head:
            stcess_amount = t.tax_amount
    
    item_list = []
    id = 0
    for d in doc.get("items"):
        id+=1
        item_dict ={
            "SlNo": id,
            "PrdDesc": d.item_name,
            "IsServc": "N",
            "HsnCd": d.gst_hsn_code,
            "Qty": d.production_quantity,
            "FreeQty": 0,
            "Unit": d.uom,
            "UnitPrice": d.rate,
            "TotAmt": d.total_rate,
            "Discount": 0,
            "PreTaxVal": 0,
            "AssAmt": 0,
            "GstRt": int(d.cgst_rate if d.cgst_rate else 0) + int(d.sgst_rate if d.sgst_rate else 0) + int(d.igst_rate if d.igst_rate else 0),                           
            "IgstAmt": d.igst_amount,
            "CgstAmt": d.cgst_amount,
            "SgstAmt": d.sgst_amount,
            "CesRt": d.cess_rate,
            "CesAmt": d.cess_amount,
            "CesNonAdvlAmt": d.cess_non_advol_amount,
            "StateCesRt": 0,
            "StateCesAmt": 0,
            "StateCesNonAdvlAmt": 0,
            "OthChrg": 0,
            "TotItemVal": d.taxable_value
        }
        item_list.append(item_dict)
        
    # "Sales Invoice Item"

    json_data ={
        "Version": "1.1",  #Version of the schema
        "TranDtls": {
            "TaxSch": "GST",           #*GST- Goods and Services Tax Scheme
            "SupTyp": "B2B",           #*Type of Supply: B2B-Business to Business, SEZWP - SEZ with payment, SEZWOP - SEZ without payment, EXPWP - Export with Payment, EXPWOP - Export without payment,DEXP - Deemed Export
            "IgstOnIntra": "N",        #Y- indicates the supply is intra state but chargeable to IGST
            "RegRev": "N",             #Y- whether the tax liability is payable under reverse charge
            "EcmGstin": None           #GSTIN of e-Commerce operator
            },
        "DocDtls": {
            "Typ": "INV",              #Document Type: INVOICE, CREDIT NOTE, DEBIT NOTE
            "No": doc.name,            #Document Number
            "Dt": str(doc.posting_date)#Document Date
            },
        "SellerDtls": {
            "Gstin": doc.supplier_gstin,       #GSTIN of supplier
            "LglNm": doc.supplier_address,             #Legal Name
            "Addr1": sup_data.address_line1,  #Address 1 of the supplier
            "Addr2": sup_data.address_line2,  #Address 2 of the supplier
            "Loc": sup_data.city,             #Location
            "Pin": sup_data.pincode,                 #Pincode                                     #############################
            "Stcd": (doc.company_gstin)[0:2],                 #State Code of the supplier                     ##############################
            "Ph": sup_data.phone,
            "Em": sup_data.email_id
            },
        "BuyerDtls": {
            "Gstin": doc.company_gstin,          #GSTIN of supplier
            "LglNm": doc.company_address,                  #Legal Name
            "Addr1": buy_data.address_line1,             #Address 1 of the Buyier
            "Addr2": buy_data.address_line2,             #Address 2 of the buyier
            "Loc": buy_data.city,                        #Location
            "Pin": buy_data.pincode,                            #Pincode
            "Pos": doc.place_of_supply,                  #Place Of Supply
            "Stcd": (doc.company_gstin)[0:2],                            #State Code of the buyier
            "Ph": buy_data.phone,
            "Em": buy_data.email_id
            },
        "ValDtls": {
            "AssVal": doc.total_amount,
            "IgstVal": igst_amount, 
            "CgstVal": cgst_amount,
            "SgstVal": sgst_amount,
            "CesVal": cess_amount,
            "StCesVal": stcess_amount,
            "Discount": 0,
            "OthChrg": 0,
            "RndOffAmt": doc.rounded_total,
            "TotInvVal": doc.outstanding_amount
            },
        "RefDtls": {
            "InvRm": "NICGEPP2.0"
            },
            "ItemList": item_list
    }
    json_string = json.dumps(json_data, indent=4)
    return json_string

    
def load_doc(doctype, name, perm="read"):
    doc = frappe.get_doc(doctype, name)
    doc.check_permission(perm)
    run_onload(doc)
    return doc

def run_onload(doc):
	doc.set("__onload", frappe._dict())
	doc.run_method("onload")