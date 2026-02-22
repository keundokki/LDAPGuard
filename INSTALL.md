# LDAPGuard Installation Guide

This guide will help you install LDAPGuard in under 5 minutes.

## Prerequisites

Before installing, make sure you have:

- [ ] **Docker** or **Podman** installed
- [ ] **Docker Compose** or **Podman Compose** installed  
- [ ] **Git** installed
- [ ] Internet connection
- [ ] 4GB RAM minimum (8GB recommended)
- [ ] 20GB disk space

**Don't have these?** See the [Prerequisites Installation](#prerequisites-installation) section below.

---

## Installation Methods

Choose the method that works best for you:

### Method 1: One-Line Install ⚡ (Recommended)

**Fastest and easiest!** Just copy and paste:

```bash
curl -fsSL https://raw.githubusercontent.com/keundokki/LDAPGuard/main/install.sh | bash
```

**What it does:**
- ✅ Checks your system
- ✅ Asks a few simple questions
- ✅ Generates secure encryption keys
- ✅ Installs and starts LDAPGuard
- ✅ Shows you exactly where to go next

**Time**: ~2-3 minutes

---

### Method 2: Git Clone + Make 🛠️

**For users who want more control:**

```bash
# 1. Clone repository
git clone https://github.com/keundokki/LDAPGuard.git
cd LDAPGuard

# 2. Run installer
make install

# Or for quick install with defaults:
make quick-install
```

**Time**: ~3-4 minutes

---

### Method 3: Manual Installation 📋

**For users who want complete control:**

```bash
# 1. Clone repository
git clone https://github.com/keundokki/LDAPGuard.git
cd LDAPGuard

# 2. Create configuration
cp .env.example .env

# 3. Generate secure keys
export SECRET_KEY=$(openssl rand -hex 32)
export ENCRYPTION_KEY=$(openssl rand -hex 32)
export DB_PASSWORD=$(openssl rand -hex 16)

# 4. Update .env file
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$DB_PASSWORD/" .env
sed -i "s/changeme/$DB_PASSWORD/g" .env

# 5. Start services
docker-compose up -d

# Or with Podman:
podman-compose up -d
```

**Time**: ~5-10 minutes

---

## After Installation

### 1. Access LDAPGuard

Open your web browser and go to:

```
http://localhost:3000
```

### 2. Login

Use the default credentials:

- **Username**: `admin`
- **Password**: `admin`

⚠️ **IMPORTANT**: Change this password immediately after login!

### 3. Change Admin Password

1. Click on the user menu (top right)
2. Select "Change Password"
3. Enter a strong password
4. Click "Change Password"

### 4. Configure Your First LDAP Server

1. Go to the "Servers" tab
2. Click "Add Server"
3. Fill in your LDAP server details:
   - **Name**: Friendly name (e.g., "Production LDAP")
   - **Host**: Your LDAP server hostname/IP
   - **Port**: Usually 389 (LDAP) or 636 (LDAPS)
   - **Base DN**: e.g., `dc=example,dc=com`
   - **Bind DN**: Admin user DN
   - **Bind Password**: Admin password
4. Click "Test Connection" to verify
5. Click "Save"

### 5. Create Your First Backup

1. Go to the "Backups" tab
2. Click "Create Backup"
3. Select your LDAP server
4. Choose backup type (Full recommended for first backup)
5. Click "Create"
6. Watch it complete in real-time!

---

## Verification

Check that everything is working:

```bash
# Method 1: Using Make
make health

# Method 2: Manual check
curl http://localhost:8000/docs
curl http://localhost:3000

# Method 3: Check containers
docker-compose ps
# or: podman-compose ps
```

All containers should show "Up" status.

---

## Troubleshooting

### Problem: "Command not found: docker-compose"

**Solutions:**

```bash
# If you have Docker:
pip install docker-compose

# If you have Podman:
pip install podman-compose

# On macOS with Homebrew:
brew install docker-compose
# or
brew install podman-compose
```

### Problem: "Port already in use"

**Solution**: Change the ports in `docker-compose.yml`:

```yaml
services:
  web:
    ports:
      - "3001:80"  # Changed from 3000
  api:
    ports:
      - "8001:8000"  # Changed from 8000
```

### Problem: "Permission denied"

**Solutions:**

```bash
# Option 1: Fix permissions
sudo chown -R $USER:$USER .

# Option 2: Run with sudo
sudo docker-compose up -d

# Option 3: Add your user to docker group
sudo usermod -aG docker $USER
# Then logout and login again
```

### Problem: Services won't start

**Solution**: Check the logs:

```bash
# View all logs
docker-compose logs

# View specific service
docker-compose logs api
docker-compose logs web
docker-compose logs postgres

# Follow logs in real-time
docker-compose logs -f
```

### Problem: Can't login with admin/admin

**Solution**: The database might not be initialized. Wait 30 seconds and try again, or restart:

```bash
docker-compose restart api
```

---

## Prerequisites Installation

### Install Docker

#### Ubuntu/Debian
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Logout and login again
```

#### macOS
```bash
brew install --cask docker
# Or download from: https://www.docker.com/products/docker-desktop
```

#### Windows
Download Docker Desktop from: https://www.docker.com/products/docker-desktop

### Install Podman (Alternative to Docker)

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install podman podman-compose
```

#### macOS
```bash
brew install podman podman-compose
```

#### Fedora/RHEL
```bash
sudo dnf install podman podman-compose
```

### Install Git

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install git
```

#### macOS
```bash
brew install git
# Or use Xcode Command Line Tools:
xcode-select --install
```

#### Windows
Download from: https://git-scm.com/download/win

---

## Uninstallation

If you want to remove LDAPGuard:

```bash
# Stop and remove all containers
docker-compose down

# Remove all data (WARNING: This deletes your backups!)
docker-compose down -v

# Remove images
docker-compose down -v --rmi all

# Delete the directory
cd ..
rm -rf LDAPGuard
```

---

## Next Steps

Now that LDAPGuard is installed:

1. ✅ Change admin password
2. ✅ Add LDAP server
3. ✅ Create first backup
4. 📚 Read the [Quick Reference](QUICK_REFERENCE.md)
5. 📖 Check the [README](README.md) for advanced features
6. ⚙️ Set up scheduled backups
7. 🔔 Configure webhooks (optional)
8. 📊 Set up monitoring (optional)

---

## Getting Help

- **Quick Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
- **Full Documentation**: [README.md](README.md)
- **API Documentation**: http://localhost:8000/docs
- **GitHub Issues**: https://github.com/keundokki/LDAPGuard/issues

---

**Welcome to LDAPGuard! 🚀**

You now have a powerful, secure LDAP backup solution running on your infrastructure.
