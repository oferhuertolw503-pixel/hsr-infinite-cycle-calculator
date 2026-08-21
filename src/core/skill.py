"""Skill abstraction.

A skill produces one or more resource events.
"""


class Skill:
    def __init__(self, name, events=None, trigger=None):
        self.name = name
        self.events = events or []
        self.trigger = trigger

    def execute_events(self):
        return self.events
