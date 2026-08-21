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
| §5.3 | 时序：`Executable(e_k)⟺x_k≥cost ∧ condition` | `src/simulation/timed_engine.py` `TimedBattleEngine` | `tests/test_timed_engine.py` |
| §5.4 | 敌方时钟 `q_t`、插队/额外回合不推进 | `TimedBattleEngine`（`enemy_av`、`no_advance`） | `test_enemy_clock_*`、`test_inserted_actions_*` |
| §6 | 案例数值：0.88353 / 1.02442 / 1.00522..1.04432 | `examples/theory_document/*.json`（重构演示矩阵） | `tests/test_theory_examples.py` |
| §7 | 八步复核流程 | `src/analyzer/audit.py` `CycleAudit` | `tests/test_audit.py` |
| §7 步骤 7 | 扰动测试（N/未击杀/治疗缺失/插队） | `src/analyzer/robustness.py` | `tests/test_robustness.py` |
| §8 | 哪条边决定成败 | `TransferMatrix.edge_sensitivity` | `test_edge_sensitivity_*` |

## 关键数值复现

在仓库根目录运行 `python main.py <示例>` 可复现文档 §6 数值：

| 示例 | 谱半径（计算） | 文档 §6 |
|---|---|---|
| `four_node_model_N5.json` | 0.88353 | 第一组参数 N=5 |
| `four_node_kill_energy.json` | 1.02442 | 调整转移并加入击杀回能 |
| `seven_node_family.json --family` | 1.00522 / 1.01825 / 1.03129 / 1.04432 (N=2..5) | 七节点模型 N=2..5 |

> 注意：文档 §6 只记录了谱半径，未给出原矩阵。示例矩阵是"谱半径与文档一致"的**重构演示值**，非截图原值；如需正式结论，应把截图中的真实矩阵按 §7 流程逐边填表后替换。

## 重构示例的再生

`python tools/generate_theory_examples.py` 可重新生成 `examples/theory_document/` 下的三个文件：

- 四节点矩阵用秩 1 构造 `A = rho·vvᵀ/(vᵀv)`，Perron 根恰为 `rho`、Perron 向量恰为文档 §4 的 α；
- 七节点族以强连通基矩阵精确缩放到 `rho=1.00522`，再对 T_U 相关边（军功、自充能）做二分搜索，使 N=3..5 的谱半径命中目标值，体现 §5.2 的 N 依赖。
