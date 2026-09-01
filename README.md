# HSR Infinite Cycle Calculator

只有一个程序文件 `calculator.py`。它负责计算任意非负方阵，也内置四个原图
复算案例。项目统一使用一种数学口径，不再混用行、列向量。

## 唯一口径

```text
x_(t+1) = x_t @ A
```

- `x_t` 是行向量；
- `A[i][j]` 表示事件 i 产生事件 j；
- `rho(A)` 是所有特征值绝对值的最大值；
- 主导比例 `p` 满足 `p @ A = rho(A) * p`。

代码通过计算 `A.T` 的右特征向量得到 `A` 的左特征向量 `p`。

## 文件

```text
calculator.py     唯一程序：计算器 + 四个案例
docs/screenshots/ 四张案例原图
requirements.txt  NumPy 依赖
README.md         使用说明
.gitignore        缓存忽略规则
```

## 计算矩阵

```bash
python calculator.py '[[0.5,0.2],[0.1,0.6]]'
```

输出：

```text
谱半径 = 0.70000000
状态 = 衰减
主导比例 = [0.3333333333333333, 0.6666666666666666]
```

判断规则：

- `rho < 1`：衰减；
- `rho ≈ 1`：临界；
- `rho > 1`：增长。

谱半径只描述线性模型，不足以单独证明实战永动。

## 复算案例

```bash
python calculator.py --cases
```

四节点顺序为 `H/H_U/T/T_U`，七节点顺序为
`H/H_U/C/M/C_U/T/T_U`。目标数 `N` 只进入矩阵最后一行的部分系数。

七节点原图显示 `T→C_U=1/4`，但结果表需要 `1/2` 才能复现。
`calibrated=False` 保存显示矩阵，`calibrated=True` 保存结果表口径。
