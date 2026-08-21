"""Team composition model."""


class Team:
    def __init__(self, members):
        self.members = members

    def names(self):
        return [m.get("name") for m in self.members]

    def events(self):
        result = []
        for member in self.members:
            result.extend(member.get("events", []))
        return result
