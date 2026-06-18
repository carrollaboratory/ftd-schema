# ftd-schema

A centralized location for schema bundles used by FTD and related pipeline tools,
with explicit version directories and manifest metadata.

## Import Release Artifacts

Use src/import_release.py to:

1. Import schema files from a release artifact zip.
2. Write files to src/schemas/<schema-type>/<schema-name>/<tag>.
3. Update manifest.yaml current and version entries.
4. Auto-generate _<schema-name>_study.yaml for data_dictionaries (default on).

Stable tags only are supported (examples: v1.0, v1.0.0, v2.9.4).

## Install For Tool Imports

From the repository root:

```bash
pip install -e .
```

Then import in downstream tools:

```python
from ftd_schema import resolve_schema_ref, resolve_schema_path

version_dir = resolve_schema_path("data_dictionaries", "fhir", "v2.9.3")
csv_path = resolve_schema_ref(
  path_or_url="https://github.com/org/repo/blob/main/src/ftd_schema/schemas/data_dictionaries/fhir/v2.9.3/AccessPolicy-dd.csv"
)
```

Resolve an entire schema directory with resolve_schema_ref:

```python
from ftd_schema import resolve_schema_ref

# Coordinate mode -> version directory
schema_dir = resolve_schema_ref(
  schema_type="data_dictionaries",
  schema_name="fhir",
  tag="v2.9.3",
)

# Local path mode -> directory
schema_dir = resolve_schema_ref(
  path_or_url="src/ftd_schema/schemas/data_dictionaries/fhir/v2.9.3"
)

# GitHub tree URL mode -> mapped to local clone directory
schema_dir = resolve_schema_ref(
  path_or_url="https://github.com/org/repo/tree/main/src/ftd_schema/schemas/data_dictionaries/fhir/v2.9.3"
)

# Optional: iterate all files
all_files = [p for p in schema_dir.rglob("*") if p.is_file()]
```

All resolver helpers return a pathlib.Path.

For advanced use, the `SchemaResolver` class exposes additional helpers:

```python
from ftd_schema import SchemaResolver

resolver = SchemaResolver("data_dictionaries", "fhir")

# Load a Python schema module (file_formats with schema.py only)
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
  --schema-type data_dictionaries \
  --schema-name fhir \
  --tag v2.9.4 \
  --zip-url https://github.com/carrollaboratory/kfi-fhir-input/releases/download/v2.9.3/project-artifacts.zip \
  --source-subdir project/data-dictionary
```

### Import from a release tag page + asset name

```bash
python src/import_release.py \
  --schema-type data_dictionaries \
  --schema-name fhir \
  --tag v2.9.4 \
  --zip-url https://github.com/carrollaboratory/kfi-fhir-input/releases/tag/v2.9.3 \
  --release-asset project-artifacts.zip \
  --source-subdir project/data-dictionary
```

### Import GitHub source archive from a tag page

```bash
python src/import_release.py \
  --schema-type data_dictionaries \
  --schema-name inc_access \
  --tag v1.0.0 \
  --zip-url https://github.com/include-dcc/include-access-model/releases/tag/v1.0.0 \
  --release-asset "Source code"
```

Note: "Source code" archives are repository snapshots. They may not include
generated directories like project/data-dictionary.

## Common Arguments

- --schema-type: One of data_dictionaries, file_formats.
- --schema-name: Bundle name under src/ftd_schema/schemas/<schema-type>/.
- --tag: Destination version directory and manifest version (stable tags only).
- --zip-file: Local zip artifact path.
- --zip-url: Remote artifact URL.
- --release-asset: Optional filename when --zip-url is a GitHub releases/tag URL.
- --source-subdir: Optional path inside the zip to extract.
- --replace-existing: Overwrite an existing destination tag directory.
- --notes: Optional text appended to manifest version notes.
- --generate-study-yaml / --no-generate-study-yaml:
  - Defaults to enabled for data_dictionaries.
  - Generates _<schema-name>_study.yaml from imported *-dd.csv files.
