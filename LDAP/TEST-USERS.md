# LDAP Test Users Quick Reference

All test users have password: **`password123`**

## Test Users

### Admin
```
UID: admin
DN: uid=admin,ou=users,dc=example,dc=com
Name: Administrator
Email: admin@example.com
Password: password123
```

### IT Department
```
UID: john.doe
DN: uid=john.doe,ou=users,dc=example,dc=com
Name: John Doe
Title: Senior Developer
Email: john.doe@example.com
Groups: developers, admin
Password: password123

UID: jane.smith
DN: uid=jane.smith,ou=users,dc=example,dc=com
Name: Jane Smith
Title: DevOps Engineer
Email: jane.smith@example.com
Groups: developers
Password: password123
```

### Development Team
```
UID: bob.wilson
DN: uid=bob.wilson,ou=users,dc=example,dc=com
Name: Bob Wilson
Title: Junior Developer
Email: bob.wilson@example.com
Groups: developers
Password: password123
```

### Management
```
UID: alice.johnson
DN: uid=alice.johnson,ou=users,dc=example,dc=com
Name: Alice Johnson
Title: IT Manager
Email: alice.johnson@example.com
Groups: managers
Password: password123

UID: charlie.brown
DN: uid=charlie.brown,ou=users,dc=example,dc=com
Name: Charlie Brown
Title: Project Manager
Email: charlie.brown@example.com
Groups: managers
Password: password123
```

### Support Team
```
UID: david.lee
DN: uid=david.lee,ou=users,dc=example,dc=com
Name: David Lee
Title: Support Engineer
Email: david.lee@example.com
Groups: support
Password: password123

UID: emma.davis
DN: uid=emma.davis,ou=users,dc=example,dc=com
Name: Emma Davis
Title: Support Specialist
Email: emma.davis@example.com
Groups: support
Password: password123
```

### QA & Product
```
UID: frank.miller
DN: uid=frank.miller,ou=users,dc=example,dc=com
Name: Frank Miller
Title: QA Engineer
Email: frank.miller@example.com
Password: password123

UID: grace.taylor
DN: uid=grace.taylor,ou=users,dc=example,dc=com
Name: Grace Taylor
Title: Product Manager
Email: grace.taylor@example.com
Password: password123
```

### Service Accounts
```
UID: ldap-sync
DN: uid=ldap-sync,ou=services,dc=example,dc=com
Name: LDAP Sync Service
Email: ldap-sync@example.com
Password: password123

UID: backup-service
DN: uid=backup-service,ou=services,dc=example,dc=com
Name: Backup Service
Email: backup-service@example.com
Password: password123
```

## Groups

- **admin** - Contains: admin
- **developers** - Contains: john.doe, jane.smith, bob.wilson
- **managers** - Contains: alice.johnson, charlie.brown
- **support** - Contains: david.lee, emma.davis

## Quick Test Commands

### Test LDAP Connectivity
```bash
ldapsearch -x -h localhost -p 3389 -b "dc=example,dc=com" -s base "(objectclass=*)"
```

### Authenticate as a User
```bash
ldapwhoami -x -D "uid=john.doe,ou=users,dc=example,dc=com" -w password123 -h localhost -p 3389
```

### List All Users
```bash
ldapsearch -x -h localhost -p 3389 -b "ou=users,dc=example,dc=com" "(objectClass=inetOrgPerson)"
```

### List All Groups
```bash
ldapsearch -x -h localhost -p 3389 -b "ou=groups,dc=example,dc=com" "(objectClass=groupOfNames)"
```

## Testing Scenarios

### 1. Basic Authentication
- Login: `john.doe` / `password123`
- Expected: Success, user in developers group

### 2. Service Account Testing
- Login: `ldap-sync` / `password123`
- Expected: Success, can authenticate as service account

### 3. Group Membership
- Search members of developers group
- Expected: john.doe, jane.smith, bob.wilson

### 4. Backup/Restore Testing
- Add admin: `cn=admin,dc=example,dc=com` / `admin_password`
- Create a backup of all users
- Verify all 10 users + 2 service accounts are backed up
- Restore and verify all entries are present

### 5. Permission Testing
- Test readonly user: `cn=readonly,dc=example,dc=com` / `readonly_password`
- Should be able to search/read
- Should NOT be able to modify/delete

## Database Stats

**Total Entries:**
- 1 Domain entry
- 6 Organizational Units
- 4 Groups
- 10 Users
- 2 Service Accounts
- **Total: 23 entries**

Perfect for testing backup/restore functionality!
