# P21 · BoardUI 视觉层改造 · Before / After 对照

> 日期：2026-11-15　｜　范围：`boardlib/template.py`（仅样式）+ 生成产物
> 主人硬约束：**整体排版和结构不动**，只换 UI 组件/视觉层。

## 0. 结论与边界

BoardUI 是 React 19 + React Aria + Tailwind v4 的**源码分发**组件库（`.tsx`），本项目是 Python 生成单文件 HTML + 原生 JS、零构建。
因此不能「装组件库」，改为**移植它的设计系统**：语义令牌层 + 组件 CSS 配方。

| 层 | 处理 |
|---|---|
| 结构层 | **锁定**：三栏 IDE、10 视图、12 导航、32 条折叠规则、hash 路由、P18 抽屉、P19 雷达、P20 锚定链，DOM / JS 逻辑 / 数据 / 部署链零改动 |
| 组件样式层 | 收敛重复类 + 令牌化，改源头而非追加覆盖层 |
| 令牌层 | 新建 `--bui-*` 语义令牌，旧变量名保留为 alias |

> 更正：上一轮汇报说 BoardUI 是「9 档字阶」，核源码后实际是 **13 档**（Large Title 64 → Caption 2 11）。
> 本项目按中文密度区间取其中 **9 档**（9.5 / 10 / 11 / 12 / 13 / 14 / 16 / 19 / 26px），沿用它的「一档 = size + line-height + weight + tracking」复合结构，不照搬数值。

## 1. 参数对照

| 维度 | Before | After |
|---|---|---|
| 语义色 | 26 个裸 hex 变量，无语义分层 | 85 个 `--bui-*`（48 个已引用），表面/文字/描边/11 档暖铜 accent/状态色 |
| 字号 | **18 种**硬编码 px | **9 档**复合令牌，源码 `font-size:Npx` 归零 |
| 圆角 | **10 种**（1/2/3/4/5/6/8/10/16/999） | **4 档**（sm4 / md8 / lg10 / pill999），1–3px 柱条微几何保留 |
| 间距 | 硬编码 px | 4px 基准 8 档 `--bui-space-1..8`，`--sp/--pad` 已接入 |
| 动效 | CSS 4 档 + GSAP 6 档 | CSS 收敛到 **2 档**：`--bui-motion 150ms`（状态反馈）、`--bui-motion-panel 220ms`（抽屉/遮罩） |
| 数字 | `tabular-nums` 9 处，数字用 Consolas 等宽字体 | `body` 继承 `tabular-nums`；数字显示改回正文字体族（主人 2026-11-07 铁律），仅代码/时间戳保留 mono |
| 焦点态 | 仅 2 个元素有 | 全站单一 `focus-visible` 配方 + `--bui-focus-ring` |
| 阴影 | 全站 `none` | 卡片极浅接触阴影 + toast/抽屉面板阴影（dark 底不加发光） |
| 首屏密度 | `#stage-body` 1285.3px | **1248.6px（−36.7px，紧凑 2.9%）**，四组全部变短 |

## 2. 逐处改动清单（编号供单点微调）

| # | 名称 | Before | After |
|---|---|---|---|
| 01 | `:root` 令牌层 | 26 行裸 hex | 85 个 `--bui-*` + 旧变量 alias；DOM/JS 无需改 |
| 02 | accent 色 | 保留暖铜 `#C9A15E`（**拒绝 BoardUI 默认蓝**） | 扩成 11 档铜色 ramp，`--bui-accent-on` 替掉 4 处裸 `#1A1712` |
| 03 | 卡片圆角 | `--r:12px` | `--r:var(--bui-radius-lg)` = **10px** |
| 04 | 字号归一 | 285 处硬编码 px | 285 处 → `var(--bui-type-*)`；档位取各区间下界防折行 |
| 05 | 圆角归一 | 70 处硬编码 px | 70 处 → 4 档令牌 |
| 06 | 动效归一 | 38 处 `.15/.2/.22/.26/.3s` | 38 处 → 2 档令牌 |
| 07 | 数字等宽 | 9 处散落 | `body` 继承 + 10 处令牌引用 |
| 08 | 数字字体族 | `.num` / 指标数字用 Consolas | 改 `font-family:inherit`；`.code/.tl-time/.rd-time` 保留 mono |
| 09 | 左栏层级倒挂 | `.nav-gt` 10.5px / 400 / `--ink3` | 11px / 600 / `--bui-text-secondary` / `.08em` |
| 10 | 卡片标题层级 | `.tb-title` 13.5px | 14px / 600 / 20px 行高 / 主文字色（复合字阶 `t2`） |
| 11 | 三栏视觉权重 | 10 个视图所有卡片同一灰度 | 左栏导航面板 `--bui-bg-secondary`，与中栏主面板拉开 |
| 12 | 焦点环 | 只有 `.more-btn` / `.sd-close` | 全组件 `focus-visible` + 独立胶囊/关闭按钮 `--bui-focus-ring` |
| 13 | 阴影 | `--shadow:none`、卡片 `box-shadow:none` | 卡片 `var(--bui-shadow-card)`、toast `var(--bui-shadow-panel)` |
| 14 | 窄屏回调 | — | P21 层自带 `@media(max-width:760px)`，显式回写 card/tabs/datebtn/tb-tip/rd-title |

### 删除的 6 组纯死规则

| 位置 | 内容 | 判定 |
|---|---|---|
| 原 L53–55 | `#tab-*:checked` 旧 accent 版 | 被 P16 L426–428 同优先级覆盖 |
| 原 L389–391 | `#tab-*:checked` 蓝色版 | 同上，且颜色是错的 |
| 原 L51 | 重复 `.tabs label:last-child` | 与 L388 逐字相同 |
| 原 L47 | `.card` 首层定义 | 被 P16 L436 全量覆盖 |
| 原 L220 | `.view .card` 首层定义 | 同上 |
| 原 L261 | `.np-watch-t` 首层定义 | 被 L266 覆盖，`line-height:1.7` 已并入后者 |

> 其余「重复类」是 P16 刻意保留的覆盖层，删掉会回退到旧样式；**真正的单一真源在令牌层**——两层现在引用同一组取值。

## 3. 三个已拍板的取舍

1. **强调色**：保留暖铜，不采用 BoardUI 默认蓝（避开「深色底 + 靛蓝」AI 默认审美红线）。
2. **卡片圆角**：10px，不采用 BoardUI `rounded-3xl` 24px（24px 对交易看板偏软）。
3. **字阶数值**：保留 12/13px 中文密度基准，不抬到 BoardUI 正文 14px。

## 4. 验证结果

| 项 | 结果 |
|---|---|
| `py_compile` / `node --check` | PASS |
| `pytest` | **32 passed**（补采 11/13 缺失的市场广度后） |
| headless Edge 同源 iframe 探针 | **26/26 PASS** |
| 10 视图逐个切换 + 互斥 | PASS |
| P17 面板泄漏 / P18 抽屉 ESC / P19 雷达 / P20 窗口 | 全部回归 PASS |
| 桌面 1440px 无横向溢出 | PASS（1265/1265） |
| 393px iframe × 10 视图无横向溢出 | PASS |
| console 错误 | 0 |
| 密度量化 | `#stage-body` −36.7px，单行 −0.8px，涨停原因列 −1.0px |
| 截图目检 | 桌面 / 移动端首屏 / 移动端主内容区，无新增视觉问题 |

顺带修复：`breadth` 表缺 `20261113` 一行（11/13 自动跑数时乐咕限流），用 `stock_market_activity_legu()` 按统计日期校验后**真实补采**（涨 744 / 跌 4415 / 涨停 38），未伪造数据。

## 5. 已知保留项（非本次范围）

- GSAP 入场动画时长仍为原值（属 JS 动画预算，未动 JS）。
- 移动端「涨停原因」窄列折行、右侧「形态」列需卡片内横向滚动 —— 改造前后截图一致，属既有响应式行为。
- `--bui-*` 中 37 个为 ramp / 字阶配套档位，是设计系统的常规预留面，非死代码。

## 6. 截图

- 改造前桌面：`_p21_before_desktop.png`
- 改造后桌面：`_p21_final_desktop.png`
- 改造后移动端首屏：`_p21_final_mobile.png`
- 改造后移动端主内容：`_p21_final_mobile_main.png`
- 改造前移动端主内容：`_p21_before_mobile_main.png`

（存于 `D:\WorkBuddy_Work\效率工具\_p21_preview\`）

想单点微调：报上表编号即可，例如「09 改回淡一点」「03 回到 12px」。
