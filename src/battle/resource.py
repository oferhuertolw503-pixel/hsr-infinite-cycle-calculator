"""Battle resource state model."""

from dataclasses import dataclass


@dataclass
class ResourceState:
    hp: float = 1.0
    energy: float = 0.0
    skill_points: float = 0.0
    action_value: float = 0.0

    def add_energy(self, value: float):
        self.energy += value

    def consume_energy(self, value: float) -> bool:
        if self.energy >= value:
            self.energy -= value
            return True
        return False
