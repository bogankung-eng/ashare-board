# P22 · 米白纸感主题 + 组件形态重做 · Before / After 对照

> 日期：2026-11-15　｜　范围：`boardlib/template.py`（仅样式）+ 生成产物
> 主人选择：**A 米白纸感** + **换色并重做组件形态** + 右上角深浅切换
> 硬约束（延续 P21）：**整体排版和结构不动** —— 三栏 IDE、10 视图、12 导航、32 条折叠规则、hash 路由、P18 抽屉、P19 雷达、P20 锚定链，DOM / 渲染 JS / 数据 / 部署链零改动。

## 0. 结论与边界

P21 换的是「零件制造标准」（语义令牌、字阶、圆角、动效），**没换色系**，所以主人反馈「跟原来差不多、偏黑暗」。
P22 换的是「表面与形态」这一层：默认主题改为米白纸感，深色主题完整保留为可切换项。

| 层 | 处理 |
|---|---|
| 结构层 | **锁定**：一个 DOM 节点都没增删改（除新增一个按钮） |
| 数据层 | 零改动，`pytest 32 passed` |
| 渲染 JS | 零改动，5 段内联脚本 `node --check` 全过 |
| 令牌层 | `:root` 默认浅色；新增 `:root[data-theme="dark"]` 回退到 P21 深色 |
| 组件形态层 | 新增 P22 层，作用域 `:root:not([data-theme="dark"])`，**深色主题像素级保持 P21** |

> 关键设计：形态层只在浅色生效，所以深色不是「近似还原」而是**完全不经过新规则**，避免任何深色回归。

## 1. 色板对照（Before = P21 深色 / After = P22 默认）

| 语义令牌 | Before（深色） | After（米白纸感） |
|---|---|---|
| 页底 `--bui-bg-full` | `#13161A` | **`#FAF9F6`** 纸感米白 |
| 卡片 `--bui-bg-primary` | `#1B1F25` | **`#FFFFFF`** 纯白 |
| 次级面 `--bui-bg-secondary` | `#22272E` | `#F4F2EC` |
| 三级面 `--bui-bg-tertiary` | `#2A3038` | `#EAE7DF` |
| hover `--bui-bg-hover` | `#252A31` | `#EFEDE6` |
| 主文字 | `#E9EBEE` | `#1F1F1F` |
| 次文字 | `#B2B8C1` | `#5E6066` |
| 三级文字 | `#8A929C` | `#787A80` |
| 描边 | `rgba(255,255,255,.075)` | `#E4E1D9` |
| 控件描边 | `rgba(255,255,255,.13)` | `#D3CFC5` |
| 强调 `--bui-accent-500` | `#C9A15E` | **`#A9782F`** 加深暖铜（浅底保对比） |
| 强调文字 `--bui-accent-300` | `#E0BE86` | **`#8A6326`** |
| 强调反色 `--bui-accent-on` | `#1A1712` | `#FFFFFF` |
| 涨 / 跌 | `#D9605A` / `#3E9E78` | **`#BE3B32`** / **`#187A52`**（红涨绿跌不变） |
| 信息 / 紫 | `#7FA8C4` / `#9A8FC4` | `#2A6C90` / `#6A5CA6` |
| 卡片阴影 | `0 1px 1px rgba(0,0,0,.14)` | `0 1px 2px rgba(40,36,26,.07)` |

> 色值沿用主人在三套候选里选定的 A（预览稿 `_p21_theme_preview.py`），未擅自调色。

## 2. 组件形态 Before / After（这是「重做形态」的实质）

| # | 部件 | Before | After |
|---|---|---|---|
| 01 | 顶栏 | 深色/灰色实心圆角块，与卡片同形 | **去盒化**：纸底直出、仅留一条底部分隔线，标题像文档标题 |
| 02 | 卡片 | 灰面 + 细描边，与页底几乎同色 | 纯白浮起 + `#E4E1D9` 描边 + 极浅接触阴影 |
| 03 | 左栏导航 | 与主卡片同色灰块 | 退一档到 `--bui-bg-full` 米白，形成三级视觉权重 |
| 04 | 选中态（tab / 日期） | **实心琥珀块** | 浅铜底 + 铜描边 + 深铜字，强调色面积压到 5% 以下 |
| 05 | 分组条 `.grp-head` | 满宽彩色横条 | 透明底 + 3px 左竖线（红/铜/蓝按层级），章节标题感 |
| 06 | 徽章 / 标签 | 4–8px 方角 | **胶囊** `999px`，文字短不折行 |
| 07 | 表头 / 斑马纹 | 深灰表头、无斑马 | 浅米表头 + `rgba(30,28,22,.025)` 极浅斑马 |
| 08 | 行 hover | 深色下曾整块提亮（P16 修过） | 只微变暗到 `--bui-bg-hover` + 主文字加黑，绝不提亮 |
| 09 | 抽屉遮罩 / 面板阴影 | `rgba(8,10,13,.60)` / 纯黑阴影 | `rgba(35,32,26,.38)` / 暖褐阴影，跟纸感一致 |
| 10 | 表单控件 | 强制 `color-scheme:dark` | 浅色下回 `light`，下拉不再是深色原生控件 |

## 3. 逐处改动清单（编号供单点微调）

| # | 名称 | 位置 | 说明 |
|---|---|---|---|
| 01 | `:root` 色板 | `template.py` 11–40 | 换成 A 米白纸感；accent ramp 仅 300/500/alpha/on 被全站引用，其余为语义占位 |
| 02 | 阴影令牌 | `template.py` | 纸感接触阴影，去掉深色发光感 |
| 03 | `:root[data-theme="dark"]` | `:root` 之后 | P21 深色 18 个颜色/阴影令牌完整回退 |
| 04 | P22 形态令牌 | `:root` 末尾 | `--bui-nav-bg / --bui-badge-radius / --bui-sel-* / --bui-band-bg / --bui-zebra / --bui-mask / --bui-panel-shadow` |
| 05 | 防闪屏初始化 | `<head>` 最前 | 读 `localStorage['board-theme']`，默认 `light`，先设 `data-theme` 再解析 CSS |
| 06 | 切换按钮 | `<body> .wrap` 内 | 1.5px 线性 SVG 太阳/月亮，浅色显示太阳、深色显示月亮 |
| 07 | 切换脚本 | 按钮后 | `absolute` 定位、不占布局流；写 localStorage；`aria-label` / `title` 同步 |
| 08 | `.wrap{position:relative}` | P22 层 | 按钮定位参照；不改三栏宽度 |
| 09 | `.topbar{padding-right}` | P22 层 + 760px 回调 | 唯一布局例外：给按钮留 56px（窄屏 42px），不影响响应式结构 |
| 10 | 形态层 1–7 | `</style>` 前 | 只写 background / border / color / box-shadow / border-radius |
| 11 | 裸色补丁 | 形态层后 | 接回深色时代写死的淡粉/淡蓝/淡金文字 |
| 12 | 徽章排除项 | 形态 5 | 所有选择器带 `:not(.grp-head)`，见「踩坑」 |
| 13 | 窄屏回调 | P22 层末尾 | 按钮 30px、`padding-right:42px`、卡片 `overflow-x:auto`（P16 铁律） |
| 14 | 产物同步 | `board.html` / `public/index.html` | 由 `_gen_board.py` 重新生成后复制 |

## 4. 裸色补丁清单（浅底下会消失的历史硬编码）

| 原色 | 出现处 | 接回 |
|---|---|---|
| `#f5f1ea` / `#a89c8e` / `#c6bba9` | `h1` / `.sub` / `.datebtn` | `--bui-text-primary` / `--bui-text-secondary` |
| `#E9938E` / `#E2554F` / `#f0a8a2` / `#F0B4B0` | `.t-lb4` / `.g-lb5` / `.g-lb7` / `.kw` / `.tag-danger` / `.st-danger` / `.sq-gap` | `--bui-status-up` |
| `#E8A23A` / `#D8B27C` / `#F0D3A4` | `.t-lb3` / `.g-lb3` / `.co-link:hover` | `--bui-accent-300` |
| `#5FA8CC` / `#9CC0D6` | `.t-lb2` / `.g-lb2` | `--bui-info` |
| `#8a8f98` | `.t-lb1` | `--bui-text-secondary` |
| `#1f2430` | `.temp-marker` | `--bui-text-primary` |
| `#fff` | `.t-lb5` / `.t-lb7` | 保留（深红底白字，语义正确） |

> 注：`.temp-track` 的蓝→绿→红渐变、`rgba(...,.4)` 系列半透明标签描边在浅底上对比仍足够，**刻意保留**，避免过度收拾把信息洗白。

## 5. 深浅切换

- 默认 `light`（主人要的米白），`data-theme` 由 head 脚本在任何 CSS 解析前写入 → 无闪屏。
- 右上角圆形按钮，点击在 `light ⇄ dark` 间切换，写 `localStorage['board-theme']`；两个图标由 CSS 按 `data-theme` 显隐。
- 按钮 `position:absolute`（相对 `.wrap`），滚动时随页面走，不会长期悬浮遮挡右栏；`z-index:80` 低于 toast(99) / 抽屉(900/901)。
- 深色主题形态层完全不生效，P21 的实心琥珀选中态、深灰卡片、满宽分组色块**全部原样保留**。

## 6. 验证结果

| 项 | 结果 |
|---|---|
| `python -m py_compile` | OK |
| `node --check` × 5 段内联 JS | 全过 |
| `pytest tests/ -q` | **32 passed** |
| headless Edge 同源 iframe 探针 | **35 PASS / 0 FAIL** |
| 默认主题 / 页底色 | `light` / `rgb(250,249,246)` |
| 切换 + localStorage + 回切 | 全过；深色页底 `rgb(19,22,26)`、顶栏 `rgb(27,31,37)` |
| P17 面板泄漏回归 | `.panel-trend` / `.panel-value` 仍 `display:none` |
| P18 抽屉 | 点击 `.js-stk` → `#sd-wrap` 加 `on` |
| P19 雷达 / P20 锚定链 | 两视图 DOM 内容均渲染 |
| 折叠引擎 | 14 个「查看更多」小胶囊正常 |
| 393px 移动端 | `innerWidth=393`、`scrollWidth=378`、按钮在界内、topbar 无裁切 |
| 分组条一致性 | 4 个 `.grp-head` 全部 `radius=0px` + 透明底 |
| 截图目检 | 浅/深桌面、锚定链、雷达、移动端首屏 + 中栏，共 6 张 |

## 7. 踩坑记录（写进项目铁律）

1. **`.grp-head` 也带 `g-lb*` 颜色类**：徽章胶囊化规则与 `.grp-head` 形态规则特异性同为 `(0,3,0)`，「后写赢」把分组标题盖成 `999px` 胶囊，且不同分组形状不一致。修复 = 徽章选择器统一加 `:not(.grp-head)`，并用探针逐条量 `borderRadius` 兜底。
   → **通用教训：给全站某类元素加形态时，先查这个类是否同时被用作容器类。**
2. **主 JS 包在 IIFE 里**（`template.py` 1251 行 `(function () { "use strict"; ... })()`），`renderRadar` / `renderAnchor` / `applyFolds` / `openStock` 都不挂 `window`。探针若用 `typeof iframe.contentWindow.xxx` 会全部误判为 FAIL。
   → 验证必须走**真实点击 / DOM 内容 / 计算样式**，不能查函数引用。
3. **headless 移动端截图**：`--window-size=393` 实际被 Chrome 抬到 ~500px，iframe harness 会在右侧留白。精确 393px 用固定宽 iframe + probe 读 `innerWidth/scrollWidth`；展示用截图改用 500px 直接截，画面更干净。

## 8. 还没动的事（按优先级）

1. `cycle` 空壳视图（`renderCycle()` 死代码、`#cycle-card` 容器不存在）。
2. 消息面（P19 雷达）与盘面锚定链（P20）联动。
3. 个股深研抽屉（P18）补研报 / 公告 / 互动易。
4. 地域强度 / 地域发酵预测（缺 `code → 省份` 映射地基）。
5. GSAP 动画时长仍与 CSS 两档动效不统一（P21 未收敛）。
