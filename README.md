# HSR Infinite Cycle Calculator

崩坏：星穹铁道永动机数学建模与计算器。

开发依据：《崩铁永动机的矩阵理论.md》——资源转移矩阵的谱半径决定线性长期趋势；实战"永动"还须满足上限、阈值、时序与敌方行动四类约束。理论到代码的逐节映射见 [docs/theory_implementation_map.md](docs/theory_implementation_map.md)；端到端案例（`样例/` 截图的完整建模与核验）见 [docs/case_study_yangli.md](docs/case_study_yangli.md)。

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
- 版本数据管理（§7 步骤 8：`MatrixLibrary` 把每张 A 与版本/模式/祝福/敌方机制绑定后对比，regime 不一致即警告禁止外推）
- 断轴分类与时序报告（§8"断轴究竟是资源问题还是时序问题"：`CycleDetector` + `--report` 一键汇总）

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
python -m src examples/himeko_nova_cycle_demo.json
python main.py examples/himeko_nova_cycle_demo.json
python main.py examples/theory_document/four_node_model_N5.json
python main.py examples/theory_document/four_node_model_N5.json --sensitivity --repair
python main.py examples/theory_document/four_node_kill_energy.json --audit
python main.py examples/theory_document/seven_node_family.json --family
python main.py examples/theory_document/version_matrix_library.json --library
python main.py examples/theory_document/seven_node_real_family.json --family
python main.py examples/theory_document/four_node_kill_real_family.json --family
python main.py examples/theory_document/audit_workflow_demo.json --audit
python main.py examples/theory_document/audit_workflow_demo.json --report
python main.py examples/team_simulation_demo.json --team
python main.py examples/team_search_demo.json --search
```

`examples/theory_document/` 下的示例复现理论文档 §6 的谱半径数值
（阶段一截图矩阵 0.88856、击杀回能 1.02442、七节点 N=2..5 的
1.00522..1.04432）。注意：文档 §6 对阶段一标注 0.88353，与截图矩阵
计算值 0.88856 不符，**以截图为准**（见 `docs/case_study_yangli.md` §4）。
`audit_workflow_demo.json --audit` 跑通 §7 八步审计全流程：N=2 时去掉
缇宝大招自充能或 C→H_U 回流减半，谱半径即翻转为衰减（rho<1）；目标数
升到 N=5 后保持稳健——演示"哪条边决定成败"。
`four_node_model_N5.json --sensitivity --repair` 演示 §4/§8 定位与修复：
解析弹性 `d rho/d a_ij = u_i v_j` 与数值差分一致（误差 ~1e-7），
决定性边是 C→H_U（弹性最大），最脆弱边与最小修复落在 H_U 自循环
（系数 x1.30、增加 0.18 即达临界 rho=1）。`--family` 输出附临界目标数 N
（"目标数从哪里进入系统"，§8）。
`version_matrix_library.json --library` 演示 §7 步骤 8 版本数据管理：
九个变体（四节点/七节点 × 不同来源、敌方机制与目标数）经 `source` 引用
既有示例文件（可再生、不复制数值），对比表给出各上下文的 rho/regime；
regime 不一致时明确警告"结论上下文绑定，禁止外推"，多粒度时提示
rho 不可跨粒度排名。`--report` 输出谱半径+Perron+瓶颈+时序断轴分类
的一键完整报告。

**截图实测矩阵**（`样例/` 截图逐边转录，数值全部对齐后才入库）：
`four_node_model_N5.json` 为阶段一截图矩阵（H/H_U/C/M，rho=0.88856，
Perron 向量 (0.207,0.542,0.091,0.161)，歧义单元格 H_U→M 读 1/5）；
`seven_node_real_family.json` 复现截图特征值 N=2..5 = 1.00522/1.01872/
1.03174/1.04432 与 N=5 特征向量；`four_node_kill_real_family.json` 复现
rho=1.02442 与文档 §4 的 α——且给出真实临界目标数：N=3 时 0.99683<1
仍衰减，N=4 时 1.01088 首次越过 1（§8）。实测变体已入版本矩阵库
（provenance="实测"）。文档 §6 对阶段一标注的 0.88353 与截图矩阵不符，
保留在 JSON 的 `documented_rho_doc` 字段仅作对照。

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
- [x] 完整技能/光锥/命座数据表与优先级编辑器（schema v2：
      `data/characters/*.json` + `docs/character_data_schema.md`；
      `PriorityEditor`/`priority_overrides` 运行时与队伍级编辑，
      CLI `--team` 一键模拟 + §8 断轴判定）

### Phase 3: Optimization（矩阵层）✅

- [x] 参数敏感性分析（`--sensitivity`：解析弹性 `d rho/d a_ij = u_i v_j`、
      数值差分交叉验证、脆弱边/潜在新边排序；主导根非单实根时自动退化数值）
- [x] 自动寻找循环组合（`--repair`：达到 rho>=1 的最小单边干预规划，
      含一阶弹性估计交叉核对；`critical_parameter` 给出临界目标数 N）
- [x] 版本数据管理（`--library`：`MatrixLibrary` 版本/模式/祝福/敌方机制
      注册表，`compare()` 给出 regime 一致性与外推警告，§7 步骤 8）
- [x] 断轴分类与一键报告（`CycleDetector` 资源/触发/时序三类断轴，
      `Report` + `--report` 汇总，§8）
- [x] 队伍搜索与稳定性最大化（模拟器层，`--search`：枚举角色组合 ×
      优先级排轴（含关闭耗点技能的省点变体），按 是否持续 > 完成循环数 >
      §8 断轴类别 > 终结技次数 排序，输出可直接粘贴进队伍文件的最优
      `priority_overrides`）

## 目录结构

```
src/
  matrix/      转移矩阵引擎（transfer_matrix, perron, irreducibility,
               capped, family, library, validator, visualization）
  analyzer/    瓶颈敏感性（bottleneck）、修复规划与临界 N（optimizer）、
               队伍搜索（team_search）、版本矩阵库对比（library+loader）、
               断轴分类（cycle_detector）、一键报告（report）、
               八步审计（audit）、扰动测试（robustness）
  simulation/  离散时序引擎（timed_engine, speed_engine, priority）
  data_loader/ 角色与矩阵示例加载（含角色 schema 校验）
  cli.py       命令行参数解析与路由
  cli_handlers.py  各分析模式的调用与终端展示
examples/      示例（含 theory_document/ 文档案例复现与队伍模拟）
data/          角色数据（schema v2：技能/光锥/命座/优先级，
               见 docs/character_data_schema.md）
tools/         示例生成脚本
docs/          架构、理论映射文档与示例图
```

## 开发

Python >= 3.10，依赖见 `requirements.txt`（numpy / scipy / matplotlib / pandas）。

推荐使用 `python -m src <示例>` 作为统一入口；`python main.py` 继续保留为
兼容入口。

```bash
python -m pytest tests/ -q
python tools/generate_theory_examples.py   # 重新生成文档案例（可复现）
```
