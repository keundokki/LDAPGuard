# Port Configuration Note

## ⚠️ Important: Port Numbers Changed

The LDAP test environment uses **unprivileged ports** (> 1024) for compatibility with rootless podman/docker.

### Port Mappings

| Service | Port | Notes |
|---------|------|-------|
| LDAP | **3389** | Forwarded to container port 389 |
| LDAPS | **6363** | Forwarded to container port 636 |
| PHPLDAPAdmin | **6680** | Standard HTTP port |

## Why Not Port 389?

Port 389 is a privileged port (< 1024) that requires:
- Running with root/sudo
- Special system configuration (sysctl)
- Elevated privileges

For development, using port **3389** is simpler and doesn't require root access.

## Using with LDAPGuard

### Configuration
When adding an LDAP server in LDAPGuard, use:
```
Host:     localhost
Port:     3389        ← Use 3389, NOT 389
Base DN:  dc=example,dc=com
```

### From Command Line
All `ldapsearch`, `ldapadd`, etc. commands use **port 3389**:
```bash
ldapsearch -x -h localhost -p 3389 -b "dc=example,dc=com" "(cn=*)"
```

## What If I Need Port 389?

### Option 1: Run with Docker Desktop (macOS/Windows)
Docker Desktop has built-in elevated privileges:
```bash
# Change docker-compose.yml back:
ports:
  - "389:389"    # ← Change from 3389:389

# Start normally
docker-compose up -d
```

### Option 2: Configure System (Linux)
If you're on Linux with rootless podman and want port 389:
```bash
# Edit /etc/sysctl.conf and add:
net.ipv4.ip_unprivileged_port_start=389

# Apply:
sudo sysctl -p

# Then change docker-compose.yml:
ports:
  - "389:389"

# Start with podman:
podman-compose up -d
```

### Option 3: Run with Sudo (Not Recommended)
```bash
sudo podman-compose up -d
```
⚠️ Not recommended - creates permission issues with data directories

## Default Configuration (Current)

The `docker-compose.yml` is pre-configured for:
- ✅ Rootless podman (no sudo needed)
- ✅ Docker Desktop
- ✅ Standard docker-compose
- ✅ No special system configuration needed

**Just use port 3389 and it will work!** 🚀

## FAQs

**Q: Do I need to change anything else?**  
A: No, just use port 3389 in LDAPGuard. Everything else is the same.

**Q: Will backups differ?**  
A: No, the data is identical. Port 3389 vs 389 doesn't affect backup content.

**Q: Can I use a different port?**  
A: Yes, edit `docker-compose.yml` and change `3389:389` to any unprivileged port (e.g., `5389:389`)

**Q: Does this affect performance?**  
A: No, performance is identical. Only the network binding port changes.

**Q: What ports are unprivileged?**  
A: Any port > 1024. Common choices:
- 3389 (RDP, but available here)
- 5389 (commonly available)
- 8389 (another choice)
- 10389 (yet another)

---

**TL;DR:** Use **port 3389** with LDAPGuard. The environment will work without sudo or special configuration. 🎉
