# 理论文档 → 代码实现映射

本文档把《崩铁永动机的矩阵理论.md》的各节映射到本仓库的模块、示例与测试，便于按理论持续开发与复核。

## 行文约定

- 行向量记法（§2.2）：`x_{t+1} = x_t A`，`A[i,j]` 表示第 i 类事件平均产生第 j 类后继事件数。
- 结论措辞遵循 §6：`rho>1` 只报告"线性增长方向"，绝不单独宣布实战永动。

## 映射表

| 理论节 | 内容 | 代码/数据 | 测试 |
|---|---|---|---|
| §2.1 | 事件节点与状态向量 | `TransferMatrix.node_names`；七节点 `H,H_U,C,M,C_U,T,T_U` 见 `examples/theory_document/seven_node_family.json` | `tests/test_theory_examples.py` |
| §2.2 | 资源转移矩阵、行向量记法 | `src/matrix/transfer_matrix.py`（`iterate` 按 `x_t A` 迭代） | `tests/test_matrix.py::test_iterate_row_convention` |
| §2.3 | 假设 A1 非负性 | `validate_matrix`（`non_negative`/`finite`/`square`） | `tests/test_matrix.py::test_rejects_*` |
| §3 引理 1 | `x_{t+n}=x_t A^n` | `TransferMatrix.iterate` / `vector_decay_horizon` | 同上 |
| §3 定理 1 | `rho<1 ⇒ A^n→0` | `TransferMatrix.classify` regime=`decay` | `test_classify_decay` |
| §3 定理 2 | `rho=1` 临界、Perron 向量 | regime=`critical`；`dominant_pair` | `test_classify_critical_irreducible` |
| §3 定理 3 | `rho>1` 仅增长方向 | regime=`growth` + caveats；`growth_doubling_time` | `test_classify_growth` |
| §3 反推限制 | 上限/阈值/时序/敌方四类约束 | `classify` 的 caveats 恒附注 | `test_classify_growth` 断言"不能单独推出实战无限循环" |
| §4 | Perron 向量 = 相对频率、瓶颈定位 | `perron_frequencies`（最小份额节点标记 `flagged_as_scarce`） | `test_perron_vector_normalized` |
| §5.1 | 上限：`x_{t+1}=min(c, x_t A + b_t)` | `src/matrix/capped.py` `CappedTransferSystem` | `tests/test_capped.py` |
| §5.2 | 阈值/目标数：`A=A(x_t,N,s_t)` | `src/matrix/family.py` `MatrixFamily`；N 进入 T_U 相关转移的七节点族 | `tests/test_theory_examples.py`、`test_family` 相关 |
| §5.3 | 时序：`Executable(e_k)⟺x_k≥cost ∧ condition` | `src/simulation/timed_engine.py` `TimedBattleEngine`；速度驱动引擎 `src/simulation/speed_engine.py` | `tests/test_timed_engine.py`、`tests/test_speed_engine.py` |
| §5.4 | 敌方时钟 `q_t`、插队/额外回合不推进 | `TimedBattleEngine`（`enemy_av`、`no_advance`）；`SpeedBattleEngine` 的敌方行动值 | `test_enemy_clock_*`、`test_inserted_actions_*`、`tests/test_speed_engine.py` |
| §6 | 案例数值：0.88353 / 1.02442 / 1.00522..1.04432 | `examples/theory_document/*.json`（重构演示矩阵） | `tests/test_theory_examples.py` |
| §7 | 八步复核流程 | `src/analyzer/audit.py` `CycleAudit`；全流程示例 `examples/theory_document/audit_workflow_demo.json` | `tests/test_audit.py`、`tests/test_audit_demo.py` |
| §7 步骤 7 | 扰动测试（N/未击杀/治疗缺失/插队） | `src/analyzer/robustness.py` | `tests/test_robustness.py` |
| §8 | 哪条边决定成败 | `TransferMatrix.edge_sensitivity`；N=2 单边缺失即翻转 regime 的审计演示 | `test_edge_sensitivity_*`、`tests/test_audit_demo.py` |
| §1.1（模拟层） | AV=10000/速度、插入行动不消耗通常回合 | `src/simulation/speed_engine.py` `SpeedBattleEngine` | `tests/test_speed_engine.py` |
| §5.1（模拟层） | 能量/技能点封顶 | `SpeedBattleEngine`（`energy_cap`、`sp_cap`） | `test_energy_is_capped`、`test_skill_points_are_capped` |
| §5.2（模拟层） | "能量满才开大"阈值 → 可执行动作集随状态改变 | `SpeedBattleEngine` 的大招阈值触发（插入动作） | `test_ultimate_fires_at_threshold_*` |
| 可视化 | Phase 1 矩阵可视化 | `src/matrix/visualization.py`（heatmap / 有向图 / rho 曲线） | `tests/test_visualization.py`；示例图见 `docs/figures/` |

## 关键数值复现

在仓库根目录运行 `python main.py <示例>` 可复现文档 §6 数值：

| 示例 | 谱半径（计算） | 文档 §6 |
|---|---|---|
| `four_node_model_N5.json` | 0.88353 | 第一组参数 N=5 |
| `four_node_kill_energy.json` | 1.02442 | 调整转移并加入击杀回能 |
| `seven_node_family.json --family` | 1.00522 / 1.01825 / 1.03129 / 1.04432 (N=2..5) | 七节点模型 N=2..5 |

> 注意：文档 §6 只记录了谱半径，未给出原矩阵。示例矩阵是"谱半径与文档一致"的**重构演示值**，非截图原值；如需正式结论，应把截图中的真实矩阵按 §7 流程逐边填表后替换。

## 重构示例的再生

`python tools/generate_theory_examples.py` 可重新生成 `examples/theory_document/` 下的四个文件：

- 四节点矩阵用秩 1 构造 `A = rho·vvᵀ/(vᵀv)`，Perron 根恰为 `rho`、Perron 向量恰为文档 §4 的 α；
- 七节点族以强连通基矩阵精确缩放到 `rho=1.00522`，再对 T_U 相关边（军功、自充能）做二分搜索，使 N=3..5 的谱半径命中目标值，体现 §5.2 的 N 依赖；
- `audit_workflow_demo.json` 以 N=2 基矩阵（rho≈1.00522，略超临界）驱动 §7 全流程审计：扰动测试显示"去掉 T_U 自充能 → rho=0.9965 翻转为衰减"、"C→H_U 回流减半 → rho=0.9856 翻转为衰减"，而"N 升到 5 → rho=1.0443 仍稳健"——直观演示 §8"断轴究竟是资源问题还是时序问题"。

## 战斗模拟（离散验证层）

`SpeedBattleEngine`（`src/simulation/speed_engine.py`）把矩阵结论落到离散时序：

- AV = 10000 / 速度（§1.1），行动值最小的单位先行动；
- 能量/技能点封顶（§5.1）；"能量满才开大"作为状态阈值触发插入动作，且插入动作**不消耗通常回合**（§5.2/§1.1）；
- 敌方行动值归零即插队打断闭环（§5.4），闭环须在敌方行动前完成；
- 角色数据（`data/characters/*.json`，已含 `speed` 字段）经 `unit_from_character_data` 直接构建单位。

示例图（`docs/figures/`）：`four_node_heatmap.png`、`four_node_digraph.png`、`seven_node_family_rho.png`。
