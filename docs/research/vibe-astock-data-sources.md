# Vibe-Astock 数据源完整溯源（2026-09-27 深挖）

> 来源：simonlin1212/Vibe-Astock 源码逐文件分析（fetchers.py / astock.py / pool_source.py / historical_sources.py / iwencai_client.py / newsradar.py / news_sources.json / probability.py / baostock_src.py / yahoo.py / watchtower.py）
> 结论先行：**全部是免费公开接口，唯一可选付费是问财 OpenAPI key**。akshare/mootdx/baostock 只是"壳"，底层全是东财/同花顺/腾讯 HTTP 接口 → Cloudflare Worker TS 几乎全能直调复刻。

## 一、盘面/盯盘（复盘主线）

| 数据 | 表层依赖 | 真实源 + 接口 | Worker 可用 |
|---|---|---|---|
| 大盘指数/个股实时行情 | 标准库 urllib | 腾讯 `https://qt.gtimg.cn/q=sh000001,...`（GBK 解码，`~` 分隔字段，60只/批） | ✅ |
| 涨停池/炸板池/跌停池 | akshare `stock_zt_pool_em/zbgc/dtgc` | 东财 push2ex `getTopicZTPool/ZBPool/DTPool`（ut=7eea3edc...） | ✅ 直调 HTTP |
| 昨日涨停今日表现 | akshare `stock_zt_pool_previous_em` | 东财 push2ex `getYesterdayZTPool` | ✅ |
| 板块资金流（行业t:2/概念t:3，今日f62+5日f164+10日f174） | requests | 东财 `https://push2delay.eastmoney.com/api/qt/clist/get`（ut=b2884a393a59ad64002292a3e90d46a5；push2 常被掐所以用 delay 镜像） | ✅ |
| 成交额 TOP20 | 同上 clist | fid=f6 降序，fs=沪深京全A | ✅ |
| 龙虎榜明细 | akshare `stock_lhb_detail_em` | 东财数据中心 datacenter-web `RPT_DAILYBILLBOARD_DETAILSNEW`；席位明细 `RPT_BILLBOARD_DAILYDETAILSBUY/SELL` | ✅ |
| 涨停原因（免费路径） | requests | **同花顺涨停揭秘** `https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool`（分页200×20，逐行核对 first_limit_up_time 防错场） | ✅ |
| 涨停原因（付费增强） | 问财 OpenAPI | `https://openapi.iwencai.com/v1/query2data`，Bearer key，查询"{日期}涨停的股票 涨停原因" | ✅ 需 key |
| 解禁日历/个股解禁 | 东财数据中心 | `RPT_LIFT_STAGE`（strict 模式：失败抛错不静默） | ✅ |
| 历史板块日线 | requests | 同花顺 `https://d.10jqka.com.cn/v4/line/bk_{code}/01/{year}.js`（JSONP 信封校验，不执行 JS） | ✅ |

## 二、个股研究页（vr/astock.py，五层数据源）

| 层 | 数据 | 接口 |
|---|---|---|
| L1 | 行情+PE/PB/市值/换手/量比 | 腾讯 qt.gtimg.cn（1个请求批量） |
| L2 | 研报列表+PDF | 东财 `reportapi.eastmoney.com/report/list` + `pdf.dfcfw.com/pdf/H3_{id}_1.pdf` |
| L2 | 公告 | 东财 `np-anotice-stock.eastmoney.com/api/security/ann` |
| L3/4 | 两融`RPTA_WEB_RZRQ_GGMX`/大宗`RPT_DATA_BLOCKTRADE`/股东户数`RPT_HOLDERNUMLATEST`/分红`RPT_SHAREBONUS_DET`/龙虎榜/解禁 | 东财数据中心 `datacenter-web.eastmoney.com/api/data/v1/get`（统一限流 em_get：全局锁+1s间隔+0.1-0.5s抖动） |
| L3/4 | 个股资金流120日 | `push2his.eastmoney.com/api/qt/stock/fflow/daykline/get` |
| L3/4 | 热门概念 | 东财 `emappdata.eastmoney.com/stockrank/getHotStockRankList`（POST） |
| L4 | 互动易问答 | 巨潮 `irm.cninfo.com.cn/newircs/index/queryKeyboardInfo`（两步：查orgId→拉问答） |
| L5 | 一致预期EPS/财务摘要 | akshare→同花顺 `stock_profit_forecast_ths` / `stock_financial_abstract_ths` |
| L5 | 估值分位（PE/PB 历史分位+p20/p50/p80） | akshare→百度股市通 `stock_zh_valuation_baidu` |
| — | K线（日/周/月/60分钟） | mootdx 通达信 TCP 协议 → **Worker 不可用**（替代：东财 push2his kline） |

## 三、资讯雷达（零 key）

- 12 赛道 × **108 个纯 RSS 源**（news_sources.json），标准库 urllib + 40 线程池，按赛道分组时间倒序
- 中文源：量子位/智东西/机器之心+新智元（wechat2rss 转换）/36氪/钛媒体/IT之家/虎嗅/华尔街见闻/东财 RSS/经济观察网
- 英文：OpenAI/DeepMind/HF/arXiv、SemiAnalysis/EE Times、FT/WSJ/CNBC/SEC/美联储、Yahoo Finance
- 合规红线过滤：赌博/加密/预测市场/色情关键词（连 polymarket/kalshi 都在过滤词里）

## 四、事件概率（宏观对冲视角）

- **Kalshi**：`https://api.elections.kalshi.com/trade-api/v2/events` + `/series`（零鉴权，cursor 翻页，宏观系列按 category=Economics/Financials 定向取 CPI/FOMC/衰退等）
- **Polymarket**：`https://gamma-api.polymarket.com/markets` + `/tags`（零鉴权，offset 分页，tag 定向取宏观）
- 实测坑（作者注释）：Kalshi 量字段必须带 `_fp` 后缀；Polymarket 排序参数是 `volume24hr` 无下划线（官方文档写错，用文档参数会 422）；`/events` 上传 category 被忽略
- 原始响应逐字节落盘留证（raw_ref），每条合约带采集时间戳

## 五、回测历史数据

- **A股**：baostock（证券宝，SDK/TCP 零鉴权）：日K/估值历史（peTTM/pbMRQ等）/标的信息 + **纯计算筹码分布 CYQ**（三角分布+换手衰减，300格网格，出获利比例/90%成本区间/集中度）→ Worker 不可用（TCP），K线可换东财 push2his
- **美股/港股**：Yahoo `query2.finance.yahoo.com/v8/finance/chart/{sym}`（零crumb）+ quoteSummary（分析师预期/机构持仓/财报/评级变动/期权链/新闻搜索）

## 六、实时动态（watchtower）

- 腾讯行情 3 秒/轮（交易时段），非交易时段 20 秒；标的池=持仓+自选(≤300)+市值≥500亿大票+昨日梯队+成交前十
- 急拉急跌：180 秒观察窗 ±1.5%，至少积累 60 秒；封板/开板：价格 vs zt_price（兼容北交所 30cm）状态翻转
- 冷却去重 300 秒/票/类型；事件按日落盘 jsonl

## 七、可直接"走私"进 ashare-board 的 Top 5（Worker 亲和度排序）

1. **同花顺涨停揭秘接口**（涨停原因+封板时间，免费，✅HTTP）→ 补齐短线归因
2. **东财涨停池三件套 HTTP 直调**（替代 akshare 依赖）→ 晋级率/昨日梯队
3. **东财数据中心 12 个 reportName**（龙虎榜席位/两融/解禁/股东户数，✅HTTP）→ 中长线+价值指标扩展
4. **限流+日期校验+错误披露三纪律**（em_get 模式/龙虎榜日期核对/降级不静默）→ 推送质量
5. **108 RSS 新闻源清单**（json 直接抄）→ Worker cron 每日聚合推送

## 八、Worker 不可用项及替代

| 不可用 | 原因 | 替代 |
|---|---|---|
| mootdx K线 | TCP 通达信协议 | 东财 push2his `api/qt/stock/kline/get` 或腾讯 |
| baostock 筹码分布 | TCP SDK | 自算：腾讯/东财日K + 换手率 → 同款三角分布算法可移植 |
| 问财 OpenAPI | 需付费 key | 同花顺涨停揭秘免费路径 |
| Yahoo（国内视角） | 国内访问不稳 | Worker 出网在海外，反而顺畅 |
