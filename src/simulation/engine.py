class BattleEngine:
    """Discrete event battle simulator."""

    def __init__(self, actions, state):
        self.actions = actions
        self.state = state
        self.history = []

    def step(self):
        for action in self.actions:
            if action.execute(self.state):
                self.history.append(self.state.snapshot())
                return True
        return False

    def run(self, turns=100):
        for _ in range(turns):
            self.step()

        return {
            "turns": turns,
            "history": self.history,
            "final_state": self.state.snapshot(),
        }
