import frappe
from frappe.model.document import Document


class UserControlPanel(Document):
    def on_update(self):
        # This method is called after the document is saved
        employee = frappe.get_doc("Employee", self.employee)
        restrictions_data = []
        for r in self.restrictions:
            restrictions_data.append({
                "user": employee.user_id,
                "allow": r.allow,
                "for_value": r.for_value,
                "is_default": r.is_default,
                "apply_to_all_doctypes": r.apply_to_all_doctypes,
                "applicable_for": r.applicable_for,
                "hide_descendants": r.hide_descendants,
            })
        frappe.enqueue(
            method="user_control_panel.utils.sync_permissions_async",
            queue="short",
            timeout=300,
            employee_user_id=employee.user_id,
            restrictions=restrictions_data,
            now=True,
        )
        self.sync_user_roles(employee.user_id)

    def sync_user_roles(self, employee_user_id):
        """
        Synchronize User Roles to exactly match desired desired_roles,
        while preserving any 'Company' permissions.
        """
        try:
            control_panel_settings = frappe.get_doc("Control Panel Settings")
            allowed_roles = [role.role for role in control_panel_settings.allowed_roles]
            user = frappe.get_doc("User", employee_user_id)
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
                    message=f"User: {employee_user_id}\nAdded Roles: {roles_to_add}\nRemoved Roles: {roles_to_remove}",
                )

        except Exception as e:
            frappe.log_error(
                title="Control Panel Management Error",
                message=f"Error managing roles for {employee_user_id}: {e | str}",
            )
            frappe.throw(f"Error managing user roles: {e | str}")
