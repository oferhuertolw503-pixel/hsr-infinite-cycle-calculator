# HSR Infinite Cycle Calculator

一个简单的资源转移矩阵计算器。当前版本只做两件事：

1. 计算非负方阵的谱半径和主导特征向量；
2. 验证四张案例截图中的计算结果。

## 文件结构

```text
src/
  calculator.py   核心计算
  cases.py        四个验证案例
  __main__.py     命令行入口
tests/
  test_calculator.py
docs/screenshots/ 四张案例原图
```

## 安装和运行

```bash
pip install -r requirements.txt
python -m src
```

最后显示 `结论：全部通过` 即表示四个案例复算成功。

## 计算自己的矩阵

新建 `matrix.json`：

```json
{
  "name": "我的矩阵",
  "matrix": [
    [0.5, 0.2],
    [0.1, 0.6]
  ]
}
```

运行：

```bash
python -m src matrix.json
```

判断口径：

- `rho < 1`：衰减；
- `rho ≈ 1`：临界；
- `rho > 1`：存在线性增长方向，但不能单独证明游戏实战永动。

## 四个验证案例

| 截图 | 验证内容 |
|---|---|
| `case_4node_decay.png` | 四节点无击杀回能，`rho=0.88353` |
| `case_4node_kill.png` | 四节点击杀回能，`rho=1.02442`，并核对特征向量 |
| `case_matrix_definition.png` | 七节点矩阵逐格转录，`T→C_U=1/4` |
| `case_7node_matrix.png` | 结果表的 `rho(N=2..5)` |

七节点原图本身有一处矛盾：矩阵显示 `T→C_U=1/4`，结果表需要
`T→C_U=1/2` 才能复现。代码在 `src/cases.py` 中明确保留这两个口径。

## 测试

```bash
python -m pytest -q
```

角色数据库、战斗模拟、队伍搜索和自动优化不属于当前版本。
