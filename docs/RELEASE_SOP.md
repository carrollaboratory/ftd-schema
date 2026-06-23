# Release Playbook
Procedure for versioning, tagging, and publishing schema releases.

---

## Prerequisites 

- Ensure all schema changes are committed to git
- Decide which schemas have changed (they may have different new version numbers)
- Choose a version tag format appropriate for the release process (example: `v0.9.3`)

---

## Example: Data Model Release Pipeline Format v1.1.0

### Step 1: Update the Schema Files
Don't update more than one schema at the same time.

1. Create new version directory
2. Copy and edit schema (or start fresh)


### Step 2: Update the Manifest

Edit `src/ftd_schema/schema/file_format/pipeline_format/manifest.yaml`:

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


### Step 3: Commit all changes to a branch, when ready ask for a PR review.


## Example: Data Dictionary Release Using import_release

Use this flow when importing data dictionary artifacts from an upstream release.

### Step 1: Choose Source Artifact and Target Tag

Don't update more than one schema at the same time.

1. Identify schema coordinates (`--schema-type`, `--schema-name`, `--tag`)
2. Identify artifact source (`--zip-file` or `--zip-url`)
3. If using `--zip-url`, provide a direct downloadable `.zip` artifact URL
4. If importing a nested directory, set `--source-subdir` (for example: `project/data-dictionary`)


### Step 2: Run import_release

Example: Import data dictionaries (default target-subdir):

```bash
python src/import_release.py \
  --schema-type common_data_model \
  --schema-name fhir \
  --tag v2.9.4 \
  --zip-url https://github.com/carrollaboratory/kfi-fhir-input/releases/download/v2.9.3/project-artifacts.zip \
  --source-subdir project/data-dictionary
```

Example: Import enumerations to specific subdirectory:

```bash
python src/import_release.py \
  --schema-type common_data_model \
  --schema-name fhir \
  --tag v2.9.3 \
  --zip-url https://github.com/carrollaboratory/kfi-fhir-input/releases/download/v2.9.3/project-artifacts.zip \
  --source-subdir project/enumerations \
  --target-subdir enumerations \
  --replace-existing
```

Example using direct artifact URL:

```bash
python src/import_release.py \
  --schema-type common_data_model \
  --schema-name fhir \
  --tag v2.9.4 \
  --zip-url https://github.com/carrollaboratory/kfi-fhir-input/releases/download/v2.9.3/project-artifacts.zip \
  --source-subdir project/data-dictionary
```

Notes:

- `--target-subdir` defaults to `data_dictionary` for common_data_model imports (override as needed).
- Use `--replace-existing` when intentionally re-importing the same tag directory.


### Step 3: Review Imported Output

Verify:

1. Files were written under `src/ftd_schema/schema/common_data_model/<schema-name>/<tag>/<target-subdir>/`
   (or `src/ftd_schema/schema/common_data_model/<schema-name>/<tag>/` if no subdirectory specified)
2. Imported files match the expected contents from the source zip


### Step 4: Commit all changes to a branch, when ready ask for a PR review.


## PR Checklist

- [ ] Schema file(s) edited and tested
- [ ] Manifest updated with new version, breaking changes, notes
- [ ] Version marked with `status: stable` or `status: beta` as appropriate
- [ ] Deprecated entries marked with `deprecated: true` if applicable
- [ ] Tools consuming this schema notified (if applicable)

---

### Step 4: After review, merge the branch into main and create a Release and tag
