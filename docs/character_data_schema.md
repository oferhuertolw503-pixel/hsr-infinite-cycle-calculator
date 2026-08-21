# 角色数据 Schema v2（游戏侧数据录入）

本文档描述 `data/characters/*.json` 的 v2 格式,以及 `SpeedBattleEngine`
的动作优先级语义与编辑方式。数据只录入模拟器实际消费的字段;
数值以游戏内为准,演示条目须在 `notes` 标注来源。

## 顶层字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` / `name` | str | 至少其一;`name` 同时是队伍/优先级覆盖中的单位名 |
| `path` / `element` / `rarity` | — | 背景信息,模拟器不消费 |
| `speed` | number > 0 | AV = 10000/速度(§1.1) |
| `max_energy` | number > 0 | 能量上限与终结技阈值(§5.1/§5.2),默认 120 |
| `skills` | list | v2 技能表(见下) |
| `events` | dict/list | **旧格式**,继续兼容;`unit_from_character_data` 两种都接受 |
| `light_cone` | object | 光锥(名称+效果列表) |
| `eidolons` | list | 已启用命座(rank 1..6 + 效果列表) |
| `notes` | str | 数据来源/演示声明 |

## skills 条目

| 字段 | 说明 |
|---|---|
| `name` | 唯一;也是优先级编辑的键 |
| `type` | `basic` / `skill` / `ultimate` / `talent` / `technique`(校验用) |
| `energy_gain` | 该行动的回能 |
| `energy_cost` | > 0 时表示终结技(阈值行动,引擎在能量满时自动插入) |
| `skill_points` | 正数回点、负数耗点 |
| `priority` | number,越小越先;缺省为声明顺序 |
| `inserted` | true 表示插入行动(追击/额外回合,不消耗通常回合,§1.1) |
| `trigger` | 触发说明(如 `weakness_break`、`energy_full`),文档字段 |

校验规则(`validate_character` / `load_character_validated`):
`energy_cost` 与 `energy_gain` 不得同时出现(终结技走阈值语义);
speed/max_energy 必须为正;技能名不得重复。

## light_cone / eidolons 效果

两种来源共用同一套声明式效果,加载时按顺序应用:

| kind | 参数 | 语义 |
|---|---|---|
| `speed_delta` | `value` | 速度加值(下限 1) |
| `initial_energy` | `value` | 开局能量(封顶于 max_energy) |
| `energy_regen_percent` | `value`,`action_types?` | 回能加成;`action_types` 缺省作用于全部行动 |
| `grant_action` | `action` | 追加一个 ActionSpec(默认 `inserted: true`) |

## 优先级语义与编辑

引擎选择规则(§5.3 可执行动作集):在**可执行**的通常行动中取
`priority` 最小者,平局按声明顺序。`enabled: false` 的行动不可执行。

两种编辑途径:

1. **数据文件内**:skills 直接写 `priority`;
2. **队伍文件覆盖**(`priority_overrides`)或运行时 `PriorityEditor`
   (`src/simulation/priority.py`):`set_priority` / `reorder` /
   `enable` / `disable`,`to_overrides()` 序列化为 JSON,
   `apply_priority_overrides(units, overrides)` 应用——队伍文件可在
   不改动角色表的情况下重排轴:

```json
{
  "characters": ["data/characters/himeko.json", "..."],
  "enemy_speed": 96,
  "priority_overrides": {
    "姬子": {"skill": {"enabled": false}, "basic_attack": 1}
  },
  "simulation": {"turns": 300, "initial_skill_points": 3}
}
```

`python main.py examples/team_simulation_demo.json --team` 会打印
生效的优先级表、模拟结果与 §8 断轴判定(资源/触发/时序)。

## 现有数据表

| 文件 | 说明 |
|---|---|
| `himeko.json` | 姬子,由旧 events 升级;含光锥回能演示 |
| `march7th_hunt.json` | 三月七·巡猎,由旧 events 升级;含 E1 速度演示 |
| `tribbie.json` | 缇宝演示骨架(七节点模型 T/T_U 对应) |
| `luocha.json` | 罗刹演示骨架(field 回点;四节点截图对应) |

> 所有条目的回能/耗点数值为演示量级,正式使用前应按游戏内数值
> 逐项核对(§7 逐边填表原则同样适用于技能数据)。
