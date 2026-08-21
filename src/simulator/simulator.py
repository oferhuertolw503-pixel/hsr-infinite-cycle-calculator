"""Discrete event simulation core."""


class Simulator:
    def __init__(self, events):
        self.events = events
        self.state = {}
        self.history = []

    def step(self):
        triggered = []
        for event in self.events:
            if event.can_trigger(self.state):
                triggered.append(event.name)
        self.history.append(triggered)
        return triggered

    def run(self, turns=10):
        return [self.step() for _ in range(turns)]
