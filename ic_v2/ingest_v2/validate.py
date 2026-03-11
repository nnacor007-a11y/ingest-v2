from typing import Any, Dict

from .errors import ValidationError


ALLOWED_TARGET_ENTITY_TYPES = {"plant", "site", "owner", "project"}


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _req(payload: Dict[str, Any], key: str) -> Any:
    if key not in payload:
        raise ValidationError(f"ValidationError:MissingField:{key}")
    return payload[key]


def _validate_confidence(v: Any) -> None:
    if not _is_number(v):
        raise ValidationError("ValidationError:InvalidType:confidence")
    if v < 0 or v > 1:
        raise ValidationError("ValidationError:OutOfRange:confidence")


def _validate_target_entity_type(v: Any) -> None:
    if not isinstance(v, str):
        raise ValidationError("ValidationError:InvalidType:target_entity_type")
    if v not in ALLOWED_TARGET_ENTITY_TYPES:
        raise ValidationError("ValidationError:InvalidEnum:target_entity_type")


def _validate_string(v: Any, field: str) -> None:
    if not isinstance(v, str) or not v.strip():
        raise ValidationError(f"ValidationError:InvalidString:{field}")


FACT_RULES: Dict[str, Dict[str, Any]] = {
    "plant_attribute": {
        "required": [
            "fact_type",
            "target_entity_type",
            "target_entity_id",
            "attribute_key",
            "attribute_value",
            "confidence",
        ],
        "types": {
            "target_entity_id": "string",
            "attribute_key": "string",
            "attribute_value": "string",
        },
    }
}


def validate_fact_payload(payload: Dict[str, Any]) -> None:
    fact_type = _req(payload, "fact_type")

    if not isinstance(fact_type, str) or not fact_type.strip():
        raise ValidationError("ValidationError:InvalidString:fact_type")

    if fact_type not in FACT_RULES:
        raise ValidationError(f"ValidationError:UnknownFactType:{fact_type}")

    _validate_target_entity_type(_req(payload, "target_entity_type"))
    _validate_confidence(_req(payload, "confidence"))

    rules = FACT_RULES[fact_type]

    for k in rules.get("required", []):
        _req(payload, k)

    for field, typ in rules.get("types", {}).items():
        v = _req(payload, field)
        if typ == "string":
            _validate_string(v, field)
        else:
            raise ValidationError(f"ValidationError:RuleTypeUnsupported:{field}")