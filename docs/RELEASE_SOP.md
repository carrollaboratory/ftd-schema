# Release Playbook
Procedure for versioning, tagging, and publishing schema releases.

---

## Prerequisites 

- Ensure all schema changes are committed to git
- Decide which schemas have changed (they may have different new version numbers)
- Use stable tags only for imports (example: `v2.9.3`)

---

## Example: Data Model Release Pipeline Format v1.1.0

### Step 1: Update the Schema Files
Don't update more than one schema at the same time.

1. Create new version directory
2. Copy and edit schema (or start fresh)


### Step 2: Update the Manifest

Edit `src/schemas/file_formats/pipeline_format/manifest.yaml`:

```yaml
versions:
  - tag: "v1.0.0"
    directory: "v1.0.0"
    version: "v1.0.0"
    released: "2026-06-17"
    status: stable
    breaking_changes: []
    notes: |
      Initial release.
    deprecated: false

  - tag: "v1.1"              # Add new entry
    directory: "v1.1.0"
    version: "v1.1.0"
    released: "2026-06-20"   # Today's date
    status: stable
    breaking_changes: []     # Empty if backward-compatible
    notes: |
      - Added optional 'tags' field
      - Improved regex validation for enumerations
    deprecated: false

current_tag: "v1.2.0"
current_version: "v1.2.0"
current_stable_tag: "v1.1.0"      # Point to tested stable
current_stable_version: "v1.1.0"
```


### Step 3: Commit all changes to a branch, when ready ask for a PR review.


## Checklist

- [ ] Schema file(s) edited and tested
- [ ] Manifest updated with new version, breaking changes, notes
- [ ] `current_stable_tag` in manifest points to latest tested stable
- [ ] Beta entries are marked with `status: beta` until promoted
- [ ] Tools consuming this schema notified (if applicable)

---

### Step 4: After review, merge the branch into main and create a Release and tag
