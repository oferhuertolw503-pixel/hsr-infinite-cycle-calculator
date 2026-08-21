"""Battle state model for nonlinear simulation."""

from dataclasses import dataclass, field


@dataclass
class BattleState:
    hp: float = 10000
    energy: float = 0
    skill_points: int = 3
    action_value: float = 0
    turn: int = 0
    history: list = field(default_factory=list)

    def add_energy(self, value):
        self.energy = min(energy_cap := 100, self.energy + value)

    def consume_energy(self, value):
        if self.energy >= value:
            self.energy -= value
            return True
        return False

    def log(self, event):
        self.history.append(event)
