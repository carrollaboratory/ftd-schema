"""Import selected files from a zip into schema directories in this repository."""

from __future__ import annotations

import argparse
import io
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import List, Optional

import yaml

def parse_args() -> argparse.Namespace:
    """Parse and validate command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Import selected files from a zip into a schema directory in this repository.",
    )
    parser.add_argument(
        "--schema-type", required=True, choices=["common_data_model", "file_format"]
    )
    parser.add_argument("--schema-name", required=True)
    parser.add_argument(
        "--tag",
        required=True,
        help="Version tag and destination directory (example: v2.9.2)",
    )
    parser.add_argument(
        "--zip-file",
        help="Path to local zip artifact. Provide either --zip-file or --zip-url.",
    )
    parser.add_argument(
        "--zip-url",
        help=(
            "Direct URL to a downloadable .zip artifact. "
            "Provide either --zip-file or --zip-url."
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
        "--target-subdir",
        default=None,
        help=(
            "Optional subdirectory where files should be placed within the version directory. "
            "Examples: data_dictionary, enumerations, mapping. "
            "Defaults to 'data_dictionary' for common_data_model, version root for file_format."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root path (defaults to auto-detected project root).",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace existing destination tag directory if it already exists.",
    )

    args = parser.parse_args()

    if bool(args.zip_file) == bool(args.zip_url):
        parser.error("Provide exactly one of --zip-file or --zip-url.")

    return args


def fetch_zip_to_memory(zip_file: Optional[str], zip_url: Optional[str]) -> bytes:
    """Load zip bytes from a local file or direct URL."""
    if zip_file:
        p = Path(zip_file)
        if not p.exists():
            raise FileNotFoundError(f"Zip file not found: {p}")
        return p.read_bytes()

    assert zip_url is not None
    with urllib.request.urlopen(zip_url) as response:
        return response.read()


def get_zip_root_candidates(zf: zipfile.ZipFile) -> List[str]:
    """Return sorted top-level entries found in the zip archive."""

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
    """Resolve the zip prefix to extract from based on the requested subdirectory."""

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
    """Extract matching files from the zip into the destination directory."""

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
    """Generate _<schema-name>_study.yaml from imported *-dd.csv files."""

    dd_files = sorted(
        p.name for p in destination.iterdir() if p.is_file() and p.name.endswith("-dd.csv")
    )
    if not dd_files:
        raise ValueError(
            f"No *-dd.csv files found in {destination}; cannot generate _{schema_name}_study.yaml"
        )

    data_dictionary = {
        filename[: -len("-dd.csv")].lower(): {"identifier": filename} for filename in dd_files
    }

    study_doc = {
        "model_name": schema_name,
        "model_prefix": schema_name,
        "format": "ftd_dd",
        "data_dictionary": data_dictionary,
    }

    output_path = destination / f"_{schema_name}_study.yaml"
    with output_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(study_doc, handle, sort_keys=False, default_flow_style=False)

    return output_path


def main() -> int:
    """Run the import command and return a process exit code."""

    args = parse_args()

    try:
        repo_root = Path(args.repo_root).resolve()
        schema_dir = (
            repo_root
            / "src"
            / "ftd_schema"
            / "schema"
            / args.schema_type
            / args.schema_name
        )

        if not schema_dir.exists():
            raise FileNotFoundError(f"Schema directory not found: {schema_dir}")

        destination = schema_dir / args.tag
        target_subdir = args.target_subdir
        if target_subdir is None:
            target_subdir = (
                "data_dictionary" if args.schema_type == "common_data_model" else ""
            )
        if target_subdir:
            destination = destination / target_subdir
        if destination.exists():
            if not args.replace_existing:
                raise FileExistsError(
                    f"Destination already exists: {destination}. "
                    "Use --replace-existing to overwrite."
                )
            shutil.rmtree(destination)

        destination.mkdir(parents=True, exist_ok=False)

        zip_bytes = fetch_zip_to_memory(args.zip_file, args.zip_url)

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            source_prefix = resolve_source_prefix(zf, args.source_subdir)

        extracted_files = extract_selected_tree(zip_bytes, source_prefix, destination)
        if extracted_files == 0:
            shutil.rmtree(destination, ignore_errors=True)
            raise ValueError("No files extracted from zip. Check --source-subdir and artifact contents.")

        generated_study_path = None
        if (
            args.schema_type == "common_data_model"
            and target_subdir == "data_dictionary"
        ):
            generated_study_path = generate_study_yaml(destination, args.schema_name)

        print(f"Imported {extracted_files} files to {destination}")
        if generated_study_path is not None:
            print(f"Generated study YAML: {generated_study_path}")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
