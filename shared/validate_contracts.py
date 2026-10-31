"""Validate shared wire formats locally, without fetching schema URLs."""
from __future__ import annotations

import argparse
import json
import sys
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

SHARED_DIR = Path(__file__).resolve().parent
EXAMPLES_DIR = SHARED_DIR / "examples"


def _local_only(uri: str) -> Resource:
    raise NoSuchResource(ref=uri)


@lru_cache(maxsize=1)
def _schemas():
    contract = json.loads((SHARED_DIR / "api_contract.json").read_text(encoding="utf-8"))
    evidence = json.loads((SHARED_DIR / "schemas/evidence_schema.json").read_text(encoding="utf-8"))
    registry = Registry(retrieve=_local_only)
    for schema in (contract, evidence):
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return contract, evidence, registry


def get_validator(definition: str = "navigate_response") -> Draft202012Validator:
    """Return a validator usable by backend, frontend-fixture and RAG tests."""
    contract, evidence, registry = _schemas()
    if definition == "evidence":
        schema_ref = evidence["$id"]
    elif definition in contract["$defs"]:
        schema_ref = f"{contract['$id']}#/$defs/{definition}"
    else:
        raise ValueError(f"Unknown contract definition: {definition}")
    return Draft202012Validator(
        {"$ref": schema_ref}, registry=registry, format_checker=FormatChecker()
    )


def validate(payload, definition: str = "navigate_response") -> None:
    """Raise jsonschema.ValidationError on invalid data; never coerce inputs."""
    get_validator(definition).validate(payload)


def _check_file(path: Path, definition: str) -> bool:
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = list(get_validator(definition).iter_errors(payload))
    if errors:
        for error in errors:
            location = "/" + "/".join(str(part) for part in error.absolute_path)
            print(f"FAIL {path.name} {location}: {error.message}", file=sys.stderr)
        return False
    print(f"PASS {path.name} ({definition})")
    return True


def main(argv=None) -> int:
    contract, _, _ = _schemas()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", nargs="?", type=Path, help="JSON file; omit to check all shared examples")
    parser.add_argument("--definition", choices=[*contract["$defs"], "evidence"], default="navigate_response")
    args = parser.parse_args(argv)
    try:
        if args.payload:
            return 0 if _check_file(args.payload, args.definition) else 1
        manifest = json.loads((EXAMPLES_DIR / "manifest.json").read_text(encoding="utf-8"))
        results = [_check_file(EXAMPLES_DIR / entry["file"], entry["definition"]) for entry in manifest]
        return 0 if all(results) else 1
    except (OSError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
