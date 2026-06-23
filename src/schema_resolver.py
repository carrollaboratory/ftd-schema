"""Resolve schema directories and Python schema modules from this package."""

from __future__ import annotations

import importlib.resources
import importlib.util
from pathlib import Path
from typing import Any, Optional

import yaml


def _package_dir() -> Path:
    """Return the installed ftd_schema package directory."""

    try:
        return Path(str(importlib.resources.files("ftd_schema")))
    except Exception:
        return Path(__file__).resolve().parent / "ftd_schema"


def _schema_root(repo_root: Optional[Path] = None) -> Path:
    """Return the schema root for an installed package or repo checkout."""

    if repo_root is None:
        return _package_dir() / "schema"
    return Path(repo_root).resolve() / "src" / "ftd_schema" / "schema"


def _read_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load one schema manifest file."""

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with manifest_path.open(encoding="utf-8") as handle:
        manifest = yaml.safe_load(handle) or {}

    if not isinstance(manifest, dict):
        raise ValueError(f"Manifest is not a mapping: {manifest_path}")

    return manifest


class SchemaResolver:
    """Resolve schema paths and load Python schema modules."""

    def __init__(
        self, schema_type: str, schema_name: str, repo_root: Optional[Path] = None
    ):
        """Initialize a resolver for one schema bundle."""

        self.schema_type = schema_type
        self.schema_name = schema_name
        self.schema_dir = _schema_root(repo_root) / schema_type / schema_name
        self.manifest_path = self.schema_dir / "manifest.yaml"

        if not self.schema_dir.exists():
            raise FileNotFoundError(f"Schema not found: {self.schema_dir}")

    def get_manifest(self) -> dict[str, Any]:
        """Load the schema manifest."""

        return _read_manifest(self.manifest_path)

    def get_versions(self) -> list[str]:
        """Return version directory names in lookup order."""

        versions: list[str] = []
        manifest = self.get_manifest()

        for item in manifest.get("versions", []):
            if not isinstance(item, dict):
                continue

            for key in ("directory", "tag", "version"):
                value = item.get(key)
                if isinstance(value, str) and value not in versions:
                    versions.append(value)

        for child in sorted(self.schema_dir.iterdir()):
            if child.is_dir() and child.name not in versions:
                versions.append(child.name)

        return versions

    def get_default_version(self) -> str:
        """Return the default version identifier for this schema."""

        versions = self.get_versions()
        if not versions:
            raise ValueError(f"No versions found for schema: {self.schema_dir}")

        return versions[0]

    def get_version_path(self, version: Optional[str] = None) -> Path:
        """Return the directory for one schema version."""

        selected_version = version or self.get_default_version()
        direct_path = self.schema_dir / selected_version
        if direct_path.is_dir():
            return direct_path

        manifest = self.get_manifest()
        for item in manifest.get("versions", []):
            if not isinstance(item, dict):
                continue

            identifiers = {item.get("directory"), item.get("tag"), item.get("version")}
            if selected_version not in identifiers:
                continue

            directory = item.get("directory") or item.get("tag") or item.get("version")
            if not isinstance(directory, str):
                continue

            candidate = self.schema_dir / directory
            if candidate.is_dir():
                return candidate

        raise FileNotFoundError(
            f"Version '{selected_version}' not found for schema: {self.schema_dir}"
        )

    def load_schema(self, version: Optional[str] = None) -> Any:
        """Load the schema.py module for one version."""

        schema_path = self.get_version_path(version) / "schema.py"
        if not schema_path.exists():
            raise FileNotFoundError(f"schema.py not found: {schema_path}")

        module_name = (
            f"ftd_schema_dynamic_{self.schema_type}_{self.schema_name}_"
            f"{schema_path.parent.name.replace('.', '_').replace('-', '_')}"
        )
        spec = importlib.util.spec_from_file_location(module_name, schema_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Cannot load schema module from {schema_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
