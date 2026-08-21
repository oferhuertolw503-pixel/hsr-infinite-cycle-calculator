# Version 1 Architecture

## Pipeline

```
Character Data / Matrix Examples (JSON)
  -> TransferMatrix (矩阵引擎)
  -> Spectral Analysis (谱半径 / Perron / 不可约性 / 分类)
  -> BottleneckAnalyzer + CycleRepairPlanner (§4/§8: 边际弹性、脆弱边、
                 最小干预修复、临界目标数 N)
  -> CycleAudit (§7 八步复核: 粒度 -> 量纲 -> 逐边填表 -> 谱半径
                 -> Perron -> 时序模拟 -> 扰动测试 -> 版本区分)
  -> MatrixLibrary (§7 步骤 8: 版本/模式/祝福/敌方机制注册表与对比)
  -> SpeedBattleEngine (离散时序验证: AV=10000/速度, 敌方时钟,
                       上限/阈值/可执行性)
  -> CycleDetector + Report (§8 断轴分类: 资源/触发/时序; 一键汇总)
  -> Report (CLI: python main.py <example> [--family] [--audit]
             [--sensitivity] [--repair] [--library] [--report])
```

核心思想：矩阵理论用于发现循环结构，离散事件模拟用于验证实战可行性。

## 当前活跃模块

| 模块 | 职责 |
|---|---|
| `src/matrix/` | 转移矩阵、谱半径、Perron、不可约性、封顶系统、N 族、版本矩阵库（library）、可视化 |
| `src/analyzer/` | 瓶颈敏感性（bottleneck）、修复规划与临界 N（optimizer）、断轴分类（cycle_detector）、一键报告（report）、八步审计（audit）、扰动测试（robustness） |
| `src/simulation/` | 时序引擎（timed_engine）、速度驱动引擎（speed_engine） |
| `src/data_loader/` | 角色与矩阵示例加载、矩阵库加载（source/family_key/perturbation 引用） |

## 遗留骨架（未接入活跃管线）

`src/battle/` 与 `src/simulator/` 是早期骨架实现，未在任何代码中引用；
`src/core/` 的部分概念已并入 `src/simulation/`。新开发应基于
`src/simulation/` 与 `src/matrix/`。

## 优化目标

矩阵层（已实现）：`CycleRepairPlanner` 搜索达到目标谱半径的最小单边干预，
`critical_parameter` 定位临界目标数 N——回答 §8 的定位问题。
模拟器层（待做）：搜索队伍并最大化稳定性，约束包括：

- 能量约束（上限、阈值开大）
- 技能点约束（上限、消耗/回复）
- 行动值约束（AV = 10000 / 速度）
- 触发条件（追加攻击、插入行动不消耗通常回合）
- 敌方行动约束（闭环须在敌方行动前完成）

矩阵模型提供理论分析，模拟器验证实际离散执行。
