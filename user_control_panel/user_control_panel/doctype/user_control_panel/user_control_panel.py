import frappe

frappe.log_error("Loading user_control_panel.py", "Debug")
from frappe.model.document import Document


class UserControlPanel(Document):
	def on_update(self):
		# This method is called after the document is saved
		# You can add your custom logic here
		self.perform_after_save_actions()

	def perform_after_save_actions(self):
		# This method is called after the document is saved
		# You can add your custom logic here
		try:
			control_panel_settings = frappe.get_doc("Control Panel Settings")

			allowed_roles = [role.role for role in control_panel_settings.allowed_roles]

			user = frappe.get_doc("User", self.user)

			current_user_roles = [user_role.role for user_role in user.roles]

			selected_roles = [role.role for role in self.roles]

			roles_to_add = []
			roles_to_remove = []

			for role in selected_roles:
				if role in allowed_roles and role not in current_user_roles:
					roles_to_add.append(role)

			for role in current_user_roles:
				if role in allowed_roles and role not in selected_roles:
					roles_to_remove.append(role)

			for role in roles_to_add:
				user.append("roles", {"role": role})

			ur = []

			for user_role in user.roles:
				if user_role.role not in roles_to_remove:
					ur.append(user_role)

			user.roles = ur

			user.save(ignore_permissions=True)

			if roles_to_add or roles_to_remove:
				frappe.log_error(
					title="User Role Management",
					message=f"User: {self.user}\nAdded Roles: {roles_to_add}\nRemoved Roles: {roles_to_remove}",
				)
		except Exception as e:
			frappe.log_error(
				title="Control Panel Management Error", message=f"Error managing roles for {self.user}: {e!s}"
			)
			frappe.throw(f"Error managing user roles: {e!s}")

		try:
			# Keep track of permissions we're setting now
			current_permissions = []

			for permission in self.restrictions:
				permission_dict = {
					"doctype": "User Permission",
					"user": self.user,
					"allow": permission.allow,
					"for_value": permission.for_value,
					"is_default": permission.is_default,
					"apply_to_all_doctypes": permission.apply_to_all_doctypes,
					"applicable_for": permission.applicable_for,
					"hide_descendants": permission.hide_descendants,
				}

				# Build a unique identifier for this permission
				permission_key = f"{permission.allow}:{permission.for_value}"
				current_permissions.append(permission_key)

				# Check if permission already exists
				existing_permission = frappe.db.exists(
					"User Permission",
					{"user": self.user, "allow": permission.allow, "for_value": permission.for_value},
				)

				if existing_permission:
					# Update existing permission
					perm_doc = frappe.get_doc("User Permission", existing_permission)
					perm_doc.is_default = permission.is_default
					perm_doc.apply_to_all_doctypes = permission.apply_to_all_doctypes
					perm_doc.applicable_for = permission.applicable_for
					perm_doc.hide_descendants = permission.hide_descendants
					perm_doc.save(ignore_permissions=True)
				else:
					# Create new permission
					restriction = frappe.get_doc(permission_dict)
					restriction.insert(ignore_permissions=True)

			# Find and delete permissions that were not included in the current set
			existing_permissions = frappe.get_all(
				"User Permission", filters={"user": self.user}, fields=["name", "allow", "for_value"]
			)

			for perm in existing_permissions:
				perm_key = f"{perm.allow}:{perm.for_value}"
				if perm_key not in current_permissions:
					frappe.delete_doc("User Permission", perm.name, ignore_permissions=True)
		except Exception as e:
			frappe.log_error(
				title="Control Panel Management Error",
				message=f"Error managing permissions for {self.user}: {e!s}",
			)
			frappe.throw(f"Error managing user permissions: {e!s}")
