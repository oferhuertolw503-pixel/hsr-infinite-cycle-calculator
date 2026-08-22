# HSR Infinite Cycle Calculator

崩坏：星穹铁道永动机数学建模与计算器。

开发依据：《崩铁永动机的矩阵理论.md》——资源转移矩阵的谱半径决定线性长期趋势；实战"永动"还须满足上限、阈值、时序与敌方行动四类约束。理论到代码的逐节映射见 [docs/theory_implementation_map.md](docs/theory_implementation_map.md)；端到端案例（`样例/` 截图的完整建模与核验）见 [docs/case_study_yangli.md](docs/case_study_yangli.md)。

## V1：初学者入口

V1 只回答一个问题：**四张案例图里的矩阵和结果能否被诚实地复算？**

```bash
pip install -r requirements.txt
python -m src.v1
```

预期最后一行是 `结论: V1 验收通过`。七节点原图存在一处内部不一致：
矩阵显示 `T→C_U=1/4`，结果表需要 `1/2` 才能复现。V1 分别保存逐格
转录版和结果表校准版，不把两者混成同一份数据。角色资料来源与当前数据
边界见 [docs/v1_character_sources.md](docs/v1_character_sources.md)。

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
python -m src.v1
python -m src examples/theory_document/four_node_model_N5.json
python -m src examples/theory_document/four_node_kill_real_family.json --family
python -m src examples/theory_document/seven_node_real_family.json --family
python -m src examples/theory_document/seven_node_table_calibrated_family.json --family
```

四节点衰减图在 N=5 得 `rho=0.88353`；加入击杀回能后得
`rho=1.02442`，同一公式下临界目标数为 N=4。七节点逐格转录版得到
`rho(N=2..5)=1.00127..1.04087`；结果表校准版得到图中报告的
`1.00522..1.04432`。完整的逐图证据见
[docs/case_study_yangli.md](docs/case_study_yangli.md)。

示例图（`docs/figures/`）：四节点转移矩阵热力图/有向图、七节点族 rho 曲线。

## 开发路线

### Phase 1: Matrix Engine ✅

- [x] 基础矩阵表示（校验：方阵、有限、非负 A1）
- [x] 谱半径计算
- [x] 特征向量 / Perron 分析（归一化相对频率、不可约性、复根检测）
- [x] 矩阵族（N 依赖）与封顶系统
- [x] 矩阵可视化（heatmap / 有向图 / rho 曲线，matplotlib）

### Phase 2: Battle Simulator ⚠️（原型层，非 V1 结论）

- [x] 行动值系统（AV = 10000 / 速度，`SpeedBattleEngine`）
- [x] 能量系统接入角色数据（上限、阈值开大）
- [x] 技能点系统接入角色数据（上限、消耗/回复）
- [x] 追加攻击与插入行动（不消耗通常回合）
- [x] 敌方行动约束（行动值时钟，闭环须在敌方行动前完成）
- [x] 演示级技能/光锥/命座数据表与优先级编辑器（schema v2：
      `data/characters/*.json` + `docs/character_data_schema.md`；
      `PriorityEditor`/`priority_overrides` 运行时与队伍级编辑，
      CLI `--team` 一键模拟 + §8 断轴判定）

### Phase 3: Optimization（实验功能，V1 后续）

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

Python >= 3.10，依赖见 `requirements.txt`（numpy / matplotlib）。

推荐使用 `python -m src <示例>` 作为统一入口；`python main.py` 继续保留为
兼容入口。

```bash
python -m pytest tests/ -q
python tools/generate_theory_examples.py   # 重新生成文档案例（可复现）
python -m tools.generate_figures           # 从 V1 数据重新生成示意图
```
