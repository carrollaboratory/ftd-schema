"""
Schema resolver utility for ftd-schema consumer tools. See README.md for 
usage examples.

"""

import importlib.resources
import importlib.util
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

import yaml


def _ftd_schema_dir() -> Path:
    """Return the installed ftd_schema package directory (contains schemas/)."""
    try:
        ref = importlib.resources.files("ftd_schema")
        return Path(str(ref))
    except Exception:
        # Fallback: resolve relative to this file's known position in src/
        return Path(__file__).resolve().parent / "ftd_schema"


class SchemaResolver:
    """Resolve and load versioned schemas from ftd-schema repository."""

    def __init__(self, schema_type: str, schema_name: str, repo_root: Optional[Path] = None):
        """
        Initialize a schema resolver.

        Args:
            schema_type: Either "data_dictionaries" or "file_formats"
            schema_name: Name of the schema (e.g., "access", "pipeline_format")
            repo_root: Root path of ftd-schema repo. If None, assumes relative import.
        """
        self.schema_type = schema_type
        self.schema_name = schema_name

        if repo_root is None:
            pkg_dir = _ftd_schema_dir()
        else:
            pkg_dir = Path(repo_root) / "src" / "ftd_schema"

        self.schema_dir = pkg_dir / "schemas" / schema_type / schema_name
        
        if not self.schema_dir.exists():
            raise ValueError(f"Schema not found: {self.schema_dir}")

    def _is_explicit_version_dir(self, name: str) -> bool:
        """Return True for explicit version directories (v<digit>...)."""
        return len(name) > 1 and name.startswith("v") and name[1].isdigit()

    def get_manifest(self) -> Dict[str, Any]:
        """Load and return the schema manifest (YAML)."""
        manifest_path = self.schema_dir / "manifest.yaml"
        with open(manifest_path) as f:
            return yaml.safe_load(f)

    def get_current_version(self) -> str:
        """Get the current/latest recommended version tag or directory name."""
        manifest = self.get_manifest()
        if "current_stable_tag" in manifest:
            return manifest["current_stable_tag"]
        if "current_stable_version" in manifest:
            return manifest["current_stable_version"]
        if "current_version" in manifest:
            return manifest["current_version"]
        if "current_tag" in manifest:
            return manifest["current_tag"]

        # Fallback when manifest omits a current pointer.
        versions = self.get_versions()
        if not versions:
            raise ValueError(f"No versions found for schema: {self.schema_dir}")
        return versions[0]

    def _matches_version_identifier(self, item: Dict[str, Any], version: str) -> bool:
        """Return True when a manifest entry matches a provided version string."""
        return version in {
            item.get("directory"),
            item.get("tag"),
            item.get("version"),
        }

    def get_versions(self, include_beta: bool = True, include_deprecated: bool = True) -> List[str]:
        """Get list of available version identifiers from manifest and disk.

        Args:
            include_beta: Include versions marked as status=beta.
            include_deprecated: Include versions marked deprecated=true.
        """
        manifest = self.get_manifest()
        manifest_versions = []
        for item in manifest.get("versions", []):
            status = item.get("status", "stable")
            if not include_beta and status == "beta":
                continue
            if not include_deprecated and item.get("deprecated", False):
                continue

            if "directory" in item:
                manifest_versions.append(item["directory"])
            elif "tag" in item:
                manifest_versions.append(item["tag"])
            elif "version" in item:
                manifest_versions.append(item["version"])

        fs_versions = [
            p.name for p in self.schema_dir.iterdir()
            if p.is_dir() and self._is_explicit_version_dir(p.name)
        ]

        # Preserve manifest order first, then append any on-disk versions not listed.
        ordered = []
        for v in manifest_versions + fs_versions:
            if v not in ordered:
                ordered.append(v)
        return ordered

    def get_stable_versions(self) -> List[str]:
        """Get versions suitable for production use (stable and not deprecated)."""
        return self.get_versions(include_beta=False, include_deprecated=False)

    def _resolve_version_dir(self, version: Optional[str] = None) -> Path:
        """Resolve a version identifier to an explicit on-disk directory."""
        if version is None:
            version = self.get_current_version()

        # 1) Direct explicit directory, e.g. v2.9.2
        direct_dir = self.schema_dir / version
        if direct_dir.is_dir():
            return direct_dir

        # 2) Accept SemVer without v-prefix if directory is v{version}
        prefixed_dir = self.schema_dir / f"v{version}"
        if prefixed_dir.is_dir():
            return prefixed_dir

        # 3) Backward compatibility with older layout: versions/{version}/
        legacy_dir = self.schema_dir / "versions" / version
        if legacy_dir.is_dir():
            return legacy_dir

        # 4) Manifest mapping: tag/version -> explicit directory
        manifest = self.get_manifest()
        for item in manifest.get("versions", []):
            item_dir = item.get("directory")
            if self._matches_version_identifier(item, version) and item_dir:
                candidate = self.schema_dir / item_dir
                if candidate.is_dir():
                    return candidate

        raise ValueError(f"Schema version not found: {version}")

    def get_version_path(self, version: Optional[str] = None) -> Path:
        """Return the filesystem path to a specific explicit version directory."""
        return self._resolve_version_dir(version)

    def load_schema(self, version: Optional[str] = None) -> Any:
        """
        Load a Python schema module for the given version.

        Args:
            version: Specific version to load. If None, uses current version.

        Returns:
            The schema module (containing schema object, etc.).

        Raises:
            ValueError: If version not found, schema.py missing, or load fails.
        """
        version_dir = self._resolve_version_dir(version)
        schema_path = version_dir / "schema.py"

        if not schema_path.exists():
            raise ValueError(
                "No Python schema module found at "
                f"{schema_path}. Use get_version_path() for non-Python bundles."
            )

        spec = importlib.util.spec_from_file_location("schema", schema_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Cannot load schema module from {schema_path}")

        schema_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schema_module)
        
        return schema_module

    def load_current(self) -> Any:
        """Load the current/latest schema version."""
        return self.load_schema(version=None)

    def is_deprecated(self, version: str) -> bool:
        """Check if a version is marked as deprecated."""
        info = self.get_version_info(version)
        if info is None:
            return False
        return info.get("deprecated", False)

    def is_beta(self, version: str) -> bool:
        """Check if a version is marked as beta."""
        info = self.get_version_info(version)
        if info is None:
            return False
        return info.get("status", "stable") == "beta"

    def get_version_info(self, version: str) -> Optional[Dict[str, Any]]:
        """Get detailed info for a specific version from manifest."""
        manifest = self.get_manifest()
        for v in manifest.get("versions", []):
            if self._matches_version_identifier(v, version):
                return v
        return None


def _default_repo_root(repo_root: Optional[Path] = None) -> Path:
    """Resolve the ftd_schema package directory (contains schemas/)."""
    if repo_root is None:
        return _ftd_schema_dir()
    return Path(repo_root).resolve() / "src" / "ftd_schema"


def resolve_schema_path(
    schema_type: str,
    schema_name: str,
    tag: Optional[str] = None,
    repo_root: Optional[Path] = None,
) -> Path:
    """Resolve a version directory by schema coordinates.

    Returns a pathlib.Path to the local schema version directory.
    Works for both editable and regular pip installs.
    """
    resolver = SchemaResolver(schema_type=schema_type, schema_name=schema_name, repo_root=repo_root)
    return resolver.get_version_path(version=tag)


def resolve_local_or_github_path(
    path_or_url: str,
    repo_root: Optional[Path] = None,
) -> Path:
    """Resolve a local path or GitHub blob/tree URL to a local path in this clone.

    For GitHub URLs, this maps paths after /blob/<ref>/ or /tree/<ref>/ into
    the current cloned repository. Network access is not required.
    """
    root = _default_repo_root(repo_root)

    raw = path_or_url.strip()
    if not raw:
        raise ValueError("path_or_url cannot be empty")

    if raw.startswith(("http://", "https://")):
        parsed = urlparse(raw)
        if parsed.netloc not in {"github.com", "www.github.com"}:
            raise ValueError(f"Unsupported URL host: {parsed.netloc}")

        parts = [p for p in parsed.path.split("/") if p]
        # Expected: /<owner>/<repo>/blob/<ref>/<path...>
        # or       /<owner>/<repo>/tree/<ref>/<path...>
        if len(parts) < 5 or parts[2] not in {"blob", "tree"}:
            raise ValueError(
                "GitHub URL must match /<owner>/<repo>/(blob|tree)/<ref>/<path>"
            )

        rel_path = Path(*parts[4:])
        candidate = (root.parent.parent / rel_path).resolve()
    else:
        p = Path(raw)
        if p.is_absolute():
            candidate = p.resolve()
        else:
            # Try relative to package dir (schemas/...), then repo root (src/ftd_schema/...)
            for base in (root, root.parent.parent):
                candidate = (base / p).resolve()
                if candidate.exists():
                    break

    # Security check: must resolve inside package or repo tree
    repo_root_resolved = root.parent.parent
    inside_pkg = candidate.is_relative_to(root)
    inside_repo = candidate.is_relative_to(repo_root_resolved)
    if not (inside_pkg or inside_repo):
        raise ValueError(f"Resolved path escapes repository: {candidate}")

    if not candidate.exists():
        raise FileNotFoundError(f"Path not found: {candidate}")

    return candidate


def resolve_schema_ref(
    schema_type: Optional[str] = None,
    schema_name: Optional[str] = None,
    tag: Optional[str] = None,
    path_or_url: Optional[str] = None,
    repo_root: Optional[Path] = None,
) -> Path:
    """Resolve a schema reference from either coordinates or path/URL.

    Exactly one mode is allowed:
    - Coordinate mode: schema_type + schema_name (+ optional tag)
    - Path mode: path_or_url
    """
    has_coords = bool(schema_type or schema_name or tag)
    has_path = bool(path_or_url)

    if has_coords == has_path:
        raise ValueError(
            "Provide either coordinate fields (schema_type/schema_name/tag) "
            "or path_or_url, but not both"
        )

    if has_path:
        return resolve_local_or_github_path(path_or_url=path_or_url or "", repo_root=repo_root)

    if not schema_type or not schema_name:
        raise ValueError("schema_type and schema_name are required in coordinate mode")

    return resolve_schema_path(
        schema_type=schema_type,
        schema_name=schema_name,
        tag=tag,
        repo_root=repo_root,
    )


# Example usage
if __name__ == "__main__":
    # Load pipeline format schema
    resolver = SchemaResolver("file_formats", "pipeline_format")
    
    # Get current version
    current_version = resolver.get_current_version()
    print(f"Current version: {current_version}")
    
    # Load current schema module
    schema_module = resolver.load_current()
    print(f"Schema loaded: {schema_module}")

    # Resolve current version directory path
    current_path = resolver.get_version_path()
    print(f"Current path: {current_path}")
    
    # Get manifest info
    manifest = resolver.get_manifest()
    print(f"Manifest: {manifest['schema_name']}")
    
    # List all versions
    versions = resolver.get_versions()
    print(f"Available versions: {versions}")

    # List stable, non-deprecated versions
    stable_versions = resolver.get_stable_versions()
    print(f"Stable versions: {stable_versions}")
    
    # Check deprecation status
    is_deprecated = resolver.is_deprecated(current_version)
    print(f"Current version deprecated: {is_deprecated}")

    # Check beta status
    is_beta = resolver.is_beta(current_version)
    print(f"Current version beta: {is_beta}")
