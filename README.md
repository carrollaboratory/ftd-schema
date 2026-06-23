# ftd-schema

A centralized location for schema bundles used by FTD and related pipeline tools,
with explicit version directories and manifest metadata.

## Directory Structure

Each schema type contains multiple schema versions, with each version potentially containing multiple file types:

```
src/ftd_schema/schema/
├── common_data_model/          # Common Data Model schemas
│   ├── fhir/                   # Schema name (e.g., fhir, inc_access)
│   │   ├── v0.9.3/             # Version directory
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
3. Extract only the selected files/subdirectory into this repository.
4. For `common_data_model` imports into `data_dictionary`, generate `_<schema-name>_study.yaml`.

When using `--zip-url`, provide a direct downloadable `.zip` URL. The importer does not transform
release page URLs or GitHub tag URLs.

Required format example:

```text
https://github.com/carrollaboratory/kfi-fhir-input/releases/download/v0.9.3/project-artifacts.zip
```

Any tag string can be used (examples: v1.0, v1.0.0, v0.9.4, v0.9.4-rc1).

## Install For Tool Imports

From the repository root:

```bash
pip install -e .
```

Then import in downstream tools:

```python
from ftd_schema import SchemaResolver

resolver = SchemaResolver("common_data_model", "fhir")
version_dir = resolver.get_version_path("v0.9.3")

format_resolver = SchemaResolver("file_format", "pipeline_format")
schema_module = format_resolver.load_schema("v1.0.0")
```

Resolve an entire schema directory with the resolver:

```python
from ftd_schema import SchemaResolver

resolver = SchemaResolver("common_data_model", "fhir")
schema_dir = resolver.get_version_path("v0.9.3")

# Optional: iterate all files
all_files = [p for p in schema_dir.rglob("*") if p.is_file()]
```

Resolver path helpers return a pathlib.Path.

If you omit the version when calling `get_version_path()` or `load_schema()`, the
resolver uses the first version returned by `get_versions()`.

You can also pass `repo_root` to `SchemaResolver(...)` when resolving schemas from
an explicit checkout instead of the installed package.

For advanced use, the `SchemaResolver` class exposes additional helpers:

```python
from ftd_schema import SchemaResolver

resolver = SchemaResolver("common_data_model", "fhir")

# Load a Python schema module (file_format with schema.py only)
schema_module = resolver.load_schema(version="v1.0.0")

# List available versions
versions = resolver.get_versions()

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
  --tag v0.9.4 \
  --zip-url https://github.com/carrollaboratory/kfi-fhir-input/releases/download/v0.9.3/project-artifacts.zip \
  --source-subdir project/data-dictionary
```

### Import enumerations to a specific subdirectory

```bash
python src/import_release.py \
  --schema-type common_data_model \
  --schema-name fhir \
  --tag v0.9.3 \
  --zip-url https://github.com/carrollaboratory/kfi-fhir-input/releases/download/v0.9.3/project-artifacts.zip \
  --source-subdir project/enumerations \
  --target-subdir enumerations \
  --replace-existing
```

## Common Arguments

- --schema-type: One of common_data_model, file_format.
- --schema-name: Bundle name under src/ftd_schema/schema/<schema-type>/.
- --tag: Destination version directory.
- --zip-file: Local zip artifact path.
- --zip-url: Direct downloadable `.zip` artifact URL.
- --source-subdir: Optional path inside the zip to extract.
- --target-subdir: Optional subdirectory within the version where files are placed.
  - Examples: data_dictionary, enumerations, mapping, etc.
  - Defaults to "data_dictionary" for common_data_model, version root for file_format.
  - When this resolves to `data_dictionary` for `common_data_model`, `_<schema-name>_study.yaml` is generated.
- --repo-root: Optional repository root override.
- --replace-existing: Overwrite an existing destination tag directory.
