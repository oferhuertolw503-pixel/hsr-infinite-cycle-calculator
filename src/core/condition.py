class Condition:
    """Base condition used to decide whether an event can trigger."""

    def check(self, state):
        return True


class EnergyFull(Condition):
    def check(self, state):
        return state.energy >= state.max_energy


class EnemyBroken(Condition):
    def check(self, state):
        return getattr(state, "enemy_broken", False)


class SkillPointAvailable(Condition):
    def check(self, state):
        return state.skill_points > 0
