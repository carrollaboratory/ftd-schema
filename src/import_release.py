"""Import schema files from a release zip and update manifest metadata. See
 README.md for usage instructions.

"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import re
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlparse, urlunparse

import yaml

STABLE_TAG_RE = re.compile(r"^v\d+(\.\d+)*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import release zip contents into an explicit version directory and update manifest.",
    )
    parser.add_argument("--schema-type", required=True, choices=["data_dictionaries", "file_formats"])
    parser.add_argument("--schema-name", required=True)
    parser.add_argument("--tag", required=True, help="Stable tag and destination directory (example: v2.9.2)")
    parser.add_argument(
        "--zip-file",
        help="Path to local zip artifact. Provide either --zip-file or --zip-url.",
    )
    parser.add_argument(
        "--zip-url",
        help="URL to zip artifact. Provide either --zip-file or --zip-url.",
    )
    parser.add_argument(
        "--release-asset",
        default="",
        help=(
            "Optional asset filename when --zip-url points to a GitHub releases/tag URL "
            "(example: project-artifacts.zip)."
        ),
    )
    parser.add_argument(
        "--source-subdir",
        default="",
        help=(
            "Optional subdirectory inside the zip to import from. "
            "If omitted, the zip root is used (or the only top-level directory if exactly one exists)."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root path (defaults to auto-detected project root).",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional note text appended to the manifest entry.",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace existing destination tag directory if it already exists.",
    )
    parser.add_argument(
        "--generate-study-yaml",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Generate _<schema-name>_study.yaml from imported *-dd.csv files. "
            "Defaults to enabled for --schema-type data_dictionaries."
        ),
    )

    args = parser.parse_args()

    if bool(args.zip_file) == bool(args.zip_url):
        parser.error("Provide exactly one of --zip-file or --zip-url.")

    return args


def ensure_stable_tag(tag: str) -> None:
    if not STABLE_TAG_RE.match(tag):
        raise ValueError(
            f"Invalid stable tag '{tag}'. Use stable tags only (example: v1.0.0). "
            "Prerelease tags such as beta/rc are not supported by this importer."
        )


def load_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Manifest is not a YAML mapping: {path}")
    data.setdefault("versions", [])
    if not isinstance(data["versions"], list):
        raise ValueError(f"Manifest 'versions' must be a list: {path}")
    return data


def normalize_zip_url(zip_url: str, release_asset: str = "") -> str:
    # Accept pasted markdown/snippets by extracting the first URL-like token.
    url_match = re.search(r"https?://\S+", zip_url)
    raw = (url_match.group(0) if url_match else zip_url).strip().strip("<>")
    raw = raw.rstrip(").,;\"'")
    if not raw:
        raise ValueError("--zip-url cannot be empty")

    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"--zip-url must be an absolute URL: {zip_url}")

    netloc = parsed.netloc.lower()

    # Accept GitHub release tag links and convert them to a direct source zip URL.
    # Example:
    #   https://github.com/org/repo/releases/tag/v1.2.3/Source code
    # becomes:
    #   https://github.com/org/repo/archive/refs/tags/v1.2.3.zip
    if netloc in {"github.com", "www.github.com"}:
        match = re.match(
            r"^/(?P<owner>[^/]+)/(?P<repo>[^/]+)/releases/tag/(?P<tag>[^/]+)(?:/.*)?$",
            parsed.path,
        )
        if match:
            owner = match.group("owner")
            repo = match.group("repo")
            tag = quote(match.group("tag"), safe="")
            if release_asset.strip():
                asset_name = release_asset.strip()
                asset_name_lower = asset_name.lower()

                # "Source code" on GitHub release pages is a synthetic link,
                # not a real upload under releases/download.
                if asset_name_lower in {"source code", "source code(zip)", "source code (zip)"}:
                    return urlunparse(
                        (parsed.scheme, "github.com", f"/{owner}/{repo}/archive/refs/tags/{tag}.zip", "", "", "")
                    )
                if asset_name_lower in {"source code(tar.gz)", "source code (tar.gz)"}:
                    return urlunparse(
                        (
                            parsed.scheme,
                            "github.com",
                            f"/{owner}/{repo}/archive/refs/tags/{tag}.tar.gz",
                            "",
                            "",
                            "",
                        )
                    )

                asset = quote(asset_name, safe="")
                return urlunparse(
                    (parsed.scheme, "github.com", f"/{owner}/{repo}/releases/download/{tag}/{asset}", "", "", "")
                )
            return urlunparse((parsed.scheme, "github.com", f"/{owner}/{repo}/archive/refs/tags/{tag}.zip", "", "", ""))

    safe_path = quote(parsed.path, safe="/%")
    return urlunparse((parsed.scheme, parsed.netloc, safe_path, parsed.params, parsed.query, parsed.fragment))


def fetch_zip_to_memory(zip_file: Optional[str], zip_url: Optional[str], release_asset: str = "") -> bytes:
    if zip_file:
        p = Path(zip_file)
        if not p.exists():
            raise FileNotFoundError(f"Zip file not found: {p}")
        return p.read_bytes()

    assert zip_url is not None
    normalized_url = normalize_zip_url(zip_url, release_asset)
    with urllib.request.urlopen(normalized_url) as response:
        return response.read()


def get_zip_root_candidates(zf: zipfile.ZipFile) -> List[str]:
    roots = set()
    for info in zf.infolist():
        # Skip empty names and macOS metadata folder.
        if not info.filename or info.filename.startswith("__MACOSX/"):
            continue
        root = info.filename.split("/", 1)[0]
        if root:
            roots.add(root)
    return sorted(roots)


def resolve_source_prefix(zf: zipfile.ZipFile, source_subdir: str) -> str:
    normalized = source_subdir.strip().strip("/")
    if normalized:
        roots = get_zip_root_candidates(zf)
        candidates = [normalized + "/"]

        # Common case: release artifacts have one wrapper folder at zip root.
        if len(roots) == 1 and not normalized.startswith(roots[0] + "/"):
            candidates.append(f"{roots[0]}/{normalized}/")

        for prefix in candidates:
            if any(i.filename.startswith(prefix) for i in zf.infolist()):
                return prefix

        roots_hint = ", ".join(roots[:5]) if roots else "(empty zip)"
        raise ValueError(
            f"source-subdir '{source_subdir}' not found in zip. "
            f"Top-level entries include: {roots_hint}"
        )

    roots = get_zip_root_candidates(zf)
    # If there is one root folder, treat that as the source prefix.
    if len(roots) == 1:
        return roots[0] + "/"

    # Multiple roots: use zip root.
    return ""


def extract_selected_tree(zip_bytes: bytes, source_prefix: str, destination: Path) -> int:
    extracted_files = 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for info in zf.infolist():
            name = info.filename
            if not name or name.endswith("/"):
                continue
            if name.startswith("__MACOSX/"):
                continue
            if source_prefix and not name.startswith(source_prefix):
                continue

            relative = name[len(source_prefix) :] if source_prefix else name
            relative = relative.lstrip("/")
            if not relative:
                continue

            out_path = destination / relative
            out_path.parent.mkdir(parents=True, exist_ok=True)

            with zf.open(info) as src, out_path.open("wb") as dst:
                shutil.copyfileobj(src, dst)

            extracted_files += 1

    return extracted_files


def generate_study_yaml(destination: Path, schema_name: str) -> Path:
    dd_files = sorted(
        p.name for p in destination.iterdir() if p.is_file() and p.name.endswith("-dd.csv")
    )
    if not dd_files:
        raise ValueError(
            f"No *-dd.csv files found in {destination}; cannot generate _{schema_name}_study.yaml"
        )

    data_dictionary: Dict[str, Dict[str, str]] = {}
    for filename in dd_files:
        class_name = filename[: -len("-dd.csv")]
        data_dictionary[class_name] = {"identifier": filename}

    study_doc: Dict[str, Any] = {
        "model_name": schema_name,
        "model_prefix": schema_name,
        "format": "ftd_dd",
        "data_dictionary": data_dictionary,
    }

    output_path = destination / f"_{schema_name}_study.yaml"
    with output_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(study_doc, f, sort_keys=False, default_flow_style=False)

    return output_path


def upsert_version_entry(manifest: Dict[str, Any], tag: str, notes: str) -> None:
    today = dt.date.today().isoformat()
    entries = manifest.get("versions", [])

    existing = None
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if tag in {entry.get("tag"), entry.get("directory"), entry.get("version")}:
            existing = entry
            break

    base_notes = f"Imported from release artifact for {tag}."
    full_notes = base_notes if not notes else f"{base_notes}\n{notes.strip()}"

    if existing is None:
        entries.append(
            {
                "tag": tag,
                "directory": tag,
                "version": tag,
                "released": today,
                "status": "stable",
                "breaking_changes": [],
                "notes": full_notes,
                "deprecated": False,
            }
        )
    else:
        existing["directory"] = tag
        existing["tag"] = tag
        existing["version"] = tag
        existing["released"] = existing.get("released", today)
        existing["status"] = "stable"
        existing["deprecated"] = False
        if notes:
            existing["notes"] = full_notes
        elif "notes" not in existing:
            existing["notes"] = base_notes
        if "breaking_changes" not in existing or not isinstance(existing["breaking_changes"], list):
            existing["breaking_changes"] = []

    manifest["versions"] = entries
    manifest["current_tag"] = tag
    manifest["current_version"] = tag
    manifest["current_stable_tag"] = tag
    manifest["current_stable_version"] = tag


def write_manifest(path: Path, manifest: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, sort_keys=False, default_flow_style=False)


def main() -> int:
    args = parse_args()

    try:
        ensure_stable_tag(args.tag)

        repo_root = Path(args.repo_root).resolve()
        schema_dir = repo_root / "src" / "ftd_schema" / "schemas" / args.schema_type / args.schema_name
        manifest_path = schema_dir / "manifest.yaml"

        if not schema_dir.exists():
            raise FileNotFoundError(f"Schema directory not found: {schema_dir}")

        manifest = load_manifest(manifest_path)

        destination = schema_dir / args.tag
        if destination.exists():
            if not args.replace_existing:
                raise FileExistsError(
                    f"Destination already exists: {destination}. "
                    "Use --replace-existing to overwrite."
                )
            shutil.rmtree(destination)

        destination.mkdir(parents=True, exist_ok=False)

        zip_bytes = fetch_zip_to_memory(args.zip_file, args.zip_url, args.release_asset)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            source_prefix = resolve_source_prefix(zf, args.source_subdir)

        extracted_files = extract_selected_tree(zip_bytes, source_prefix, destination)
        if extracted_files == 0:
            shutil.rmtree(destination, ignore_errors=True)
            raise ValueError("No files extracted from zip. Check --source-subdir and artifact contents.")

        should_generate_study = (
            args.generate_study_yaml
            if args.generate_study_yaml is not None
            else args.schema_type == "data_dictionaries"
        )
        generated_study_path: Optional[Path] = None
        if should_generate_study:
            generated_study_path = generate_study_yaml(destination, args.schema_name)

        upsert_version_entry(manifest, args.tag, args.notes)
        write_manifest(manifest_path, manifest)

        print(f"Imported {extracted_files} files to {destination}")
        if generated_study_path is not None:
            print(f"Generated study YAML: {generated_study_path}")
        print(f"Updated manifest: {manifest_path}")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
