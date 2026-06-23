# ftd-schema

A centralized location for schema bundles used by FTD and related pipeline tools,
with explicit version directories and manifest metadata.

## Directory Structure

Each schema type contains multiple schema versions, with each version potentially containing multiple file types:

```
src/ftd_schema/schema/
├── common_data_model/          # Common Data Model schemas
│   ├── fhir/                   # Schema name (e.g., fhir, inc_access)
│   │   ├── v2.9.3/             # Version directory
│   │   │   ├── data_dictionary/    # CSV definitions
│   │   │   |  ├── _fhir_study.yaml   # Auto-generated study file
│   │   │   ├── enumerations/       # Enumeration files
│   │   └── manifest.yaml
│   └── ...
└── file_format/                # File Format schemas
    ├── pipeline_format/        # Schema name
    │   ├── v1.0.0/             # Version directory
    │   │   └── <files>
    │   └── manifest.yaml
    └── ...
```

## Import Release Artifacts

Use src/import_release.py to:

1. Import schema files from a release artifact zip.
2. Write files to src/ftd_schema/schema/<schema-type>/<schema-name>/<tag>/<target-subdir>/
3. Update manifest.yaml version entries.
4. Auto-generate _<schema-name>_study.yaml for data_dictionary subdirectories (default on).

Stable tags only are supported (examples: v1.0, v1.0.0, v2.9.4).

## Install For Tool Imports

From the repository root:

```bash
pip install -e .
```

Then import in downstream tools:

```python
from ftd_schema import resolve_schema_ref, resolve_schema_path

version_dir = resolve_schema_path("common_data_model", "fhir", "v2.9.3")
csv_path = resolve_schema_ref(
  path_or_url="https://github.com/org/repo/blob/main/src/ftd_schema/schema/common_data_model/fhir/v2.9.3/data_dictionary/AccessPolicy-dd.csv"
)
```

Resolve an entire schema directory with resolve_schema_ref:

```python
from ftd_schema import resolve_schema_ref

# Coordinate mode -> version directory
schema_dir = resolve_schema_ref(
  schema_type="common_data_model",
  schema_name="fhir",
  tag="v2.9.3",
)

# Local path mode -> version directory
schema_dir = resolve_schema_ref(
  path_or_url="src/ftd_schema/schema/common_data_model/fhir/v2.9.3"
)

# GitHub tree URL mode -> mapped to local clone directory
schema_dir = resolve_schema_ref(
  path_or_url="https://github.com/org/repo/tree/main/src/ftd_schema/schema/common_data_model/fhir/v2.9.3"
)

# Optional: iterate all files
all_files = [p for p in schema_dir.rglob("*") if p.is_file()]
```

All resolver helpers return a pathlib.Path.

For advanced use, the `SchemaResolver` class exposes additional helpers:

```python
from ftd_schema import SchemaResolver

resolver = SchemaResolver("common_data_model", "fhir")

# Load a Python schema module (file_format with schema.py only)
schema_module = resolver.load_schema(version="v1.0")

# List stable, non-deprecated versions
stable = resolver.get_stable_versions()

# Read raw manifest data
manifest = resolver.get_manifest()
```


```python
from ftd_schema import __version__
print(__version__)
```

## Quick Start


### Import from a direct release asset URL

```bash
python src/import_release.py \
  --schema-type common_data_model \
  --schema-name fhir \
  --tag v2.9.4 \
  --zip-url https://github.com/carrollaboratory/kfi-fhir-input/releases/download/v2.9.3/project-artifacts.zip \
  --source-subdir project/data-dictionary
```

### Import from a release tag page + asset name

```bash
python src/import_release.py \
  --schema-type common_data_model \
  --schema-name fhir \
  --tag v2.9.4 \
  --zip-url https://github.com/carrollaboratory/kfi-fhir-input/releases/tag/v2.9.3 \
  --release-asset project-artifacts.zip \
  --source-subdir project/data-dictionary
```

### Import GitHub source archive from a tag page

```bash
python src/import_release.py \
  --schema-type common_data_model \
  --schema-name inc_access \
  --tag v1.0.0 \
  --zip-url https://github.com/include-dcc/include-access-model/releases/tag/v1.0.0 \
  --release-asset "Source code"
```

### Import enumerations to a specific subdirectory

```bash
python src/import_release.py \
  --schema-type common_data_model \
  --schema-name fhir \
  --tag v2.9.3 \
  --zip-url https://github.com/carrollaboratory/kfi-fhir-input/releases/tag/v2.9.3 \
  --release-asset project-artifacts.zip \
  --source-subdir project/enumerations \
  --target-subdir enumerations \
  --replace-existing
```

## Common Arguments

- --schema-type: One of common_data_model, file_format.
- --schema-name: Bundle name under src/ftd_schema/schema/<schema-type>/.
- --tag: Destination version directory and manifest version (stable tags only).
- --zip-file: Local zip artifact path.
- --zip-url: Remote artifact URL.
- --release-asset: Optional filename when --zip-url is a GitHub releases/tag URL.
- --source-subdir: Optional path inside the zip to extract.
- --target-subdir: Optional subdirectory within the version where files are placed.
  - Examples: data_dictionary, enumerations, mapping, etc.
  - Defaults to "data_dictionary" for common_data_model, version root for file_format.
- --replace-existing: Overwrite an existing destination tag directory.
- --notes: Optional text appended to manifest version notes.
- --generate-study-yaml / --no-generate-study-yaml:
  - Defaults to enabled for common_data_model.
  - Generates _<schema-name>_study.yaml from imported *-dd.csv files.
