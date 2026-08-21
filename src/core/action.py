from dataclasses import dataclass


@dataclass
class Action:
    """One executable battle action."""

    name: str
    skill: object
    condition: object = None

    def can_execute(self, state):
        if self.condition is None:
            return True
        return self.condition.check(state)

    def execute(self, state):
        if not self.can_execute(state):
            return False

        for event in self.skill.execute_events():
            event.execute(state)

        return True
