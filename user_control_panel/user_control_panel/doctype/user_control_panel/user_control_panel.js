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
		if (frm.doc.__islocal) {
			check_and_add_non_removable_row(frm, true);
		}
	},

	user: function (frm) {
		if (frm.doc.user) {
			frappe.call({
				method: "user_control_panel.user_control_panel.api.control_panel_role",
				args: {
					user: frm.doc.user,
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
			frappe.call({
				method: "user_control_panel.user_control_panel.api.control_panel_restrictions",
				args: {
					user: frm.doc.user,
				},
				callback: function (response) {
					if (response.message && response.message.length > 0) {
						const userRestrictions = response.message;

						frm.clear_table("restrictions");

						userRestrictions.forEach((restriction) => {
							const child = frm.add_child("restrictions");
							child.allow = restriction.allow;
							child.for_value = restriction.for_value;
							child.is_default = restriction.is_default;
							child.apply_to_all_doctypes = restriction.apply_to_all_doctypes;
							child.applicable_for = restriction.applicable_for;
							child.hide_descendants = restriction.hide_descendants;
						});

						frm.refresh_field("restrictions");
						check_and_add_non_removable_row(frm, true);
					} else {
						console.error(
							"No restrictions found for the employee or invalid response"
						);
					}
				},
			});
		} else {
			frm.clear_table("restrictions");
			frm.refresh_field("restrictions");
		}
	},

	restrictions_add: function (frm, cdt, cdn) {
		check_and_add_non_removable_row(frm);
	},

	restrictions_remove: function (frm, cdt, cdn) {
		check_and_add_non_removable_row(frm);
	},
});

frappe.ui.form.on("Control Panel Restriction", {
	allow: function (frm, cdt, cdn) {
		check_and_add_non_removable_row(frm);
	},
});

function check_and_add_non_removable_row(frm, new_form=false) {
	frappe.call({
		method: "user_control_panel.user_control_panel.api.control_panel_default_restrictions",
		callback: function (response) {
			console.log("Response from server:", response);
			if (response.message && response.message.length > 0) {
				const defaultRestrictions = response.message;

				defaultRestrictions.forEach((restriction) => {
					existing_restriction = frm.doc.restrictions.find(
						(r) => r.allow === restriction.allow
					);
					if (existing_restriction || (new_form && !restriction.required)) {
						return;
					} else {
						const child = frm.add_child("restrictions");
						child.allow = restriction.allow;
						child.for_value = restriction.for_value;
						child.is_default = restriction.is_default;
						child.apply_to_all_doctypes = restriction.apply_to_all_doctypes;
						child.applicable_for = restriction.applicable_for;
						child.hide_descendants = restriction.hide_descendants;
						child.required = restriction.required;
					}
				});

				frm.refresh_field("restrictions");
			} else if (frm.doc.restrictions.length === 0) {
				frm.clear_table("restrictions");
				frm.refresh_field("restrictions");
			}
		},
	});
}

function reset_user_password(frm) {
	if (!frm.doc.user) {
		frappe.msgprint(__("Please select a user first."));
		return;
	}

	frappe.call({
		method: "user_control_panel.user_control_panel.api.reset_password",
		args: {
			user: frm.doc.user,
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
