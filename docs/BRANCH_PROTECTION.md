# Branch Protection Configuration Guide

This document provides the exact settings to configure branch and tag protection rules for the LDAPGuard repository.

## Quick Links

- Repository Settings: https://github.com/keundokki/LDAPGuard/settings
- Branch Protection: https://github.com/keundokki/LDAPGuard/settings/branches
- Tag Protection: https://github.com/keundokki/LDAPGuard/settings/tag_protection

---

## 1. Main Branch Protection (Production)

**Navigate to:** Settings → Branches → Add rule

### Configuration:

**Branch name pattern:** `main`

#### Protect matching branches:
- ✅ **Require a pull request before merging**
  - ✅ Require approvals: **1**
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require review from Code Owners (if CODEOWNERS file exists)
  - ✅ Require approval of the most recent reviewable push

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - Status checks to require (add when CI/CD is configured):
    - `build`
    - `test`
    - `lint`
    - `security-scan`

- ✅ **Require conversation resolution before merging**

- ✅ **Require signed commits** (recommended for security)

- ✅ **Require linear history** (optional - prevents merge commits)

- ✅ **Include administrators** (enforce rules on repo admins too)

#### Rules applied to everyone including administrators:
- ❌ **Allow force pushes** - KEEP DISABLED
- ❌ **Allow deletions** - KEEP DISABLED

**Save changes**

---

## 2. Release Branch Protection

**Navigate to:** Settings → Branches → Add rule

### Configuration:

**Branch name pattern:** `release-*`

#### Protect matching branches:
- ✅ **Require a pull request before merging** (optional for releases)
  - Require approvals: **1** (release manager)

- ✅ **Require status checks to pass before merging**
  - Status checks: `build`, `test`

- ✅ **Restrict who can push to matching branches** (optional)
  - Add: Release managers only

#### Rules applied to everyone:
- ❌ **Allow force pushes** - KEEP DISABLED
- ❌ **Allow deletions** - KEEP DISABLED

**Save changes**

---

## 3. Tag Protection Rules

**Navigate to:** Settings → Tags → New rule

### Configuration:

**Tag name pattern:** `v*`

#### Settings:
- ✅ **Require signed commits** (recommended)
- ✅ **Restrict who can create matching tags** (optional)
  - Add: Maintainers/Release managers only

**Note:** Tag protection prevents deletion and modification of tags matching the pattern.

**Save changes**

---

## 4. Rulesets (Alternative Modern Approach)

GitHub now offers "Rulesets" as a more flexible alternative to classic branch protection rules.

**Navigate to:** Settings → Rules → Rulesets → New ruleset → New branch ruleset

### Ruleset for Main Branch:

**Ruleset name:** `Production Branch Protection`

**Enforcement status:** Active

**Bypass list:** (empty - no one can bypass)

**Target branches:**
- Add target: `main`

**Rules:**
- ✅ Restrict deletions
- ✅ Require a pull request before merging
  - Required approvals: 1
  - Dismiss stale pull request approvals: Yes
- ✅ Require status checks to pass
- ✅ Block force pushes
- ✅ Require signed commits

---

## 5. Repository Settings Checklist

**Navigate to:** Settings → General

### Security:
- ✅ Enable "Automatically delete head branches" (cleanup after PR merge)
- ✅ Enable "Allow merge commits" or choose your preferred merge method:
  - Merge commits (preserves history)
  - Squash merging (cleaner history)
  - Rebase merging (linear history)

### Pull Requests:
- ✅ Allow squash merging (recommended)
- ✅ Allow auto-merge
- ✅ Automatically delete head branches

---

## Current Protected Branches Summary

| Branch Pattern | Protection Level | Key Rules |
|---------------|------------------|-----------|
| `main` | Maximum | PR required, 1 approval, no force push, no delete |
| `release-*` | High | PR optional, no force push, no delete |
| Feature/hotfix | None | Flexible for development |

## Current Protected Tags Summary

| Tag Pattern | Protected | Signed Commits |
|-------------|-----------|----------------|
| `v*` | Yes | Recommended |

---

## Workflow After Configuration

### Creating a Release:
1. Create release branch: `git checkout -b release-0.0.6`
2. Make changes, test, commit
3. Push: `git push origin release-0.0.6`
4. Create PR: `release-0.0.6` → `main`
5. Get approval
6. Merge PR
7. Tag main: `git tag -a v0.0.6 -m "Release notes"`
8. Push tag: `git push origin v0.0.6`
9. Delete release branch: `git push origin --delete release-0.0.6`

### Hotfix Process:
1. Create hotfix branch from main: `git checkout -b hotfix/critical-bug`
2. Fix, test, commit
3. Create PR to main
4. Merge after approval
5. Tag new patch version: `v0.0.6-patch.1`

---

## Status Check Configuration (Future)

When you add CI/CD (GitHub Actions), require these checks:

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  build:
    # Build and test job
  
  lint:
    # Linting job
  
  security:
    # Security scanning job
```

Then add these as required status checks in branch protection.

---

## Enforcement Timeline

✅ **Immediate:**
- Main branch protection
- Tag protection for `v*`

⏰ **Within 1 week:**
- Release branch protection
- Status checks when CI/CD is set up

📅 **Ongoing:**
- Review and update rules as team grows
- Add Code Owners file
- Configure additional security scanning

---

## Need Help?

- GitHub Docs: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches
- Tag Protection: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/configuring-tag-protection-rules
