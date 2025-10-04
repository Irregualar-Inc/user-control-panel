frappe.ui.form.on("User Control Panel", {
	refresh: function (frm) {
		if (!frm.doc.__islocal) {
			if (frappe.user.has_role("IT Manager")) {
				frm.add_custom_button(__("Reset User Password"), function () {
					reset_user_password(frm);
				});
			}
		}
	},
	onload: function (frm) {
		frappe.call({
			method: "frappe.client.get",
			args: {
				doctype: "Control Panel Settings",
				name: "Control Panel Settings",
			},
			callback: function (response) {
				if (response.message && response.message.allowed_roles) {
					const allowedRoles = response.message.allowed_roles;
					const allowedRolesArray = allowedRoles.map((role) => role.role);
					frm.set_query("roles", function () {
						return {
							filters: {
								name: ["in", allowedRolesArray],
							},
						};
					});
					frm.doc.allowed_roles = allowedRolesArray;
				} else {
					console.error("No roles found or invalid response");
				}
			},
			error: function (error) {
				console.error("Error fetching roles:", error);
			},
		});
		check_and_add_non_removable_row(frm);
	},

	validate: function (frm) {
		validate_cost_center_exists(frm);
	},

	employee: function (frm) {
		if (frm.doc.user) {
			frappe.call({
				method: "user_control_panel.user_control_panel.api.control_panel_role",
				args: {
					employee: frm.doc.employee,
				},
				callback: function (response) {
					if (response.message && response.message.length > 0) {
						const userRoles = response.message;
						const allowedRoles = frm.doc.allowed_roles || [];
						const filteredRoles = userRoles.filter((role) =>
							allowedRoles.includes(role)
						);

						frm.clear_table("roles");

						filteredRoles.forEach((role) => {
							const child = frm.add_child("roles");
							child.role = role;
						});

						frm.refresh_field("roles");
					} else {
						console.error("No roles found for the employee or invalid response");
					}
				},
			});
		} else {
			frm.clear_table("roles");
			frm.refresh_field("roles");
		}
	},
});

frappe.ui.form.on("Control Panel Restriction", {
	allow: function (frm, cdt, cdn) {
		check_and_add_non_removable_row(frm);
	},
});

function check_and_add_non_removable_row(frm) {
	let restrictions = frm.doc.restrictions || [];
	let cost_center_row = restrictions.find((row) => row.allow === "Cost Center");

	if (!cost_center_row) {
		let new_row = frm.add_child("restrictions");
		new_row.allow = "Cost Center";
		frm.refresh_field("restrictions");
	}
}

function validate_cost_center_exists(frm) {
	let restrictions = frm.doc.restrictions || [];
	let cost_center_row = restrictions.find((row) => row.allow === "Cost Center");

	if (!cost_center_row) {
		frappe.throw(__("Please add 'Cost Center' restriction to the Restrictions table."));
	}
}

function reset_user_password(frm) {
	if (!frm.doc.user) {
		frappe.msgprint(__("Please select a user first."));
		return;
	}

	frappe.call({
		method: "user_control_panel.user_control_panel.api.reset_password",
		args: {
			employee: frm.doc.employee,
		},
		callback: function (response) {
			if (response.message) {
				frappe.msgprint({
					title: __("Password Reset Successful"),
					indicator: "green",
					message: __("The new password for {0} is: <b>{1}</b>", [
						frm.doc.user,
						response.message,
					]),
				});
			} else {
				frappe.msgprint(__("Failed to reset password. Please try again."));
			}
		},
		error: function (error) {
			frappe.msgprint(__("Error resetting password: {0}", [error.message]));
		},
	});
}
