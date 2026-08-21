"""Trigger conditions for battle events."""


class Trigger:
    def __init__(self, name, condition):
        self.name = name
        self.condition = condition

    def check(self, state):
        return self.condition(state)
