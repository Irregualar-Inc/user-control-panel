import frappe
from frappe import _


@frappe.whitelist()
def control_panel_role():
	user = frappe.form_dict.get("user")

	roles = frappe.db.get_all(
		"Has Role",
		filters={"parent": user, "parenttype": "User"},
		fields=["role"],
	)

	return [role.role for role in roles]


@frappe.whitelist()
def reset_password():
	new_password = frappe.utils.generate_hash(length=8)
	user = frappe.form_dict.get("user")
	try:
		user_doc = frappe.get_doc("User", user)
		user_doc.new_password = new_password
		user_doc.save(ignore_permissions=True)
		frappe.db.commit()
		return new_password
	except Exception as e:
		frappe.log_error(f"Error resetting password for user {user}: {e}")
		frappe.throw(_(f"Failed to reset password. Please try again.: {e}"))
