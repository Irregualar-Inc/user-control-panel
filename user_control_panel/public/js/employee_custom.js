frappe.ui.form.on("Employee", {
	onload: function (frm) {
		if (!frappe.user.has_role("System Manager")) {
			frappe.meta.get_docfield("Employee", "create_user", frm.doc.name).hidden = 1;
			frappe.meta.get_docfield(
				"Employee",
				"create_user_permission",
				frm.doc.name
			).hidden = 1;
			frm.refresh_field("create_user");
			frm.refresh_field("create_user_permission");
		}
		if (!frm.doc.__islocal) {
			updateUserEnabledStatus(frm);
		}
		setFormReadOnly(frm);
	},

	refresh: function (frm) {
		if (!frappe.user.has_role("System Manager")) {
			frappe.meta.get_docfield("Employee", "create_user", frm.doc.name).hidden = 1;
			frappe.meta.get_docfield(
				"Employee",
				"create_user_permission",
				frm.doc.name
			).hidden = 1;
			frm.refresh_field("create_user");
			frm.refresh_field("create_user_permission");
		}
		if (!frm.doc.__islocal) {
			if (frappe.user.has_role("HR Manager")) {
				if (!frm.doc.user_id && frm.status !== "Active") {
					setupCreateUserButton(frm);
				}
				frm.doc.__ignore_user_status = true;
				setupUserToggleButton(frm);
				updateUserEnabledStatus(frm);
			}
		}
		setFormReadOnly(frm);
	},

	validate: function (frm) {
		if (frm.doc.user_id) {
			frm.doc.__ignore_user_status = true;
		}
	},
});

function updateUserEnabledStatus(frm) {
	if (frm.doc.user_id) {
		// Freeze UI while checking user status
		frappe.dom.freeze(__("Checking user status..."));

		frappe.db
			.get_value("User", frm.doc.user_id, "enabled", function (r) {
				const enabledValue = r.enabled ? 1 : 0;
				if (frm.doc.user_enabled !== enabledValue) {
					frm.set_value("user_enabled", enabledValue);
					frm.refresh_field("user_enabled");
					frappe.dom.freeze(__("Updating user status..."));
					frm.save()
						.then(() => {
							frappe.dom.unfreeze();
						})
						.catch(() => {
							frappe.dom.unfreeze();
						});
				} else {
					frappe.dom.unfreeze();
				}
			})
			.fail(function () {
				frappe.dom.unfreeze();
			});
	} else {
		if (frm.doc.user_enabled !== 0) {
			frm.set_value("user_enabled", 0);
			frm.refresh_field("user_enabled");

			frappe.dom.freeze(__("Updating user status..."));
			frm.save()
				.then(() => {
					frappe.dom.unfreeze();
				})
				.catch(() => {
					frappe.dom.unfreeze();
				});
		}
	}
}

function setupUserToggleButton(frm) {
	if (frm.doc.user_id) {
		frappe.dom.freeze(__("Checking user status..."));

		frappe.call({
			method: "frappe.client.get_value",
			args: {
				doctype: "User",
				fieldname: "enabled",
				filters: { name: frm.doc.user_id },
			},
			callback: function (r) {
				if (r.message) {
					const currentEnabledStatus = r.message.enabled;
					const buttonLabel = currentEnabledStatus ? "Disable User" : "Enable User";

					frm.add_custom_button(__(buttonLabel), function () {
						const confirmMessage = `Are you sure you want to ${
							currentEnabledStatus ? "disable" : "enable"
						} this user?`;

						frappe.confirm(confirmMessage, function () {
							frappe.dom.freeze(
								__(`${currentEnabledStatus ? "Disabling" : "Enabling"} user...`)
							);

							frappe.call({
								method: "user_control_panel.user_control_panel.api.toggle_user_status",
								args: { user_id: frm.doc.user_id, doc_id: frm.doc.name },
								callback: function (response) {
									frappe.show_alert(response, (indicator = "green"));
									frm.reload_doc();
								},
								always: function () {
									frappe.dom.unfreeze();
								},
							});
						});
					});
				}
			},
			always: function () {
				frappe.dom.unfreeze();
			},
		});
		frappe.dom.unfreeze();
	}
}

function setupCreateUserButton(frm) {
	frm.add_custom_button(__("Invite/Link User"), function () {
		if (!frm.doc.company_email) {
			frappe.throw(__('Please set "Company Email".'));
		}

		frappe.dom.freeze(__("Inviting/Linking User..."));

		frappe.call({
			method: "user_control_panel.user_control_panel.api.create_user_permissions",
			args: {
				email: frm.doc.company_email,
				first_name: frm.doc.first_name,
				last_name: frm.doc.last_name,
				middle_name: frm.doc.middle_name,
				company: frm.doc.company,
				employee_id: frm.doc.name,
			},
			callback: function () {
				frappe.show_alert(__("User invited/linked successfully."));
			},
			always: function () {
				frappe.dom.unfreeze();
			},
		});
	}).addClass("btn-primary");
}

function setFormReadOnly(frm) {
	if (frm.doc.user_enabled === 0 && frm.doc.user_id) {
		frm.set_read_only();
	}
}
