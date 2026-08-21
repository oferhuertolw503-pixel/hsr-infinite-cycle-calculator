"""Action value system abstraction."""


class ActionValue:
    def __init__(self, speed: float):
        self.speed = speed
        self.value = 10000 / speed

    def advance(self, amount: float):
        self.value -= amount

    def ready(self) -> bool:
        return self.value <= 0
