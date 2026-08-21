# HSR Infinite Cycle Calculator

崩坏：星穹铁道永动机数学建模与计算器。

开发依据：《崩铁永动机的矩阵理论.md》——资源转移矩阵的谱半径决定线性长期趋势；实战"永动"还须满足上限、阈值、时序与敌方行动四类约束。理论到代码的逐节映射见 [docs/theory_implementation_map.md](docs/theory_implementation_map.md)。

## 项目目标

将游戏中的资源循环机制抽象为可计算系统：

- 事件节点建模（事件而非角色）
- 资源转移矩阵（行向量记法 `x_{t+1}=x_t A`）
- 谱半径分析（定理 1/2/3：衰减 / 临界 / 增长方向）
- Perron 特征向量分析（相对频率与瓶颈定位）
- 不可约性检查（Perron-Frobenius 严格正性的前提）
- 封顶系统 `x_{t+1}=min(c, x_t A + b_t)`（§5.1）
- N 依赖矩阵族（§5.2，目标数进入矩阵条目）
- 敌方时钟与可执行性时序模拟（§5.3/§5.4）
- 八步复核流程审计（§7）与扰动测试
- 瓶颈定位与敏感性分析（§4/§8：解析弹性 `d rho/d a_ij = u_i v_j`、脆弱边、潜在新边）
- 循环修复规划（矩阵层"自动寻找循环组合"：最小单边干预达到 rho>=1、临界目标数 N）

核心思想：

> 矩阵理论用于发现循环结构，离散事件模拟用于验证实战可行性。

## 数学模型

设状态向量为 \(x_t\)，资源转移矩阵为非负矩阵 \(A\)：

```
x_(t+1) = x_t A
```

长期趋势由谱半径决定：

- rho(A) < 1：线性资源衰减（定理 1，足以否定纯线性永动）
- rho(A) = 1：理论守恒临界状态（定理 2，Perron 向量给出相对频率）
- rho(A) > 1：存在线性增长方向（定理 3，**不是**实战永动充分条件）

注意：rho(A)>1 并不等价于游戏实战永动，仍需检查资源上限、触发条件、行动顺序和敌方行动（§5）。

## 快速开始

```bash
python main.py examples/himeko_nova_cycle_demo.json
python main.py examples/theory_document/four_node_model_N5.json
python main.py examples/theory_document/four_node_model_N5.json --sensitivity --repair
python main.py examples/theory_document/four_node_kill_energy.json --audit
python main.py examples/theory_document/seven_node_family.json --family
python main.py examples/theory_document/audit_workflow_demo.json --audit
```

`examples/theory_document/` 下的示例复现理论文档 §6 的谱半径数值
（0.88353、1.02442、七节点 N=2..5 的 1.00522..1.04432）；矩阵条目为
"谱半径与文档一致"的重构演示值，非截图原值（见 docs 映射文档）。
`audit_workflow_demo.json --audit` 跑通 §7 八步审计全流程：N=2 时去掉
缇宝大招自充能或 C→H_U 回流减半，谱半径即翻转为衰减（rho<1）；目标数
升到 N=5 后保持稳健——演示"哪条边决定成败"。
`four_node_model_N5.json --sensitivity --repair` 演示 §4/§8 定位与修复：
解析弹性 `d rho/d a_ij = u_i v_j` 与数值差分一致（误差 ~1e-8），
B→B 是决定性边（弹性最大、也最脆弱）；最小修复为把 B→B 系数
x1.26（增加 0.16）即达临界 rho=1。`--family` 输出附临界目标数 N
（"目标数从哪里进入系统"，§8）。

示例图（`docs/figures/`）：四节点转移矩阵热力图/有向图、七节点族 rho 曲线。

## 开发路线

### Phase 1: Matrix Engine ✅

- [x] 基础矩阵表示（校验：方阵、有限、非负 A1）
- [x] 谱半径计算
- [x] 特征向量 / Perron 分析（归一化相对频率、不可约性、复根检测）
- [x] 矩阵族（N 依赖）与封顶系统
- [x] 矩阵可视化（heatmap / 有向图 / rho 曲线，matplotlib）

### Phase 2: Battle Simulator ✅（引擎层）

- [x] 行动值系统（AV = 10000 / 速度，`SpeedBattleEngine`）
- [x] 能量系统接入角色数据（上限、阈值开大）
- [x] 技能点系统接入角色数据（上限、消耗/回复）
- [x] 追加攻击与插入行动（不消耗通常回合）
- [x] 敌方行动约束（行动值时钟，闭环须在敌方行动前完成）
- [ ] 完整技能/光锥/命座数据表与优先级编辑器（游戏侧数据录入）

### Phase 3: Optimization（矩阵层）

- [x] 参数敏感性分析（`--sensitivity`：解析弹性 `d rho/d a_ij = u_i v_j`、
      数值差分交叉验证、脆弱边/潜在新边排序；主导根非单实根时自动退化数值）
- [x] 自动寻找循环组合（`--repair`：达到 rho>=1 的最小单边干预规划，
      含一阶弹性估计交叉核对；`critical_parameter` 给出临界目标数 N）
- [ ] 版本数据管理（不同版本/模式/祝福的 A 矩阵库，§7 步骤 8）

## 目录结构

```
src/
  matrix/      转移矩阵引擎（transfer_matrix, perron, irreducibility,
               capped, family, validator, visualization）
  analyzer/    瓶颈敏感性（bottleneck）、修复规划与临界 N（optimizer）、
               八步审计（audit）、扰动测试（robustness）、循环检测（legacy）
  simulation/  离散时序引擎（timed_engine, speed_engine, engine）
  battle/      行动值/战斗状态（legacy 骨架）
  data_loader/ 角色与矩阵示例加载
  cli.py       命令行入口
examples/      示例（含 theory_document/ 文档案例复现）
data/          角色数据（含 speed 字段）
tools/         示例生成脚本
docs/          架构、理论映射文档与示例图
```

## 开发

Python >= 3.10，依赖见 `requirements.txt`（numpy / scipy / matplotlib / pandas）。

```bash
python -m pytest tests/ -q
python tools/generate_theory_examples.py   # 重新生成文档案例（可复现）
```
