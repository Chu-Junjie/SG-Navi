"""Validate the frozen guidance integration contract with local-only references."""
import json
from functools import lru_cache
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def validators():
    def deny(uri):
        raise NoSuchResource(ref=uri)
    registry = Registry(retrieve=deny)
    resources = []
    for name in ("guidance_contract.json", "display_evidence_contract.json", "schemas/evidence_schema.json"):
        schema = json.loads((ROOT / "shared" / name).read_text(encoding="utf-8"))
        resources.append((schema["$id"], schema))
    for case in ("rental_deposit", "consumer_complaint"):
        name = f"frontend/schemas/{case}_input.schema.json"
        resources.append(("https://sg-navi.invalid/" + name, json.loads((ROOT / name).read_text(encoding="utf-8"))))
    for uri, schema in resources:
        Draft202012Validator.check_schema(schema)
        registry = registry.with_resource(uri, Resource.from_contents(schema))
    return {key: Draft202012Validator({"$ref": "https://sg-navi.invalid/shared/guidance_contract.json#/$defs/" + key}, registry=registry, format_checker=FormatChecker()) for key in ("request", "response")}


def validate_guidance(data, definition="response"):
    validators()[definition].validate(data)
