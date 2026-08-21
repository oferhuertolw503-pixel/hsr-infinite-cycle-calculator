"""Character domain model.

Characters are collections of resource events.
"""


class Character:
    def __init__(self, name, events=None):
        self.name = name
        self.events = events or []

    def add_event(self, event):
        self.events.append(event)

    def get_events(self):
        return self.events
