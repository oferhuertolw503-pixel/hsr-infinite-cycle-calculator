"""Cycle break classification (theory document section 8).

The matrix model answers whether the linear loop decays; a discrete
simulation answers whether an ordered run actually sustains it.  This
detector consumes the result dicts of the current engines --

  TimedBattleEngine.run:  stable / loops_completed / break_reason
                          (enemy_interjection | energy_shortage_at_* |
                           skill_point_shortage_at_* | condition_failed_at_*)
  SpeedBattleEngine.run:  cycles_completed / break_reason
                          (enemy_interjection | no_executable_action)

-- and classifies the break cause into the dichotomy of section 8:
"断轴究竟是资源问题还是时序问题" (resource vs timing), with trigger
thresholds (section 5.2 conditions) as a third class of their own.
"""

from __future__ import annotations

_RESOURCE_PREFIXES = (
    "energy_shortage",
    "skill_point_shortage",
)
_RESOURCE_REASONS = {"no_executable_action"}
_TIMING_REASONS = {"enemy_interjection"}
_CONDITION_PREFIX = "condition_failed"

_CLASS_NOTES = {
    "sustained": "闭环在模拟界限内持续,资源与时序均未断轴。",
    "resource": (
        "资源问题:能量/技能点在关键事件前短缺,账面产出即使守恒,"
        "顺序上也付不起(§5.3 可执行性)。"
    ),
    "condition": (
        "触发问题:条件/阈值不满足(如能量未满、目标数不足),"
        "转移边被状态关闭(§5.2 A=A(x_t,N,s_t))。"
    ),
    "timing": (
        "时序问题:敌方行动值在闭环完成前归零,敌方插队打断序列(§5.4);"
        "资源账面可能仍然是平的。"
    ),
    "unknown": "未知断轴原因,须人工检查模拟日志。",
}


class CycleDetector:
    """Classify whether a discrete run sustains the loop, and why not."""

    def analyze(self, simulation_result):
        if not isinstance(simulation_result, dict):
            raise TypeError(
                "expected a TimedBattleEngine/SpeedBattleEngine result dict"
            )
        reason = simulation_result.get("break_reason")
        stable = bool(simulation_result.get("stable", reason is None))
        loops = simulation_result.get(
            "loops_completed", simulation_result.get("cycles_completed", 0)
        )
        break_class = self.classify_reason(reason) if not stable else "sustained"
        return {
            "stable": stable,
            "loops_completed": loops,
            "break_reason": reason,
            "break_class": break_class,
            "enemy_interjected": (
                reason == "enemy_interjection"
                or simulation_result.get("enemy_actions", 0) > 0
            ),
            "note": _CLASS_NOTES[break_class],
        }

    @staticmethod
    def classify_reason(reason):
        """Map an engine break_reason to resource / condition / timing."""
        if reason is None:
            return "sustained"
        if reason in _TIMING_REASONS:
            return "timing"
        if reason in _RESOURCE_REASONS or reason.startswith(_RESOURCE_PREFIXES):
            return "resource"
        if reason.startswith(_CONDITION_PREFIX):
            return "condition"
        return "unknown"
