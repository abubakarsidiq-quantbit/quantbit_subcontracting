// Copyright (c) 2024, Quantbit Technology Pvt. Ltd. and contributors
// For license information, please see license.txt

var finished = []
frappe.ui.form.on('In Subcontracting', {
    get_item_list: function (frm) {
        frm.call({
            method: 'get_item_list',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    r.message.forEach(row => finished.push(row.name))
                    console.log(finished)
                }
            }
        });
    },
    department: function (frm) {
        if (frm.doc.department) {
            frappe.call({
                "method": "frappe.client.get",
                args: {
                    doctype: "Manufacturing Department",
                    name: frm.doc.department
                },
                callback: function (data) {
                    frappe.model.set_value(frm.doctype, frm.docname, "wip_warehouse", data.message.wip_warehouse);
                    frappe.model.set_value(frm.doctype, frm.docname, "target_warehouse", data.message.src_warehouse);
                    frappe.model.set_value(frm.doctype, frm.docname, "scrap_warehouse", data.message.scrap_warehouse);
                    frappe.model.set_value(frm.doctype, frm.docname, "source_warehouse", data.message.fg_warehouse);
                }
            });
        }
    },
    before_save: function(frm){
        frm.call({
            "method":"get_updated_values",
            doc:frm.doc,
            callback: function(r){
                console.log("Updated")
            }
        })
    }
});

frappe.ui.form.on("Scrap Item", {
    quantity: function(frm, cdt, cdn){
        var row = locals[cdt][cdn];
        row.amount = row.quantity * row.rate;
        frm.refresh_field('scrap');
    },
    rate: function(frm, cdt, cdn){
        var row = locals[cdt][cdn];
        row.amount = row.quantity * row.rate;
        frm.refresh_field('scrap');
    }
});

frappe.ui.form.on("In Subcontracting Item", {
    qty: function(frm, cdt, cdn){
        var row = locals[cdt][cdn];
        row.amount = row.qty * row.rate;
        frm.refresh_field('in_items');
        frm.call({
            method:'get_total',
            doc: frm.doc,
            callback: function(r){
                if (r.message){
                    console.log(r.message);
                    frm.set_value('raw_products_qty', r.message.raw_products_qty)
                    frm.set_value('finished_products_qty', r.message.finished_products_qty);
                    frm.set_value('finished_products_amount', r.message.finished_products_amount);
                    frm.refresh_field('raw_products_qty');
                    frm.refresh_field('finished_products_qty');
                    frm.refresh_field('finished_products_amount');
                }
            }
        })
    }
});


frappe.ui.form.on('Get Item List', {
    check: function (frm) {
        frm.call({
            method: 'get_finished_item_list',
            doc: frm.doc,
            callback: function (r) {
                if (r.message) {
                    frm.refresh_field(['uom'])
                    frm.refresh_field('in_material')
                    frm.refresh_field('in_items')
                    console.log(r.message)
                }
            }
        });
    }
});

frappe.ui.form.on("Material Items", {
    quantity: function(frm, cdt, cdn){
        var row = locals[cdt][cdn];
        row.amount = row.quantity * row.rate;
        frm.refresh_field('in_material');
    }
});


// frappe.ui.form.on("In Subcontracting Items", {
//     qty: function(frm, cdt, cdn){
//         var row = locals[cdt][cdn];
//         row.amount = row.qty * row.rate;
//         frm.refresh_field('in_items');
        // frm.call({
        //     method:'get_total',
        //     doc: frm.doc,
        //     callback: function(r){
        //         if (r.message){
        //             console.log(r.message);
        //             frm.set_value('raw_products_qty', r.message.raw_products_qty)
        //             frm.set_value('finished_products_qty', r.message.finished_products_qty);
        //             frm.set_value('finished_products_amount', r.message.finished_products_amount);
        //             frm.refresh_field('raw_products_qty');
        //             frm.refresh_field('finished_products_qty');
        //             frm.refresh_field('finished_products_amount');
        //         }
        //     }
        // })
//     },
//     raw_qty: function(frm, cdt, cdn){
//         var row = locals[cdt][cdn];
//         row.amount = row.qty * row.rate;
//         frm.refresh_field('in_items');
//         frappe.call({
//             method:'get_total',
//             doc: frm.doc,
//             callback: function(r){
//                 if (r.message){
//                     console.log(r.message);
//                     frm.set_value('raw_products_qty', r.message.raw_products_qty)
//                     frm.set_value('finished_products_qty', r.message.finished_products_qty);
//                     frm.set_value('finished_products_amount', r.message.finished_products_amount);
//                     frm.refresh_field('raw_products_qty');
//                     frm.refresh_field('finished_products_qty');
//                     frm.refresh_field('finished_products_amount');
//                 }
//             }
//         })
//     },
//     qty: function(frm, cdt, cdn){
//         var row = locals[cdt][cdn];
//         row.amount = row.qty * row.rate;
//         frm.refresh_field('in_items');
//     }
// });

// frappe.ui.form.on('In Subcontracting Items', {
//     qty: function (frm, cdt, cdn) {
//         var d = locals[cdt][cdn];
//         frappe.msgprint(String(d))
//         frm.call({
//             method: "get_total",
//             doc: frm.doc,
//             callback: function (r) {
//                 if (r.message) {
//                     console.log(r.message)
//                 }
//             }
//         });
//     }
// });


// setup: function(frm) {
//     frm.set_query("finished_item", "in_items", function(doc, cdt, cdn) {
//         let d = locals[cdt][cdn];+

//         return {
//             filters: [['Subcontracting BOM','finished_item', 'in', finished]]
//         };
//     });
// },