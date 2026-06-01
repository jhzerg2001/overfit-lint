"""A tiny registry so rule modules self-register on import."""
from __future__ import annotations

from .rule import Rule

_REGISTRY: dict[str, Rule] = {}


def register(rule_cls: type[Rule]) -> type[Rule]:
    """Class decorator: instantiate and register a rule by its ``rule_id``."""
    instance = rule_cls()
    rule_id = getattr(instance, "rule_id", "")
    if not rule_id:
        raise ValueError(f"{rule_cls.__name__} must set a non-empty rule_id")
    if rule_id in _REGISTRY:
        raise ValueError(f"duplicate rule_id {rule_id!r}")
    _REGISTRY[rule_id] = instance
    return rule_cls


def all_rules() -> list[Rule]:
    """All registered rules, sorted by id for stable output."""
    return [_REGISTRY[k] for k in sorted(_REGISTRY)]


def get_rule(rule_id: str) -> Rule | None:
    return _REGISTRY.get(rule_id)
