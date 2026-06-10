import os
import glob

replacements = {
    "EventCategory.AUTH": "EventCategory.auth",
    "EventCategory.USER_MGMT": "EventCategory.user_mgmt",
    "EventCategory.ROLE_MGMT": "EventCategory.role_mgmt",
    "EventCategory.TENANT_MGMT": "EventCategory.tenant_mgmt"
}

target_dir = r"d:\projects\truck_management\truck-management-product\apps\backend\app\services"
files = glob.glob(os.path.join(target_dir, "*.py"))

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    modified = False
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            modified = True

    if modified:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file}")
