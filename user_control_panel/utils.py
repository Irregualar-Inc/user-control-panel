import frappe


def sync_permissions_async(employee_user_id, restrictions):
    """
    Idempotent sync of user permissions:
      ✅ Update if permission exists and differs
      ✅ Create if new
      🗑️ Delete if removed
      🚫 Skip if identical (no redundant writes)

    Args:
        employee_user_id (str): User ID to sync permissions for
        restrictions (list): List of permission dicts or objects
    """
    if not restrictions:
        return
    try:
        desired_map = {}
        for perm in restrictions:
            # Normalize dict/object to unified structure
            perm_data = (
                perm
                if isinstance(perm, dict)
                else {
                    "allow": perm.allow,
                    "for_value": perm.for_value,
                    "applicable_for": getattr(perm, "applicable_for", "") or "",
                    "is_default": getattr(perm, "is_default", 0),
                    "apply_to_all_doctypes": getattr(perm, "apply_to_all_doctypes", 0),
                    "hide_descendants": getattr(perm, "hide_descendants", 0),
                }
            )

            key = (
                perm_data["user"],
                perm_data["allow"],
                perm_data["for_value"],
                perm_data["applicable_for"] or "",
                perm_data["apply_to_all_doctypes"],
            )
            desired_map[key] = perm_data

        if not desired_map:
            return


        # Fetch all relevant existing permissions for this user
        existing_perms = frappe.get_all(
            "User Permission",
            filters={"user": employee_user_id},
            fields=[
                "name",
                "user",
                "allow",
                "for_value",
                "applicable_for",
                "is_default",
                "apply_to_all_doctypes",
                "hide_descendants",
            ],
        )

        existing_map = {}
        for p in existing_perms:
            key = (p.user, p.allow, p.for_value, p.applicable_for or "", p.apply_to_all_doctypes)
            existing_map[key] = p

        desired_keys = set(desired_map.keys())

        changed = False  # flag to avoid unnecessary commits
        
        # --- Delete permissions no longer desired ---
        for key, existing in existing_map.items():
            if key not in desired_keys:
                frappe.delete_doc("User Permission", existing.name, ignore_permissions=True)
                changed = True

        # --- Upsert (update or create) ---
        for key, perm_data in desired_map.items():
            existing = existing_map.get(key)
            if existing:
                # Check for differences before saving (idempotent)
                needs_update = (
                    existing.is_default != perm_data.get("is_default", 0)
                    or existing.apply_to_all_doctypes
                    != perm_data.get("apply_to_all_doctypes", 0)
                    or (existing.applicable_for or "")
                    != perm_data.get("applicable_for", "")
                    or existing.hide_descendants != perm_data.get("hide_descendants", 0)
                )
                if needs_update:
                    doc = frappe.get_doc("User Permission", existing.name)
                    doc.update(perm_data)
                    doc.save()
                    changed = True
            else:
                new_doc = frappe.new_doc("User Permission")
                new_doc.update(
                    {
                        **perm_data,
                    }
                )
                try:
                    new_doc.insert()
                    changed = True
                except frappe.DuplicateEntryError as e:
                    raise e

        # Commit only if something changed
        if changed:
            frappe.db.commit()
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Sync Permissions Failed")
        raise e
