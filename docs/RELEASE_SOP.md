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

Edit `src/ftd_schema/schemas/file_formats/pipeline_format/manifest.yaml`:

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


## Example: Data Dictionary Release Using import_release

Use this flow when importing data dictionary artifacts from an upstream release.

### Step 1: Choose Source Artifact and Target Tag

Don't update more than one schema at the same time.

1. Identify schema coordinates (`--schema-type`, `--schema-name`, `--tag`)
2. Identify artifact source (`--zip-file` or `--zip-url`)
3. If using a GitHub release tag URL, set `--release-asset` (for example: `project-artifacts.zip`)
4. If importing a nested directory, set `--source-subdir` (for example: `project/data-dictionary`)


### Step 2: Run import_release

Example using release tag URL + asset name:

```bash
python src/import_release.py \
  --schema-type data_dictionaries \
  --schema-name fhir \
  --tag v2.9.4 \
  --zip-url https://github.com/carrollaboratory/kfi-fhir-input/releases/tag/v2.9.3 \
  --release-asset project-artifacts.zip \
  --source-subdir project/data-dictionary
```

Example using direct artifact URL:

```bash
python src/import_release.py \
  --schema-type data_dictionaries \
  --schema-name fhir \
  --tag v2.9.4 \
  --zip-url https://github.com/carrollaboratory/kfi-fhir-input/releases/download/v2.9.3/project-artifacts.zip \
  --source-subdir project/data-dictionary
```

Notes:

- `import_release.py` updates `manifest.yaml` for the target schema automatically.
- For `data_dictionaries`, `_<schema-name>_study.yaml` is generated automatically unless `--no-generate-study-yaml` is used.
- Use `--replace-existing` when intentionally re-importing the same tag directory.


### Step 3: Review Imported Output

Verify:

1. Files were written under `src/ftd_schema/schemas/data_dictionaries/<schema-name>/<tag>/`
2. `manifest.yaml` has the expected version entry and current pointers
3. `_<schema-name>_study.yaml` is present and references expected `*-dd.csv` files


### Step 4: Commit all changes to a branch, when ready ask for a PR review.


## PR Checklist

- [ ] Schema file(s) edited and tested
- [ ] Manifest updated with new version, breaking changes, notes
- [ ] `current_stable_tag` in manifest points to latest tested stable
- [ ] Beta entries are marked with `status: beta` until promoted
- [ ] For data_dictionaries, `_<schema-name>_study.yaml` generated and reviewed
- [ ] Tools consuming this schema notified (if applicable)

---

### Step 4: After review, merge the branch into main and create a Release and tag
