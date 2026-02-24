# Releasing LDAPGuard

This project uses a 3-branch release model:

- `develop`: integration branch, publishes `-dev` images
- `release/x.y.z`: release hardening branch, publishes candidate images
- `main`: production branch, publishes final version + `latest`

## 1) Day-to-day development

1. Create feature branch from `develop`.
2. Open PR into `develop`.
3. Merge when CI is green.

### Commands

```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-change
# ... commit work ...
git push -u origin feature/my-change
```

Open PR: `feature/my-change` -> `develop`.

## 2) Start a release

When `develop` is ready, create a release branch:

```bash
git checkout develop
git pull origin develop
git checkout -b release/1.1.0
git push -u origin release/1.1.0
```

On `release/*`:
- only stabilization fixes
- no new features

Open PRs into `release/1.1.0` for bug fixes.

## 3) Validate release candidate

CI on `release/*` builds and pushes candidate images (no `latest`).
Use those images for staging/UAT.

## 4) Promote to production

Open PR: `release/1.1.0` -> `main`.

On merge to `main`, compiler workflow will:
- build/test images
- push final tag `1.1.0`
- update `latest`
- create git tag `ldapguard-v1.1.0`

## 5) Sync back after release

After release is merged, sync production back into `develop`:

```bash
git checkout develop
git pull origin develop
git merge origin/main
git push origin develop
```

## 6) Start next cycle

Create new feature branches from updated `develop` and continue.

---

## Notes

- Do not push directly to `main`.
- Prefer PR merges for all branch transitions.
- Keep `VERSION` aligned with the branch purpose:
  - `develop`: `x.y.z-dev`
  - `release/*`: `x.y.z` or `x.y.z-rc` (team choice)
  - `main`: `x.y.z`
