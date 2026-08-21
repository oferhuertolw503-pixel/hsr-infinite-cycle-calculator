from dataclasses import dataclass


@dataclass
class ResourceState:
    """Continuous battle resources."""

    energy: float = 0.0
    skill_points: float = 3.0
    action_value: float = 0.0

    def apply(self, energy=0.0, skill_points=0.0):
        self.energy += energy
        self.skill_points += skill_points

    def snapshot(self):
        return {
            "energy": self.energy,
            "skill_points": self.skill_points,
            "action_value": self.action_value,
        }
