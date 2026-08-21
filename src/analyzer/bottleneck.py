"""Detect limiting resources."""


class BottleneckAnalyzer:
    def analyze(self, history):
        result = {}
        if not history:
            return result

        for key in ["energy", "skill_points"]:
            values = [item.get(key, 0) for item in history]
            result[key] = min(values)

        return result
