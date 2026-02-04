# Example LDAP Server Configurations

This file shows example configurations for various LDAP servers.

## OpenLDAP

```json
{
  "name": "OpenLDAP Production",
  "host": "ldap.example.com",
  "port": 389,
  "use_ssl": false,
  "base_dn": "dc=example,dc=com",
  "bind_dn": "cn=admin,dc=example,dc=com",
  "bind_password": "admin_password",
  "description": "Main OpenLDAP server"
}
```

## Active Directory

```json
{
  "name": "Active Directory",
  "host": "ad.example.com",
  "port": 389,
  "use_ssl": false,
  "base_dn": "DC=example,DC=com",
  "bind_dn": "CN=LDAPGuard Service,OU=Service Accounts,DC=example,DC=com",
  "bind_password": "service_account_password",
  "description": "Active Directory domain controller"
}
```
