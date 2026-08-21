"""Battle event abstraction."""

from dataclasses import dataclass, field


@dataclass
class Event:
    name: str
    outputs: dict = field(default_factory=dict)
    conditions: dict = field(default_factory=dict)

    def can_trigger(self, state):
        for key, value in self.conditions.items():
            if state.get(key, 0) < value:
                return False
        return True
