// Copyright (c) 2024, Quantbit Technology Pvt. Ltd. and contributors
// For license information, please see license.txt

// frappe.ui.form.on('Out Subcontracting', {
// 	refresh: function(frm) {

// 	}
// });
frappe.ui.form.on("Out Subcontracting", {
    company: function (frm) {
        frappe.call({
            method: 'update_company_address',
            doc: frm.doc,
            callback: function (r) {
                refresh_field(["company_address", "company_gstin", "comp_address"])
            }
        });
    },
    supplier: function (frm) {
        frappe.call({
            method: 'update_supplier_address',
            doc: frm.doc,
            callback: function (r) {
                refresh_field(["source_warehouse", "target_warehouse", "supplier_address", "supplier_gstin", "sup_adderss", "gst_category", "place_of_supply"])
            }
        });
    },
    process_order: function(frm){
        frappe.call({
            method: 'get_material_transfer_list',
            doc: frm.doc,
            callback: function(r){
                frm.refresh_field('items')
                console.log(r.message);
            }
        })
    },
    setup: function (frm) {
        frm.set_query("process_def_id", "items", function (doc, cdt, cdn) {
            return {
                filters: [['Job Offer Process', 'process_type', '=', 'Subcontracting']]
            };
        });

        frm.set_query("process_order", function (doc, cdt, cdn) {
            return {
                filters: [['Job Offer Process', 'process_type', '=', 'Subcontracting']]
            };
        });

        frm.set_query("batch_id", "items", function (doc, cdt, cdn) {
            var child = locals[cdt][cdn];
            return {
                filters: [['Batch', 'item', '=', child.raw_item_code]]
            };
        });
    }
});


frappe.ui.form.on("Out Subcontracting Item", {
    quantity: function(frm, cdt, cdn){
        var row = locals[cdt][cdn];
        row.amount = row.quantity * row.rate;
        frm.refresh_field('items');
    },
    rate: function(frm, cdt, cdn){
        var row = locals[cdt][cdn];
        row.amount = row.quantity * row.rate;
        frm.refresh_field('items');
    },
    batch_no: function(frm){
        frappe.call({
            method: 'update_batch_no',
            doc: frm.doc,
            callback: function(r){
                frm.refresh_field('items')
                console.log(r.message);
            }
        })
    },
});



// frappe.ui.form.on("Out Subcontracting Item", {
//     quantity: function(frm, cdt, cdn) {
//         var row = locals[cdt][cdn];
//         if (row && typeof row.quantity !== 'undefined' && typeof row.rate !== 'undefined') {
//             row.amount = row.quantity * row.rate;
//             frm.refresh_field('items');
//         } else {
//             console.error('Row, quantity, or rate is undefined:', row);
//         }
//     },
//     rate: function(frm, cdt, cdn) {
//         var row = locals[cdt][cdn];
//         if (row && typeof row.quantity !== 'undefined' && typeof row.rate !== 'undefined') {
//             row.amount = row.quantity * row.rate;
//             frm.refresh_field('items');
//         } else {
//             console.error('Row, quantity, or rate is undefined:', row);
//         }
//     }
// });


// frappe.ui.form.on("Out Subcontracting Items", {
//     items_add: function (frm, cdt, cdn) {
//         let row = frappe.get_doc(cdt, cdn);
//         row.process_ord_id = frm.doc.process_order;
//         row.source_warehouse = frm.doc.source_warehouse;
//         row.target_warehouse = frm.doc.target_warehouse;
//         frm.refresh_field('items');
//     },
//     batch_id: function (frm, cdt, cdn) {
//         var d = locals[cdt][cdn];
//         var item_code = d.raw_item_code;
//         var batch_id = d.batch_id;
//         frappe.call({
//             method: 'get_data',
//             doc: frm.doc,
//             args:{
//                 'item_code': item_code,
//                 'batch_id': batch_id
//             },
//             callback: function (r) {
//                 frm.refresh_field('items')
//                 console.log(r.message)
//             }
//         });
//     },
//     production_quantity: function (frm, cdt, cdn) {
//         let row = frappe.get_doc(cdt, cdn);
//         row.total_rate = row.production_quantity * row.rate;
//         frm.refresh_field('items');
//     },
// });