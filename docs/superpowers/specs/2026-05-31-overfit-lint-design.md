# overfit-lint 设计文档

> 日期：2026-05-31
> 状态：已批准，进入实现
> 一句话：一个扫描量化策略**源码**、不运行它、自动标出「过拟合代码气味」的 Python 静态分析工具。

---

## 1. 背景与动机

绝大多数反过拟合工具是**数值型**的——Deflated Sharpe、PBO（CSCV）、walk-forward 等。它们检验的是**单个策略的样本内信息泄漏**。

但有一类过拟合，数值检验照不到，只在**代码本身**留下痕迹：

- 把网格搜索的轮次/锚点编码进参数名（`Q_R7_VIX78`、`best_v9_iter9`）；
- 精确到奇怪小数、无经济依据的阈值（`vix_rank<=0.78`、16 位小数权重）；
- 样本外期硬编码股票黑名单、或把某只历史赢家股写死成锚点；
- 排序后系统性挑**中段名次**（固定取第 3/第 6 名，跳过头部）；
- 把具体历史时段的目标收益/回撤写进「验收门槛」（FUNNEL 漏斗）；
- 在很短的数据窗口上堆叠大量自由参数与门控条件。

这些是「看着答案做题」的指纹。**overfit-lint 读代码、找这些指纹**，作为数值检验的**互补**手段——数值检验看样本内泄漏，本工具看逻辑与流程层的过拟合。

## 2. 目标 / 非目标

**目标（v0.1）**
- 对一份 Python 策略源文件做静态分析，报出过拟合「代码气味」。
- 低误报：每条规则都有正/负样例测试托底。
- 三种消费方式：人类可读文本报告、`--json`、CI 退出码。
- 每条 finding 附一句「为什么这是过拟合信号」的解释（教育价值）。

**非目标（v0.1）**
- 不运行策略、不做回测、不算净值（纯静态）。
- 不做数值反过拟合检验（DSR/PBO 等留给其他工具或后续模块）。
- 不保证「零漏报」——这是启发式 linter，定位是**提示风险**，不是裁决真伪。
- 不分析非 Python 源码。

## 3. 核心概念

- **Finding**：一条命中。字段：`rule_id`、`severity`（info/warning/critical）、`message`、`line`、`col`、`snippet`（出错代码片段）、`why`（原理解释）、`evidence`（结构化证据，如命中的字面量值）。
- **Severity**：`info` < `warning` < `critical`。
- **Smell score**：0–100 的「过拟合气味分」，按命中数与严重度加权（公式见 §7，公开透明，绝不自己用魔术数）。分数越高越可疑。

## 4. v0.1 检查规则（7 条）

| 规则 ID | 严重度 | 抓什么 | 启发式 | 误报防线 |
|---|---|---|---|---|
| `magic-thresholds` | info–critical | 异常精确、无经济依据的阈值常数；16 位小数权重 | 浮点字面量出现在比较运算或被赋给疑似阈值/权重的名字，且小数有效位 ≥3；严重度随精度上升 | 白名单常见值（0/0.5/1/5/10/20/100、常见 VIX 档 20/25/30…）；整数与「整洁」小数不报 |
| `param-encoded-name` | warning–critical | 标识符/字符串/文件名编码了搜索轮次或锚点 | 正则匹配 `R\d+`、`iter\d+`、`v\d+`、`cand(idate)?`、`champion`、`winner`、`best_`、`_final`、`vix\d{2,}`、`top1_reference` 等 | 仅当作为变量名/键名/字符串字面量出现；普通英文词（version 之外）不误伤 |
| `hardcoded-tickers` | warning–critical | 硬编码股票代码，尤其黑/白名单或被日期门控 | 检出由短全大写字符串（1–5 字母）构成的集合/列表；若变量名含 ban/block/exclude/blacklist，或附近有 OOS 日期字面量，则升级为 critical | 需 ≥2 个疑似 ticker 才成集合；常见全大写常量（如 `TODO`、`API`）排除 |
| `rank-position-pick` | warning–critical | 排序后系统性挑中段名次（跳过头部） | 检出排序/打分（`sort_values`/`argsort`/`nlargest`/`rank`）后做**固定非头部**位置选取：`iloc[n]`/下标 `[n]`（n≥2）、`rank==k`（k≥3）、`rank_start`/`rank_slot` 参数 ≥3、`argsort(...)[s:]`（s≥2） | 取 Top-1/Top-2、干净 Top-K（前 k 全取/轮动）**不报**；只报系统性跳过头部 |
| `excessive-params` | info–critical | 自由参数过多（自由度过高） | 统计模块级数值常量、函数默认数值参数、配置字典里的数值阈值条目；超阈值（默认 >15）告警，严重度随数量上升；可选 `--data-days N` 算「参数/数据」比并升级 | 仅计数值「旋钮」，跳过纯结构常量（如索引 0/1）；阈值可配 |
| `gate-stacking` | info–warning | 单条决策路径堆叠过多阈值门控 | 在一个函数/分支里统计「特征 与/或 常量」的阈值比较门控数量；超阈值（默认 >8）告警 | 跳过循环计数、断言等非门控比较；阈值可配 |
| `hardcoded-anchors` | warning–critical | 硬编码历史收益/回撤目标、FUNNEL 验收门槛 | 数值字面量（像收益率/回撤）赋给名字含 reference/target/anchor/funnel/kpi/min_return/must_exceed/expected 的变量或键，尤其与日期区间同现 | 需「业绩语义名字 + 业绩量级数值」同时满足；普通配置数值不报 |

> 实现顺序与难度：`magic-thresholds`、`param-encoded-name`、`hardcoded-tickers`、`hardcoded-anchors`、`excessive-params` 偏字面量/命名，较直接；`rank-position-pick`、`gate-stacking` 需要 AST 结构匹配，启发式保守 + 充分测试。

## 5. 架构与模块边界

```
overfitlint/
  __init__.py          # 版本号、公共 API 导出
  cli.py               # 命令行入口（argparse）
  config.py            # RuleConfig：启用/禁用、阈值、严重度覆盖
  core/
    finding.py         # Finding 数据类 + Severity 枚举
    context.py         # AnalysisContext：source、AST、行表、可选 data_days
    registry.py        # 规则注册表（装饰器 + 收集）
    rule.py            # Rule 基类（check(context)->list[Finding]）
    runner.py          # 解析一次 → 跑启用规则（隔离异常）→ 汇总
    report.py          # 文本 / JSON 渲染 + 评分
  rules/
    __init__.py        # 导入全部规则以触发注册
    magic_thresholds.py
    param_encoded_name.py
    hardcoded_tickers.py
    rank_position_pick.py
    excessive_params.py
    gate_stacking.py
    hardcoded_anchors.py
```

**边界原则**：每条规则是一个小而独立的单元，实现统一接口 `check(context) -> list[Finding]`，互不依赖。`runner` 不关心规则内部；`report` 不关心 finding 怎么产生。单条规则抛异常被 `runner` 捕获并降级为一条 `rule-error`，不连累整次分析。

## 6. CLI 与输出

```
overfit-lint PATH [PATH ...]
  --json                 输出 JSON（默认彩色文本）
  --fail-on LEVEL        命中 ≥LEVEL（info/warning/critical）则退出码 1（默认 warning）
  --data-days N          声明训练数据交易日数，启用「参数/数据」比检查
  --select RULES         只跑这些规则（逗号分隔）
  --ignore RULES         跳过这些规则
  --explain RULE         打印某规则的原理与样例，然后退出
  --version
（气味分始终在报告末尾打印；JSON 模式下作为 score 字段）
```

退出码：`0`=无达标命中；`1`=有 ≥`--fail-on` 的命中；`2`=用法/IO/解析错误。

## 7. 评分公式（透明）

```
score = min(100, round(100 * (1 - exp(-weighted/K))))
weighted = Σ severity_weight(finding)        # info=1, warning=3, critical=8
K = 12                                        # 归一化常数（文档写明，非隐藏旋钮）
```
单调饱和：命中越多越重，分越高，封顶 100；0 命中 = 0 分。常量在文档与 `--explain score` 中明示。

## 8. 错误处理

- 目标文件不存在/不可读 → 退出码 2 + 清晰信息。
- 非 `.py` 或语法错误 → 跳过该文件，报一条文件级错误，不崩溃，继续其余文件。
- 单条规则内部异常 → 捕获、记为 `rule-error`（severity=info），不影响别的规则。
- 空文件 / 无命中 → 「未发现过拟合气味」+ 分数 0，退出码 0。

## 9. 测试策略（TDD）

- 每条规则一个测试模块：正样例（该触发的脏片段）+ 负样例（干净片段不触发）。**先写测试，再写实现。**
- `tests/fixtures/` 放可复用的脏/干净代码片段。
- 集成测试：`examples/overfit_example.py`（合成脏策略，**不含用户真实策略代码**）断言命中预期规则集；`examples/clean_momentum.py` 断言近零命中。
- CLI 测试：退出码、`--json` 结构、`--fail-on`、`--explain`。
- CI：GitHub Actions，Python 3.10–3.13 矩阵跑 pytest。

## 10. 工程化

MIT LICENSE · `pyproject.toml`（PEP 621 元数据 + 控制台入口 `overfit-lint=overfitlint.cli:main`，零运行时依赖，仅标准库）· README（badge、检查清单、安装、quickstart、样例输出、评分说明、贡献指引）· `examples/` · `CONTRIBUTING.md` · `CHANGELOG.md` · `.gitignore`。

## 11. YAGNI / 后续路线

- v0.1 只做上述 7 条 + 单文件分析。不做：插件机制、配置文件加载、多语言、IDE 插件、自动修复。
- 后续可选：数值检验模块（DSR/PBO）、跨变体「幸存者偏差折扣」、`pyproject` 配置段、`# noqa: rule-id` 行内豁免、目录递归扫描的并行化。

## 12. 命名与发布

- 工作名 `overfit-lint`（包名 `overfit-lint`，导入名 `overfitlint`）。备选 `snooplint`/`curvelint`/`alpha-smell`。发布前查 PyPI/GitHub 重名。
- 仅封装**通用方法论**，不含任何私有策略源码或具体审查结论。
