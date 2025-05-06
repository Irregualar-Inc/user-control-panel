frappe.provide("user_control_panel");

frappe.ui.form.on("Control Panel Settings", {
	refresh: function (frm) {
		// Override the standard save method for this form only
		frm.page.btn_primary.off("click");
		frm.page.btn_primary.on("click", function () {
			// Save directly without the confirmation step
			frm.save("Save", null, 1);
		});
	},
});

frappe.ui.form.on("User Control Panel", {
	refresh: function (frm) {
		// Override the standard save method for this form only
		frm.page.btn_primary.off("click");
		frm.page.btn_primary.on("click", function () {
			// Save directly without the confirmation step
			frm.save("Save", null, 1);
		});
	},
});
