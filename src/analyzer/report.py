"""Generate readable simulation reports."""


class Report:
    def generate(self, matrix_result, simulation_result, cycle_result):
        return {
            "matrix": matrix_result,
            "simulation": simulation_result,
            "cycle": cycle_result
        }
