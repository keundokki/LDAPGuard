# OpenLDAP Installation (Production LDAP VM)

This guide installs OpenLDAP directly on the LDAP VM (no containers).

## 1) Install Packages

```bash
sudo apt update
sudo apt install -y slapd ldap-utils
```

## 2) Reconfigure Slapd (Recommended)

```bash
sudo dpkg-reconfigure slapd
```

Suggested answers:
- Omit OpenLDAP server configuration? **No**
- DNS domain name: **production.local**
- Organization name: **Production LDAP**
- Administrator password: **set a strong password**
- Database backend: **MDB**
- Remove database when purging slapd? **No**
- Move old database? **Yes**

## 3) Verify Access

```bash
ldapwhoami -H ldap://localhost -D cn=admin,dc=production,dc=local -W
```

Expected: `dn:cn=admin,dc=production,dc=local`

## 4) Open Firewall (If Needed)

Allow LDAP (389) and LDAPS (636) from the production LDAPGuard VM.

## 5) Connect LDAPGuard (Production VM)

In the LDAPGuard production `.env`:

```
LDAP_HOST=production-ldap-vm
LDAP_PORT=389
LDAP_BIND_DN=cn=admin,dc=production,dc=local
LDAP_PASSWORD=your-admin-password
```

Then restart LDAPGuard:

```bash
docker-compose up -d
```
