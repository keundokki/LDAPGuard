# Branch Protection Configuration Guide

This document provides exact GitHub branch protection settings for LDAPGuard repository.

**Repository:** keundokki/LDAPGuard

---

## Table of Contents

1. [Main Branch Protection](#1-main-branch-protection)
2. [Development Branch Protection](#2-development-branch-protection)
3. [Release Branch Protection](#3-release-branch-protection)
4. [Feature Branch Guidelines](#4-feature-branch-guidelines)
5. [Tag Protection](#5-tag-protection)

---

## 1. Main Branch Protection

**Navigate to:** https://github.com/keundokki/LDAPGuard/settings/branch_protection_rules/new

### Configuration:

**Branch name pattern:** `main`

#### Protect matching branches:
- ✅ **Require a pull request before merging**
  - Required approvals: **1**
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require review from Code Owners (if CODEOWNERS file exists)
  - ❌ Require approval of the most recent reviewable push
  - ✅ Require conversation resolution before merging

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - Status checks that are required:
    - `build` (if CI/CD configured)
    - `test` (if CI/CD configured)
    - `lint` (if CI/CD configured)

- ✅ **Require signed commits** (Optional, recommended for production)

- ✅ **Require linear history**
  - Forces merge commits or squash merges, no merge bubbles

- ✅ **Require deployments to succeed before merging** (Optional, if using GitHub deployments)

- ❌ **Do not allow bypassing the above settings**
  - Even admins must follow these rules

- ✅ **Restrict who can push to matching branches**
  - Allow: Repository admins only
  - No force pushes
  - No deletions

- ✅ **Rules applied to administrators**

**Save changes**

---

## 2. Development Branch Protection

**Navigate to:** https://github.com/keundokki/LDAPGuard/settings/branch_protection_rules/new

### Configuration:

**Branch name pattern:** `dev`

#### Protect matching branches:
- ✅ **Require a pull request before merging**
  - Required approvals: **1**
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require conversation resolution before merging

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - Status checks that are required:
    - `build` (if CI/CD configured)
    - `test` (if CI/CD configured)
    - `lint` (if CI/CD configured)

- ❌ **Do NOT require linear history** (allows merge commits from features)

- ❌ **Do NOT restrict pushes** (maintainers can push directly for hotfixes)

- ✅ **Allow force pushes** - DISABLED
  - Keep dev history clean and traceable

- ✅ **Allow deletions** - DISABLED
  - Prevent accidental deletion

**Save changes**

---

## 3. Release Branch Protection

**Navigate to:** https://github.com/keundokki/LDAPGuard/settings/branch_protection_rules/new

### Configuration:

**Branch name pattern:** `release-*`

#### Protect matching branches:
- ✅ **Require a pull request before merging**
  - Required approvals: **1**
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require conversation resolution before merging

- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - Status checks that are required:
    - `build`
    - `test`
    - `security-scan` (if configured)

- ✅ **Require linear history**
  - Keeps release history clean

- ✅ **Restrict who can push to matching branches**
  - Allow: Repository admins and release managers
  - No force pushes
  - No deletions

- ✅ **Require deployments to succeed** (Optional)
  - Staging deployment must pass before merging to main

**Save changes**

---

## 4. Feature Branch Guidelines

**Feature branches do NOT need protection rules**, but follow these conventions:

### Naming Convention:
- `feature/<short-description>` - New features
- `bugfix/<short-description>` - Bug fixes
- `hotfix/<short-description>` - Emergency production fixes
- `refactor/<short-description>` - Code refactoring
- `docs/<short-description>` - Documentation updates

### Lifecycle:
1. Create from `dev` branch
2. Develop and commit regularly
3. Keep up to date with `dev` (rebase or merge)
4. Create PR to `dev` when ready
5. Delete after merge to `dev`

### Best Practices:
- Keep features small and focused
- Commit messages follow conventional commits
- Regular pushes to backup work
- Run tests locally before PR
- Update tests with feature changes

---

## 5. Tag Protection

**Navigate to:** https://github.com/keundokki/LDAPGuard/settings/tag_protection_rules/new

### Configuration:

**Tag name pattern:** `v*`

#### Settings:
- This pattern will protect all version tags (v0.0.1, v1.0.0, etc.)
- Only repository admins can create or delete protected tags
- Protects against accidental tag deletion or modification

**Save changes**

---

## Configuration Checklist

Use this checklist when configuring branch protection:

### Initial Setup
- [ ] Configure main branch protection with maximum security
- [ ] Configure dev branch protection with moderate security
- [ ] Configure release-* branch protection
- [ ] Configure tag protection for v* pattern
- [ ] Test PR workflow: feature → dev
- [ ] Test PR workflow: dev → release → main
- [ ] Verify force push blocked on main
- [ ] Verify direct commits blocked on main

### When CI/CD is Added
- [ ] Update main protection: add required status checks
- [ ] Update dev protection: add required status checks
- [ ] Update release-* protection: add required status checks
- [ ] Configure deployment requirements

### Team Growth
- [ ] Create CODEOWNERS file
- [ ] Enable required reviews from code owners
- [ ] Add team-specific branch permissions
- [ ] Document team workflow in CONTRIBUTING.md

---

## Quick Reference

### Protection Levels Summary

| Branch | PRs Required | Approvals | Force Push | Delete | Admin Bypass |
|--------|--------------|-----------|------------|--------|--------------|
| main | ✅ | 1 | ❌ | ❌ | ❌ |
| dev | ✅ | 1 | ❌ | ❌ | ✅ |
| release-* | ✅ | 1 | ❌ | ❌ | ❌ |
| feature/* | ❌ | - | ✅ | ✅ | - |
| v* (tags) | - | - | ❌ | ❌ (admin only) | - |

---

## Troubleshooting

### "Cannot push to protected branch"
✅ **Expected behavior** - Create a pull request instead

### "Status checks required but not configured"
1. Remove status check requirement temporarily
2. Configure CI/CD pipeline
3. Re-enable status check requirement

### "Need to make emergency hotfix to main"
1. Create hotfix branch from main
2. Make fix and test thoroughly
3. Create PR with "urgent" label
4. Merge after review
5. Backport to dev: `git cherry-pick <commit>`

### "Accidentally pushed to wrong branch"
- Feature/bugfix branches: `git push --force` to fix
- Protected branches: Create new PR to revert commit

---

## Updates and Maintenance

**Last Updated:** February 5, 2026
**Reviewed By:** GitHub Copilot
**Next Review:** When team structure changes or CI/CD is implemented

