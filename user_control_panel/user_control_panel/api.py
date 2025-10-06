import frappe
from frappe import _


@frappe.whitelist()
def control_panel_role():
    """
    Get all roles assigned to a specific user.

    Returns:
        list: List of role names assigned to the user
    """
    user_id = frappe.form_dict.get("user")
    if not user_id:
        frappe.throw(_("User ID is required."))

    user = frappe.get_doc("User", user_id)
    roles = frappe.db.get_all(
        "Has Role",
        filters={"parent": user, "parenttype": "User"},
        fields=["role"],
    )

    return [role.role for role in roles]


@frappe.whitelist()
def control_panel_restrictions():
    """
    Get all restrictions assigned to a specific user.

    Returns:
        list: List of role names assigned to the user
    """
    user_id = frappe.form_dict.get("user")
    if not user_id:
        frappe.throw(_("User ID is required."))

    user = frappe.get_doc("User", user_id)
    restrictions = frappe.db.get_all(
        "User Permission",
        filters={"user": user, "allow": ["!=", "Company"]},
        fields=[
            "allow",
            "for_value",
            "is_default",
            "apply_to_all_doctypes",
            "applicable_for",
            "hide_descendants",
        ],
    )

    return [
        {field: restriction.get(field) for field in restriction}
        for restriction in restrictions
    ]

@frappe.whitelist()
def control_panel_default_restrictions():
    """
    Get all restrictions assigned to a specific user.

    Returns:
        list: List of role names assigned to the user
    """
    control_panel_settings = frappe.get_doc("Control Panel Settings")
    restrictions = [r.as_dict() for r in control_panel_settings.user_restrictions]

    return [
        {field: restriction.get(field) for field in restriction}
        for restriction in restrictions
    ]


@frappe.whitelist()
def reset_password():
    """
    Reset a user's password to a new randomly generated password.

    Returns:
        str: The newly generated password
    """
    user_id = frappe.form_dict.get("user")
    if not user_id:
        frappe.throw(_("User ID is required."))

    user = frappe.get_doc("User", user_id)

    try:
        new_password = frappe.utils.generate_hash(length=8)
        user.new_password = new_password
        user.save(ignore_permissions=True)
        frappe.db.commit()
        return new_password
    except Exception as e:
        frappe.log_error(f"Error resetting password for user {user}: {e}")
        frappe.throw(_("Failed to reset password. Please try again."))


@frappe.whitelist()
def toggle_user_status():
    """
    Toggle the enabled status of a user and update the corresponding employee document.

    Request Parameters:
        user_id (str): The ID of the user to toggle
        doc_id (str): The ID of the corresponding employee document

    Returns:
        str: Success message indicating the new status
    """
    user_id = frappe.form_dict.get("user_id")
    employee_doc_id = frappe.form_dict.get("doc_id")

    if not user_id or not employee_doc_id:
        frappe.throw(_("Both user_id and doc_id are required."))

    try:
        user_doc = frappe.get_doc("User", user_id)
        current_status = user_doc.enabled
        new_status = 0 if current_status else 1

        frappe.db.set_value(
            "User", user_id, "enabled", new_status, update_modified=False
        )
        frappe.db.set_value(
            "Employee",
            employee_doc_id,
            "custom_user_enabled",
            new_status,
            update_modified=False,
        )

        status_text = "disabled" if current_status else "enabled"
        return _(f"User {status_text} successfully.")
    except Exception as e:
        frappe.log_error(f"Error toggling status for user {user_id}: {e}")
        frappe.throw(_("Failed to toggle user status. Please try again."))


@frappe.whitelist()
def create_user_permissions():
    """
    Assign default 'Employee' role to a new user.

    Returns:
        dict: Success message with status
    """
    email = frappe.form_dict.get("email")
    employee_id = frappe.form_dict.get("employee_id")
    cost_center = frappe.form_dict.get("cost_center")
    if not employee_id:
        frappe.throw(_("Employee ID is required."))

    try:
        if not frappe.db.exists("User", {"name": email}):
            user_doc = frappe.get_doc(
                {
                    "doctype": "User",
                    "email": email,
                    "first_name": frappe.form_dict.get("first_name"),
                    "middle_name": frappe.form_dict.get("middle_name"),
                    "last_name": frappe.form_dict.get("last_name"),
                    "send_welcome_email": 1,
                }
            )
            user_doc.insert(ignore_permissions=True)
        else:
            user_doc = frappe.get_doc("User", email)
        if "Employee" not in frappe.get_roles(user_doc.name):
            user_doc.add_roles("Employee")
        _create_user_permissions(user_doc.name, employee_id, cost_center)
        frappe.db.commit()
        return _("Employee role assigned successfully.")
    except Exception as e:
        frappe.log_error(f"Error creating user permissions for user {email}: {e}")
        frappe.throw(_("Failed to create user permissions. Please try again."))


def _create_user_permissions(user_id: str, employee_id: str, cost_center: str) -> None:
    """
    Assign default 'Employee' role to a new user and set up their permissions.
    Args:
        user_id (str): The ID of the user to assign the role to.
        company (str): The company to which the user belongs.
        employee_id (str): The ID of the user's employee record.
    Returns:
        None
    """

    try:
        # Add user_id for Employee
        employee = frappe.get_doc("Employee", employee_id)
        employee.user_id = user_id
        employee.create_user_permission = 1
        employee.save()

        frappe.db.commit()

        # Create User Control Panel if it doesn't exist
        if not frappe.db.exists("User Control Panel", {"user": user_id}):
            user_control_panel = frappe.get_doc(
                {
                    "doctype": "User Control Panel",
                    "user": user_id,
                }
            )

            # Add default role (Employee)
            user_control_panel.append("roles", {"role": "Desk User"})

            control_panel_settings = frappe.get_doc("Control Panel Settings")

            # Add restrictions from control panel settings to the User Control Panel
            for restriction in control_panel_settings.user_restrictions:
                user_control_panel.append(
                    "restrictions",
                    {
                        "allow": restriction.allow,
                        "for_value": (
                            employee_id
                            if restriction.allow == "Employee"
                            else (
                                cost_center
                                if restriction.allow == "Cost Center"
                                else restriction.for_value or ""
                            )
                        ),
                        "is_default": restriction.is_default,
                        "apply_to_all_doctypes": restriction.apply_to_all_doctypes,
                        "applicable_for": restriction.applicable_for,
                        "hide_descendants": restriction.hide_descendants,
                        "required": restriction.required,
                    },
                )
            # Save the User Control Panel
            user_control_panel.insert()

    except Exception as e:
        frappe.log_error(f"Error creating user permissions for user {user_id}: {e}")
        frappe.throw(_("Failed to create user permissions. Please try again."))
