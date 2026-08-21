"""Editable action-priority selector for the speed battle engine.

Priority semantics (section 5.3): among executable standard actions the
engine picks the smallest `priority`, ties broken by declaration order.
Data files set default priorities; this editor changes them at runtime
(set / reorder / enable / disable), serializes the edits as JSON
overrides, and applies such overrides to a team -- so a team file can
re-order a rotation without touching the character tables.

Overrides format (per unit name):

    {"姬子": {"basic_attack": {"priority": 3, "enabled": false},
              "skill": 1}}

Values are either a bare number (priority) or an object with optional
`priority` / `enabled` keys.
"""

from __future__ import annotations


class PriorityEditorError(ValueError):
    """Raised for unknown unit / action names in priority edits."""


def _find_unit(units, unit_name):
    for unit in units:
        if unit.name == unit_name:
            return unit
    raise PriorityEditorError(
        f"unknown unit {unit_name!r}; have "
        f"{[unit.name for unit in units]}"
    )


def _find_action(unit, action_name):
    for action in unit.actions:
        if action.name == action_name:
            return action
    raise PriorityEditorError(
        f"unknown action {action_name!r} on unit {unit.name!r}; have "
        f"{[action.name for action in unit.actions]}"
    )


def apply_priority_overrides(units, overrides):
    """Apply a serialized override map to a list of battle units."""
    for unit_name, actions in overrides.items():
        unit = _find_unit(units, unit_name)
        for action_name, value in actions.items():
            action = _find_action(unit, action_name)
            if isinstance(value, dict):
                if "priority" in value:
                    action.priority = float(value["priority"])
                if "enabled" in value:
                    action.enabled = bool(value["enabled"])
            else:
                action.priority = float(value)
    return units


class PriorityEditor:
    """View and edit the standard-action priorities of a team."""

    def __init__(self, units):
        self.units = list(units)

    # -- edits -------------------------------------------------------------
    def set_priority(self, unit_name, action_name, priority):
        _find_action(_find_unit(self.units, unit_name),
                     action_name).priority = float(priority)
        return self

    def set_enabled(self, unit_name, action_name, enabled):
        _find_action(_find_unit(self.units, unit_name),
                     action_name).enabled = bool(enabled)
        return self

    def disable(self, unit_name, action_name):
        return self.set_enabled(unit_name, action_name, False)

    def enable(self, unit_name, action_name):
        return self.set_enabled(unit_name, action_name, True)

    def reorder(self, unit_name, ordered_names):
        """Assign priorities 0..n-1 following the given action order."""
        unit = _find_unit(self.units, unit_name)
        known = {action.name for action in unit.actions}
        missing = set(ordered_names) - known
        if missing:
            raise PriorityEditorError(
                f"unknown actions {sorted(missing)} on unit {unit.name!r}"
            )
        for rank, name in enumerate(ordered_names):
            _find_action(unit, name).priority = float(rank)
        return self

    # -- views ---------------------------------------------------------------
    def view(self):
        """Editable priority table: one row per standard/inserted action."""
        rows = []
        for unit in self.units:
            for index, action in enumerate(unit.actions):
                rows.append({
                    "unit": unit.name,
                    "action": action.name,
                    "priority": action.priority,
                    "enabled": action.enabled,
                    "inserted": action.inserted,
                    "declaration_index": index,
                })
        return rows

    def to_overrides(self):
        """Serialize current priorities/enabled flags as an override map."""
        overrides = {}
        for row in self.view():
            entry = overrides.setdefault(row["unit"], {})
            entry[row["action"]] = {
                "priority": row["priority"],
                "enabled": row["enabled"],
            }
        return overrides
