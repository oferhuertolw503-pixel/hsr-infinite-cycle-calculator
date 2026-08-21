"""Discrete battle simulator."""

from .battle_state import BattleState


class BattleSimulator:
    def __init__(self, events):
        self.events = events
        self.state = BattleState()

    def run(self, rounds=100):
        for i in range(rounds):
            event = self.events[i % len(self.events)]
            event.execute(self.state)
            self.state.turn += 1
        return self.state

    def report(self):
        return {
            "turns": self.state.turn,
            "energy": self.state.energy,
            "skill_points": self.state.skill_points,
            "history": self.state.history,
        }
