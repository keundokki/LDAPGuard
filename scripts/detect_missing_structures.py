"""
Analyze backup LDIF for missing ssoRoles and manager references.
Works for any application/structure, not just cognos.
"""
import sys
from collections import defaultdict

backup_file = sys.argv[1] if len(sys.argv) > 1 else 'backups/LDAP DEV_full_20260225_073553.ldif'

# Parse all DNs and references
all_dns = set()
ssoroles_refs = defaultdict(list)  # entry_dn -> [role_dns]
manager_refs = defaultdict(list)   # entry_dn -> [manager_dns]

print(f"Analyzing {backup_file}...")
with open(backup_file, 'r') as f:
    current_dn = None
    for line in f:
        line = line.rstrip()
        
        if line.startswith('dn: '):
            current_dn = line[4:]
            all_dns.add(current_dn)
        elif line.startswith('ssoRoles: '):
            role_dn = line[10:]
            if current_dn:
                ssoroles_refs[current_dn].append(role_dn)
        elif line.startswith('manager: '):
            manager_dn = line[9:]
            if current_dn:
                manager_refs[current_dn].append(manager_dn)

# Find missing references
missing_ssoroles = set()
for entry_dn, roles in ssoroles_refs.items():
    for role_dn in roles:
        if role_dn not in all_dns:
            missing_ssoroles.add(role_dn)

missing_managers = set()
for entry_dn, managers in manager_refs.items():
    for manager_dn in managers:
        if manager_dn not in all_dns:
            missing_managers.add(manager_dn)

print(f"\nBackup analysis:")
print(f"  Total DNs: {len(all_dns)}")
print(f"  Entries with ssoRoles: {len(ssoroles_refs)}")
print(f"  Entries with manager: {len(manager_refs)}")

# Analyze missing ssoRoles targets
if missing_ssoroles:
    print(f"\n⚠️  Missing ssoRoles target structures ({len(missing_ssoroles)}):")
    
    # Group by application structure
    app_structures = defaultdict(set)
    for dn in missing_ssoroles:
        # Extract application structure (ou=roles,ou=APP,ou=applications,...)
        parts = dn.lower().split(',')
        for i, part in enumerate(parts):
            if part.startswith('ou='):
                app_structures[dn[:dn.lower().index(part) + len(part)]].add(dn)
    
    for structure, entries in sorted(app_structures.items()):
        print(f"\n  Needed structure: {structure}/")
        print(f"  Number of entries referencing this: {len(entries)}")
        print(f"  Examples:")
        for dn in sorted(list(entries)[:3]):
            print(f"    - {dn}")

# Analyze missing managers
if missing_managers:
    print(f"\n⚠️  Missing manager references ({len(missing_managers)}):")
    print(f"  Total unique missing manager DNs: {len(missing_managers)}")
    
    sample_size = min(5, len(missing_managers))
    print(f"  Examples of missing managers:")
    for dn in sorted(list(missing_managers)[:sample_size]):
        # Find entries referencing this manager
        referrers = [e for e, ms in manager_refs.items() if dn in ms]
        print(f"    - {dn}")
        print(f"      Referenced by {len(referrers)} entries")

# Summary and recommendations
print(f"\n📋 Summary:")
if not missing_ssoroles and not missing_managers:
    print("  ✅ All references are satisfied. Backup is complete.")
else:
    if missing_ssoroles:
        print(f"  ⚠️  {len(missing_ssoroles)} missing ssoRoles targets")
        print("     → Create the missing ou=roles structures under applications")
    if missing_managers:
        print(f"  ⚠️  {len(missing_managers)} missing manager references")
        print("     → Ensure all manager user entries are restored before employees")

print(f"\n💡 Options:")
print("  1. Create/restore missing structures (ou=roles, ou=applications, etc.)")
print("  2. Remove ssoRoles/manager attributes from entries during restore")
print("  3. Use multi-backup restore (restore managers first, then employees)")
