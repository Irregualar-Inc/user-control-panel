import frappe


def get_all_roles():
    excluded_roles = [
        "Administrator",
        "Employee",
        "Employee Self Service",
        "Accounts Manager",
        "System Manager",
        "Agriculture Manager",
        "Agriculture User",
        "All",
        "Guest",
        "Blogger",
        "Website Manager",
        "Report Manager",
        "Translator",
        "Knowledge Base Contributor",
        "Knowledge Base Editor",
        "Fleet Manager",
        "Fulfillment User",
        "Healthcare Administrator",
        "Banking & Payments User",
        "CRM User",
        "Analytics",
        "Auditor",
        "Support Team",
        "Sales Master Manager",
        "Student",
        "Purchase Master Manager",
        "Maintenance Manager",
        "Maintenance User",
        "Manufacturing Manager",
        "Manufacturing User",
        "Marketplace Manager",
        "Newsletter Manager",
        "Workspace Manager",
        "Whatsapp Manager",
    ]

    # Create a proper SQL IN clause with quoted items
    excluded_str = ", ".join([f"'{role}'" for role in excluded_roles])

    query = (
        f"SELECT name FROM `tabRole` WHERE name NOT IN ({excluded_str}) ORDER BY name"
    )
    return [r[0] for r in frappe.db.sql(query)]


def setup_default_user_restrictions():
    """Set up default employee restrictions during app installation"""
    # Check if Control Panel Settings already exists
    if not frappe.db.exists("DocType", "Control Panel Settings"):
        return

    # Document types that have employee fields
    document_types = [
        "Cost Center",
        "Employee",
    ]

    try:
        # Check if a document already exists
        if frappe.db.exists("Control Panel Settings", "Control Panel Settings"):
            doc = frappe.get_doc("Control Panel Settings", "Control Panel Settings")

            # Create sets of existing roles and restrictions to avoid duplicates
            existing_roles = {d.role for d in doc.get("allowed_roles", [])}
            existing_restrictions = {d.allow for d in doc.get("user_restrictions", [])}

            # Add missing roles
            roles = get_all_roles()
            for role in roles:
                if role not in existing_roles:
                    doc.append("allowed_roles", {"role": role})

            # Add missing restrictions
            for doc_type in document_types:
                if doc_type not in existing_restrictions:
                    restriction = {
                        "allow": doc_type,
                        "for_value": "",  # Empty string instead of None
                        "is_default": 0,
                        "apply_to_all_doctypes": 1,
                        "required": 0 if doc_type == "Employee" else 1,
                    }
                    doc.append("user_restrictions", restriction)

            # Save changes if any were made
            if len(doc.get("allowed_roles", [])) > len(existing_roles) or len(
                doc.get("user_restrictions", [])
            ) > len(existing_restrictions):
                doc.save(ignore_permissions=True)
                frappe.db.commit()

        else:
            # Create a new document
            doc = frappe.new_doc("Control Panel Settings")

            # Add roles
            roles = get_all_roles()
            for role in roles:
                doc.append("allowed_roles", {"role": role})

            # Add restrictions
            for doc_type in document_types:
                restriction = {
                    "allow": doc_type,
                    "for_value": "",  # Empty string instead of None
                    "is_default": 1,
                    "apply_to_all_doctypes": 1,
                    "required": 0 if doc_type == "Employee" else 1,
                }
                doc.append("user_restrictions", restriction)

            # Insert the new document
            doc.insert(ignore_permissions=True)
            frappe.db.commit()

    except Exception as e:
        frappe.log_error(
            f"Failed to set up Control Panel Settings: {e!s}", "Control Panel Setup"
        )


def after_install():
    """Run after app installation"""
    setup_default_user_restrictions()
