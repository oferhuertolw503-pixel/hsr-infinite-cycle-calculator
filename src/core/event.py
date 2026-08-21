from dataclasses import dataclass


@dataclass
class ResourceEvent:
    """A game action that changes battle resources."""

    name: str
    energy_change: float = 0.0
    sp_change: float = 0.0
    trigger: str | None = None

    def execute(self, state):
        state.apply(
            energy=self.energy_change,
            skill_points=self.sp_change,
        )
