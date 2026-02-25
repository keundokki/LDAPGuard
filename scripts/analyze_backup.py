"""Analyze backup LDIF for broken references."""
import sys

path = sys.argv[1] if len(sys.argv) > 1 else '/app/backups/LDAP DEV_full_20260225_073553.ldif'

manager_entries = 0
ssoroles_entries = 0
total_entries = 0
manager_targets = set()
ssoroles_vals = set()
all_dns = set()

with open(path, 'r') as f:
    current_dn = None
    has_manager = False
    has_ssoroles = False
    for line in f:
        line = line.rstrip()
        if line.startswith('dn: '):
            if current_dn:
                total_entries += 1
                if has_manager:
                    manager_entries += 1
                if has_ssoroles:
                    ssoroles_entries += 1
            current_dn = line[4:]
            all_dns.add(current_dn)
            has_manager = False
            has_ssoroles = False
        elif line.startswith('manager: '):
            has_manager = True
            manager_targets.add(line[9:])
        elif line.startswith('ssoRoles: '):
            has_ssoroles = True
            ssoroles_vals.add(line[10:])
    if current_dn:
        total_entries += 1

missing_managers = sorted(m for m in manager_targets if m not in all_dns)
missing_roles = sorted(r for r in ssoroles_vals if r not in all_dns)

print(f"Total entries: {total_entries}")
print(f"Entries with manager: {manager_entries}")
print(f"Entries with ssoRoles: {ssoroles_entries}")
print(f"Unique manager targets: {len(manager_targets)}")
print(f"Manager targets MISSING from backup: {len(missing_managers)}")
for m in missing_managers:
    print(f"  MISSING: {m}")
print()
print(f"Unique ssoRoles values: {len(ssoroles_vals)}")
print(f"ssoRoles targets MISSING from backup: {len(missing_roles)}")
for r in missing_roles:
    print(f"  MISSING: {r}")
