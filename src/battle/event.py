"""Event system."""

from dataclasses import dataclass


@dataclass
class BattleEvent:
    name: str
    energy_gain: float = 0
    energy_cost: float = 0
    skill_point_change: int = 0

    def execute(self, state):
        state.add_energy(self.energy_gain)
        state.consume_energy(self.energy_cost)
        state.skill_points += self.skill_point_change
        state.log(self.name)
