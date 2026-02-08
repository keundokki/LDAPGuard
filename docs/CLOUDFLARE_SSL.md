# Cloudflare SSL/TLS Configuration Guide

This guide explains how to configure LDAPGuard with Cloudflare for SSL/TLS certificates.

## 📋 Prerequisites

- Cloudflare account with your domain configured
- Traefik installed as your Ingress Controller in Kubernetes
- LDAPGuard deployed (Helm or Kustomize)

## 🔐 SSL/TLS Options

### Option 1: Cloudflare DNS + Let's Encrypt (Recommended)

**Best for:** Automatic certificate management, widely trusted certificates

This uses Traefik's ACME DNS-01 challenge with Cloudflare API to automatically obtain and renew Let's Encrypt certificates.

#### Step 1: Create Cloudflare API Token

1. Go to Cloudflare Dashboard → My Profile → API Tokens
2. Click "Create Token"
3. Use "Edit zone DNS" template
4. Select your domain under "Zone Resources"
5. Copy the API token

#### Step 2: Create Kubernetes Secret

```bash
kubectl create secret generic cloudflare-api-token \
  --from-literal=api-token=YOUR_CLOUDFLARE_API_TOKEN \
  -n traefik  # Or wherever Traefik is installed
```

#### Step 3: Configure Traefik

Add to your Traefik Helm values or configuration:

```yaml
# Traefik Helm values.yaml
additionalArguments:
  - "--certificatesresolvers.cloudflare.acme.email=your-email@domain.com"
  - "--certificatesresolvers.cloudflare.acme.storage=/data/acme.json"
  - "--certificatesresolvers.cloudflare.acme.dnschallenge.provider=cloudflare"
  - "--certificatesresolvers.cloudflare.acme.dnschallenge.resolvers=1.1.1.1:53,1.0.0.1:53"
  - "--certificatesresolvers.cloudflare.acme.dnschallenge.delaybeforecheck=30"

env:
  - name: CF_DNS_API_TOKEN
    valueFrom:
      secretKeyRef:
        name: cloudflare-api-token
        key: api-token

persistence:
  enabled: true  # Required for acme.json storage
```

Or via command line arguments:

```bash
helm upgrade traefik traefik/traefik \
  --set "additionalArguments={--certificatesresolvers.cloudflare.acme.email=your@email.com,--certificatesresolvers.cloudflare.acme.storage=/data/acme.json,--certificatesresolvers.cloudflare.acme.dnschallenge.provider=cloudflare}" \
  --set "env[0].name=CF_DNS_API_TOKEN" \
  --set "env[0].valueFrom.secretKeyRef.name=cloudflare-api-token" \
  --set "env[0].valueFrom.secretKeyRef.key=api-token"
```

#### Step 4: Deploy LDAPGuard with Cloudflare Resolver

**Helm Deployment:**

```bash
helm install ldapguard ./helm -n ldapguard \
  --set ingress.enabled=true \
  --set ingress.domain=ldapguard.yourdomain.com \
  --set ingress.tls.certResolver=cloudflare
```

Or in `values.yaml`:

```yaml
ingress:
  enabled: true
  domain: ldapguard.yourdomain.com
  tls:
    certResolver: cloudflare
```

**Kustomize Deployment:**

Update IngressRoute to use `certResolver: cloudflare`:

```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: ldapguard-https
  namespace: ldapguard
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`ldapguard.yourdomain.com`)
      kind: Rule
      services:
        - name: web
          port: 80
  tls:
    certResolver: cloudflare  # Use Cloudflare DNS resolver
```

#### Step 5: Configure Cloudflare Dashboard

1. Go to Cloudflare Dashboard → SSL/TLS
2. Set SSL/TLS encryption mode to **"Full (strict)"**
3. (Optional) Enable features:
   - Always Use HTTPS
   - Automatic HTTPS Rewrites
   - Minimum TLS Version: 1.2

---

### Option 2: Cloudflare Origin Certificates

**Best for:** Long-lived certificates (15 years), no renewal needed, free

Cloudflare issues certificates specifically for the origin server (your Kubernetes cluster).

#### Step 1: Generate Origin Certificate

1. Go to Cloudflare Dashboard → SSL/TLS → Origin Server
2. Click "Create Certificate"
3. Options:
   - Let Cloudflare generate a private key and CSR
   - Choose validity: 15 years (recommended)
   - Hostnames: `ldapguard.yourdomain.com` or `*.yourdomain.com`
4. Click "Create"
5. **Download both:**
   - Origin Certificate (save as `origin-cert.pem`)
   - Private Key (save as `origin-key.pem`)

#### Step 2: Create Kubernetes Secret

```bash
kubectl create secret tls cloudflare-origin-cert \
  --cert=origin-cert.pem \
  --key=origin-key.pem \
  -n ldapguard
```

#### Step 3: Deploy LDAPGuard with Origin Certificate

**Helm Deployment:**

```bash
helm install ldapguard ./helm -n ldapguard \
  --set ingress.enabled=true \
  --set ingress.domain=ldapguard.yourdomain.com \
  --set ingress.tls.secretName=cloudflare-origin-cert \
  --set ingress.tls.certResolver=""  # Clear certResolver when using secretName
```

Or in `values.yaml`:

```yaml
ingress:
  enabled: true
  domain: ldapguard.yourdomain.com
  tls:
    secretName: cloudflare-origin-cert
    certResolver: ""  # Leave empty when using secretName
```

**Kustomize Deployment:**

Apply the patch:

```bash
kubectl apply -f k8s/examples/patches/cloudflare-origin-cert.yaml
```

Or use as a kustomize patch in `kustomization.yaml`:

```yaml
patches:
  - path: examples/patches/cloudflare-origin-cert.yaml
```

#### Step 4: Configure Cloudflare Dashboard

1. Go to Cloudflare Dashboard → SSL/TLS
2. Set SSL/TLS encryption mode to **"Full (strict)"**
   - ⚠️ Important: "Full (strict)" validates the origin certificate
   - Don't use "Flexible" or "Full" - they won't work correctly

---

### Option 3: Cloudflare Proxied Mode (Cloudflare Handles SSL)

**Best for:** Simplest setup, but less control

Let Cloudflare terminate SSL and proxy requests to your cluster over HTTP.

#### Configuration

1. **Cloudflare Dashboard:**
   - SSL/TLS mode: "Flexible" or "Full"
   - Orange cloud (proxied) enabled for DNS record

2. **LDAPGuard:**
   - Don't enable ingress with TLS
   - Expose web service as LoadBalancer or NodePort on HTTP (port 80)

```yaml
# Helm values
ingress:
  enabled: false  # Don't use Traefik ingress

service:
  web:
    type: LoadBalancer  # or NodePort
    port: 80
```

3. **DNS:**
   - Point `ldapguard.yourdomain.com` to your cluster's LoadBalancer IP
   - Enable Cloudflare proxy (orange cloud)

⚠️ **Limitation:** You lose end-to-end encryption between Cloudflare and your cluster.

---

## 🔍 Comparison

| Feature | DNS + Let's Encrypt | Origin Certificate | Proxied Mode |
|---------|---------------------|-------------------|--------------|
| **Certificate Issuer** | Let's Encrypt | Cloudflare | Cloudflare |
| **Certificate Validity** | 90 days (auto-renewed) | 15 years | N/A |
| **Publicly Trusted** | ✅ Yes | ❌ No (Cloudflare only) | ✅ Yes |
| **Setup Complexity** | Medium | Easy | Very Easy |
| **End-to-End Encryption** | ✅ Yes | ✅ Yes | ❌ No |
| **API Token Required** | ✅ Yes | ❌ No | ❌ No |
| **Wildcard Support** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Best For** | Production | Private/internal | Simple setups |

**Recommendation:** Use **Option 1 (DNS + Let's Encrypt)** for production or **Option 2 (Origin Certificates)** for easier management.

---

## ✅ Verification

After deploying, verify your setup:

### 1. Check Certificate

```bash
# Check IngressRoute
kubectl get ingressroute -n ldapguard

# Describe IngressRoute
kubectl describe ingressroute ldapguard-https -n ldapguard

# Check Traefik logs
kubectl logs -l app.kubernetes.io/name=traefik -n traefik --tail=100 | grep -i acme
```

### 2. Test HTTPS Access

```bash
# Test from outside cluster
curl -I https://ldapguard.yourdomain.com

# Check certificate details
openssl s_client -connect ldapguard.yourdomain.com:443 -servername ldapguard.yourdomain.com < /dev/null 2>/dev/null | openssl x509 -noout -text | grep -A 2 "Subject:"
```

### 3. Verify Cloudflare SSL Mode

Go to Cloudflare Dashboard → SSL/TLS:
- Should show **"Full (strict)"** for Options 1 & 2
- Should show **"Active"** or **"Universal"** status

### 4. Test Redirect

```bash
# HTTP should redirect to HTTPS
curl -I http://ldapguard.yourdomain.com
# Should return: 301 or 302 redirect to https://
```

---

## 🐛 Troubleshooting

### Certificate Not Issued

**For Let's Encrypt + Cloudflare DNS:**

```bash
# Check Traefik logs
kubectl logs -l app.kubernetes.io/name=traefik -n traefik | grep -i cloudflare

# Common issues:
# 1. Invalid API token
kubectl get secret cloudflare-api-token -n traefik -o yaml

# 2. DNS propagation delay - increase delayBeforeCheck
# 3. Rate limit - Let's Encrypt has limits (5 certs/week per domain)
```

**For Origin Certificate:**

```bash
# Verify secret exists
kubectl get secret cloudflare-origin-cert -n ldapguard

# Check secret content
kubectl get secret cloudflare-origin-cert -n ldapguard -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -text
```

### 502 Bad Gateway

- Check Cloudflare SSL mode is "Full (strict)" (not Flexible)
- Verify LDAPGuard pods are running: `kubectl get pods -n ldapguard`
- Check service endpoints: `kubectl get endpoints -n ldapguard`

### Too Many Redirects

- Cloudflare SSL mode should NOT be "Flexible" with HTTPS backend
- Check "Always Use HTTPS" setting in Cloudflare

### Certificate Mismatch

- Verify domain in IngressRoute matches Cloudflare DNS
- Check certificate SANs match your domain

---

## 📚 Additional Resources

- [Traefik ACME Documentation](https://doc.traefik.io/traefik/https/acme/)
- [Cloudflare Origin Certificates](https://developers.cloudflare.com/ssl/origin-configuration/origin-ca/)
- [Cloudflare SSL Modes](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/)
- [LDAPGuard Helm Configuration](../helm/README.md)

---

## 💡 Example: Complete Setup

Here's a complete example using Cloudflare DNS + Let's Encrypt:

```bash
# 1. Create Cloudflare API token secret
kubectl create secret generic cloudflare-api-token \
  --from-literal=api-token=YOUR_TOKEN \
  -n traefik

# 2. Update Traefik (if needed)
helm upgrade traefik traefik/traefik -n traefik \
  --set "additionalArguments={--certificatesresolvers.cloudflare.acme.email=you@example.com,--certificatesresolvers.cloudflare.acme.storage=/data/acme.json,--certificatesresolvers.cloudflare.acme.dnschallenge.provider=cloudflare}" \
  --set "env[0].name=CF_DNS_API_TOKEN" \
  --set "env[0].valueFrom.secretKeyRef.name=cloudflare-api-token" \
  --set "env[0].valueFrom.secretKeyRef.key=api-token"

# 3. Create LDAPGuard secrets
kubectl create namespace ldapguard
kubectl create secret generic ldapguard-secrets \
  --from-literal=POSTGRES_PASSWORD="$(openssl rand -base64 24)" \
  --from-literal=SECRET_KEY="$(openssl rand -base64 32)" \
  --from-literal=ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --from-literal=DATABASE_URL="postgresql+asyncpg://ldapguard:PASSWORD@postgres:5432/ldapguard" \
  -n ldapguard

# 4. Deploy LDAPGuard with Helm
helm install ldapguard ./helm -n ldapguard \
  --set ingress.enabled=true \
  --set ingress.domain=ldapguard.yourdomain.com \
  --set ingress.tls.certResolver=cloudflare

# 5. Set Cloudflare SSL mode to "Full (strict)" in dashboard

# 6. Wait for certificate (can take 1-2 minutes)
kubectl logs -l app.kubernetes.io/name=traefik -n traefik -f

# 7. Test
curl -I https://ldapguard.yourdomain.com
```

Done! 🎉
