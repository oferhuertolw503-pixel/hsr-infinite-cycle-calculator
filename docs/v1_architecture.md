# Version 1 Architecture

## Pipeline

```
Character Data / Matrix Examples (JSON)
  -> TransferMatrix (矩阵引擎)
  -> Spectral Analysis (谱半径 / Perron / 不可约性 / 分类)
  -> CycleAudit (§7 八步复核: 粒度 -> 量纲 -> 逐边填表 -> 谱半径
                 -> Perron -> 时序模拟 -> 扰动测试 -> 版本区分)
  -> SpeedBattleEngine (离散时序验证: AV=10000/速度, 敌方时钟,
                       上限/阈值/可执行性)
  -> Report (CLI: python main.py <example> [--family] [--audit])
```

核心思想：矩阵理论用于发现循环结构，离散事件模拟用于验证实战可行性。

## 当前活跃模块

| 模块 | 职责 |
|---|---|
| `src/matrix/` | 转移矩阵、谱半径、Perron、不可约性、封顶系统、N 族、可视化 |
| `src/analyzer/` | 八步审计（audit）、扰动测试（robustness） |
| `src/simulation/` | 时序引擎（timed_engine）、速度驱动引擎（speed_engine） |
| `src/data_loader/` | 角色与矩阵示例加载 |

## 遗留骨架（未接入活跃管线）

`src/battle/` 与 `src/simulator/` 是早期骨架实现，未在任何代码中引用；
`src/core/` 的部分概念已并入 `src/simulation/`。新开发应基于
`src/simulation/` 与 `src/matrix/`。

## 优化目标

搜索队伍并最大化稳定性，约束包括：

- 能量约束（上限、阈值开大）
- 技能点约束（上限、消耗/回复）
- 行动值约束（AV = 10000 / 速度）
- 触发条件（追加攻击、插入行动不消耗通常回合）
- 敌方行动约束（闭环须在敌方行动前完成）

矩阵模型提供理论分析，模拟器验证实际离散执行。
