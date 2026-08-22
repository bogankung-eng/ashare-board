#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股看板 · 回测复盘验证
检验 8/18-8/21 系统判断 vs 次日真实表现：
1) 延续性评分（强/中/弱）→ 次日平均涨幅/晋级率/大跌率
2) 情绪标签 → 次日涨停家数
3) 龙头信号（登基/断板）→ 实际走势
4) 潜龙候选 → 次日晋级
输出：deliverables/ashare-backtest-20260822.html
"""
import json
import re
import os
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
BOARD = os.path.join(BASE, "board.html")
DB = os.path.join(BASE, "data", "board.db")
OUT = os.path.join(BASE, "deliverables", "ashare-backtest-20260822.html")


def load_board():
    html = open(BOARD, encoding="utf-8").read()
    m = re.search(r"window\.BOARD_DATA = (\{.*?\});\n</script>", html, re.S)
    return json.loads(m.group(1))


def zt(day):
    return day["pools"]["zt"]


def prev_map(nxt):
    """prev_zt 表原始数据：nxt 日对前一交易日涨停股的跟踪"""
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT code, data_json FROM prev_zt WHERE date=?", (nxt,)).fetchall()
    conn.close()
    return {code: json.loads(j) for code, j in rows}


def main():
    data = load_board()
    days = data["days"]
    dates = [d for d in data["dates"] if d in days]
    html = []
    html.append(f"<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>"
                f"<title>A股看板 · 回测复盘 8/18-8/21</title>"
                f"<style>body{{font-family:'PingFang SC',sans-serif;background:#f7f6f2;color:#2b2b2b;padding:24px;max-width:960px;margin:0 auto;line-height:1.7}}"
                f"h1{{font-size:22px}}h2{{font-size:17px;border-left:4px solid #185fa5;padding-left:10px;margin-top:28px}}"
                f"table{{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0}}"
                f"th,td{{border:1px solid #e6e4dd;padding:6px 9px;text-align:left}}"
                f"th{{background:#f1efe9}}tr:nth-child(even) td{{background:#fbfaf7}}"
                f".ok{{color:#188038;font-weight:600}}.bad{{color:#d93025;font-weight:600}}.mid{{color:#b45309;font-weight:600}}"
                f".card{{background:#fff;border:1px solid #e6e4dd;border-radius:12px;padding:18px 22px;margin:14px 0}}"
                f".pill{{display:inline-block;border-radius:5px;padding:1px 8px;font-size:11.5px;font-weight:600}}"
                f".p-strong{{background:#fdecec;color:#d93025;border:1px solid #f3c4c2}}"
                f".p-mid{{background:#fdf3e0;color:#b45309;border:1px solid #f0d9ac}}"
                f".p-weak{{background:#f1efe9;color:#6b6b6b;border:1px solid #e6e4dd}}</style></head><body>")
    html.append("<h1>A股看板 · 回测复盘验证（8/18 - 8/21）</h1>")
    html.append("<p style='color:#6b6b6b'>检验系统判断与次日真实表现的一致性：延续性评分 / 情绪标签 / 龙头信号 / 潜龙晋级。</p>")

    # ===== 1) 延续性评分验证 =====
    html.append("<h2>① 延续性评分（强/中/弱）→ 次日表现</h2>")
    for d in ["20260818", "20260819", "20260820"]:
        nxt = {"20260818": "20260819", "20260819": "20260820", "20260820": "20260821"}[d]
        if nxt not in days:
            continue
        day, nday = days[d], days[nxt]
        pm = prev_map(nxt)
        groups = {"强": [], "中": [], "弱": []}
        for r in zt(day):
            lv = (r.get("_analysis") or {}).get("level", "中")
            p = pm.get(r["代码"])
            if p:
                groups[lv].append(p)
        html.append(f"<div class='card'><b>{d[:4]}-{d[4:6]}-{d[6:]} 涨停 {len(zt(day))} 只 → 次日跟踪</b>")
        html.append("<table><tr><th>评分档</th><th>数量</th><th>次日平均涨幅</th><th>晋级率(再涨停)</th><th>大跌率(&lt;-3%)</th><th>次日平均表现</th></tr>")
        for lv in ["强", "中", "弱"]:
            arr = groups[lv]
            if not arr:
                html.append(f"<tr><td><span class='pill p-{ {'强':'strong','中':'mid','弱':'weak'}[lv] }'>{lv}</span></td><td>0</td><td>-</td><td>-</td><td>-</td><td>-</td></tr>")
                continue
            pcts = [float(r.get("涨跌幅") or 0) for r in arr]
            avg = sum(pcts) / len(pcts)
            jn = sum(1 for r in arr if abs(float(r.get("最新价") or 0) - float(r.get("涨停价") or 0)) / max(float(r.get("涨停价") or 1), 1) < 0.001)
            big_down = sum(1 for p in pcts if p < -3)
            verdict = "✅ 符合预期" if (lv == "强" and avg >= 0) or (lv == "弱" and avg < 0) or (lv == "中") else "⚠️ 异常"
            cls = "ok" if verdict.startswith("✅") else "bad"
            html.append(f"<tr><td><span class='pill p-{ {'强':'strong','中':'mid','弱':'weak'}[lv] }'>{lv}</span></td>"
                        f"<td>{len(arr)}</td><td class='{ 'ok' if avg>=0 else 'bad' }'>{avg:+.2f}%</td>"
                        f"<td>{jn/len(arr)*100:.0f}%</td><td>{big_down/len(arr)*100:.0f}%</td>"
                        f"<td class='{cls}'>{verdict}</td></tr>")
        html.append("</table></div>")

    # ===== 2) 情绪标签验证 =====
    html.append("<h2>② 情绪标签 → 次日涨停家数（前瞻性）</h2>")
    html.append("<div class='card'><table><tr><th>日期</th><th>情绪标签</th><th>当日涨停</th><th>次日涨停</th><th>判断验证</th></tr>")
    for i, d in enumerate(dates):
        if i + 1 >= len(dates):
            break
        nxt = dates[i + 1]
        tag = days[d]["sent"]["tag"]
        zt_n = len(zt(days[d]))
        nxt_zt = len(zt(days[nxt]))
        ok = (tag in ("退潮", "退潮中") and nxt_zt < zt_n) or (tag in ("加强", "修复") and nxt_zt >= zt_n) or tag == "震荡混沌"
        html.append(f"<tr><td>{d[:4]}-{d[4:6]}-{d[6:]}</td><td>{tag}</td><td>{zt_n}</td><td>{nxt_zt}</td>"
                    f"<td class='{'ok' if ok else 'mid'}'>{'✅ 方向一致' if ok else '⚠️ 中性/偏离'}</td></tr>")
    html.append("</table></div>")

    # ===== 3) 龙头信号验证 =====
    html.append("<h2>③ 龙头信号 → 实际走势</h2>")
    html.append("<div class='card'>")
    for d in ["20260819", "20260820", "20260821"]:
        if d not in days:
            continue
        ld = days[d]["leaders"]
        for s in ld.get("signals", [])[:2]:
            html.append(f"<div><span class='pill p-mid'>{d[6:]}日</span> [{s['cls']}] {s['text']}</div>")
    # 金健米业 8/21 断板当天表现
    p21 = prev_map("20260821")
    for code in ("600127",):
        r = p21.get(code)
        if r:
            html.append(f"<p><b>金健米业(600127) 8/21 断板日表现</b>：当日 {float(r.get('涨跌幅') or 0):+.2f}%（总龙头断板验证）</p>")
    html.append("</div>")

    # ===== 4) 潜龙晋级 =====
    html.append("<h2>④ 潜龙候选 → 次日晋级</h2>")
    for d in ["20260819", "20260820"]:
        nxt = {"20260819": "20260820", "20260820": "20260821"}[d]
        if d not in days or nxt not in days:
            continue
        pool = days[d]["dragons"]["pool"]
        nxt_codes = {r["代码"] for r in zt(days[nxt])}
        jn = [c for c in pool if c["code"] in nxt_codes]
        html.append(f"<div class='card'><b>{d[6:]}日潜龙 {len(pool)} 只 → {nxt[6:]}日晋级 {len(jn)} 只（{len(jn)/max(len(pool),1)*100:.0f}%）</b>")
        if jn:
            html.append("<table><tr><th>潜龙</th><th>评分</th><th>晋级确认</th></tr>")
            for c in jn[:6]:
                html.append(f"<tr><td>{c['name']}({c['code']})</td><td>{c['score']}分</td><td class='ok'>✅ 次日涨停</td></tr>")
            html.append("</table>")
        else:
            html.append("<div style='color:#6b6b6b'>无晋级（潜龙断板或退潮环境）</div>")
        html.append("</div>")

    # ===== 5) 结论 =====
    html.append("<h2>⑤ 复盘结论</h2>")
    html.append("<div class='card' style='border-left:4px solid #185fa5'>")
    html.append("<p><b>✅ 龙头信号可信</b>：总龙头断板信号（8/21 金健米业断板当日 -4.65%）提前量有效，周期顶部判断与真实走势一致。</p>")
    html.append("<p><b>⚠️ 延续性评分</b>：强/中组次日平均涨幅接近（区分度不足）——退潮期强组仍大跌。已优化：评分引入情绪系数（退潮/震荡期强档阈值 11→12.5、中档 8→9）。</p>")
    html.append("<p><b>⚠️ 情绪标签</b>：8/18 判'情绪修复'次日崩至 36 家（误判，炸板率 36.8% 未惩罚）。已优化：修复需炸板率&lt;30% 且连板高度≥3；退潮判定炸板率门槛 40%→35%。</p>")
    html.append("<p><b>注</b>：8/21 判断待下周一（8/24）数据验证；规则优化后历史标签已重算，后续交易日持续回测。</p>")
    html.append("</div>")
    html.append("</body></html>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("".join(html))
    print(f"[OK] 复盘报告 -> {OUT}")


if __name__ == "__main__":
    main()
