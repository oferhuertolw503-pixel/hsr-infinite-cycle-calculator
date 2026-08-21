"""Cycle stability analysis."""


class CycleDetector:
    def analyze(self, simulation_result):
        history = simulation_result.get("history", [])
        if not history:
            return {"stable": False, "reason": "No simulation data"}

        last = history[-1]
        stable = last.get("energy", 0) >= 0 and last.get("skill_points", 0) >= 0

        return {
            "stable": stable,
            "turns": len(history),
            "reason": "stable resource cycle" if stable else "resource depletion"
        }
