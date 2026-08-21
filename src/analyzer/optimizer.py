"""Team search and optimization foundation.

Search candidate teams and evaluate them through the simulator.
"""


class TeamOptimizer:
    def __init__(self, simulator):
        self.simulator = simulator

    def evaluate(self, team, turns=1000):
        result = self.simulator.run(team, turns)
        return result

    def rank(self, teams, turns=1000):
        results = []
        for team in teams:
            results.append({
                "team": team,
                "result": self.evaluate(team, turns)
            })
        return sorted(results, key=lambda x: x["result"].get("stable", False), reverse=True)
