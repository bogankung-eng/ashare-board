# -*- coding: utf-8 -*-
"""看板 HTML/CSS/JS 模板（P11b 拆分，逐字节搬运，勿手改——改完必须跑等价性验证）。"""

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A股短线看板 · 涨停接力复盘</title>
<style>
  :root{
    /* P16 · Graphite Ledger：中性石墨底 + 单一暖铜强调；语义色只用于数据，不用于装饰 */
    --page:#13161A; --surface:#1B1F25; --surface-2:#22272E; --surface-3:#2A3038;
    --card:var(--surface); --panel-2:var(--surface-2); --toolbar:#171B20; --toolbar-line:rgba(255,255,255,.09);
    --ink:#E9EBEE; --ink2:#B2B8C1; --ink3:#8A929C;
    --line:rgba(255,255,255,.075); --line-2:rgba(255,255,255,.13); --border:var(--line); --hover:rgba(255,255,255,.055);
    --up:#D9605A; --upbg:rgba(217,96,90,.13); --down:#3E9E78; --downbg:rgba(62,158,120,.13);
    --red:var(--up); --redbg:var(--upbg); --green:var(--down); --greenbg:var(--downbg);
    --blue:#7FA8C4; --bluebg:rgba(127,168,196,.13);
    --amber:#C9A15E; --amberbg:rgba(201,161,94,.13);
    --purple:#9A8FC4; --purplebg:rgba(154,143,196,.13);
    --accent:#C9A15E; --accent-strong:#E0BE86; --accent-soft:rgba(201,161,94,.14);
    --shadow:none; --r:12px; --r-sm:8px; --sp:16px; --pad:16px 18px;
    --font-ui:"PingFang SC","Microsoft YaHei",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
    --font-mono:Consolas,"SF Mono","Roboto Mono",monospace;
  }
  *{box-sizing:border-box; margin:0; padding:0;}
  body{background:var(--page); color:var(--ink); font-family:var(--font-ui); line-height:1.6; font-size:13px; -webkit-font-smoothing:antialiased;}
  input,select,button,textarea{color-scheme:dark; font-family:inherit;}
  .wrap{max-width:1360px; margin:0 auto; padding:20px 20px 48px;}
  .shell{background:transparent; border:none; border-radius:0; padding:0; box-shadow:none; position:relative;}
    .cu-row{display:flex;align-items:center;gap:7px;flex-wrap:wrap;padding:7px 0;border-bottom:1px dashed var(--line);}
  .cu-tag{font-size:10px;border-radius:4px;padding:1px 7px;background:var(--panel-2);color:var(--ink2);flex:none;}
  .cu-wave{background:var(--amberbg);color:var(--amber);font-weight:600;}
  .cu-lb{color:var(--up);font-size:11px;}
  .cu-ind{color:var(--ink3);font-size:11px;}
  .cu-arrow{color:var(--accent);font-weight:700;}
  .cu-link{font-style:normal;font-size:10px;color:var(--accent);background:var(--accent-soft);border-radius:3px;padding:0 4px;}
  #h-toast{display:none;position:fixed;right:16px;bottom:16px;background:var(--toolbar);color:var(--ink);border:1px solid var(--toolbar-line);border-radius:8px;padding:9px 14px;font-size:12.5px;z-index:99;}
.topbar{display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:14px; background:var(--toolbar); border:none; border-radius:var(--r-sm); padding:11px 18px; box-shadow:var(--shadow);}
  h1{font-size:16.5px; font-weight:600; color:#f5f1ea; letter-spacing:-.01em;}
  .sub{color:#a89c8e; font-size:12px;}
  .datebar{display:flex; gap:4px; flex-wrap:wrap;}
  .datebtn{border:1px solid var(--toolbar-line); background:transparent; border-radius:var(--r-sm); padding:4px 12px; font-size:12.5px; cursor:pointer; color:#c6bba9;}
  .datebtn:hover{color:#fff; border-color:#5a5142;}
  .datebtn.active{background:var(--accent); color:#fff; border-color:var(--accent); font-weight:600;}
  .card{background:var(--card); border:1px solid var(--border); border-radius:var(--r); padding:15px 17px; margin-bottom:12px; box-shadow:var(--shadow);}
  .tabs-wrap{margin-bottom:14px;}
  .tabs{display:flex; gap:0; border:1px solid var(--border); border-radius:var(--r-sm); overflow:hidden; background:var(--panel-2); width:fit-content;}
  .tabs label{padding:8px 20px; font-size:13px; cursor:pointer; color:var(--ink2); border-right:1px solid var(--border); background:transparent;}
  .tabs label:last-child{border-right:none;}
  .tabs label:hover{color:var(--accent); background:var(--panel-2);}
  #tab-short:checked ~ .tabs label[for="tab-short"],
  #tab-trend:checked ~ .tabs label[for="tab-trend"],
  #tab-value:checked ~ .tabs label[for="tab-value"]{background:var(--accent); color:#fff; border-color:var(--accent);}
  .sent-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(100px,1fr)); gap:8px;}
  .sent-item{border:1px solid var(--line); border-radius:6px; padding:8px 10px; background:var(--card); text-align:center;}
  .sent-item .label{font-size:11.5px; color:var(--ink2);}
  .sent-item .value{font-size:19px; font-weight:600; margin-top:1px;}
  .sent-item .subv{font-size:11.5px; color:var(--ink3); margin-top:2px;}
  .tag-big{font-size:15px; font-weight:600; padding:2px 12px; border-radius:8px; display:inline-block;}
  .tag-good{background:var(--upbg); color:var(--up); border:1px solid rgba(226,85,79,.4);}
  .tag-danger{background:rgba(226,85,79,.16); color:#f0a8a2; border:1px solid rgba(226,85,79,.45);}
  .tag-warn{background:var(--amberbg); color:var(--amber); border:1px solid rgba(232,162,58,.4);}
  .tag-flat{background:var(--panel-2); color:var(--ink2); border:1px solid var(--line);}
  .filters{display:flex; gap:10px; flex-wrap:wrap; align-items:flex-end;}
  .f-item{display:flex; flex-direction:column; gap:4px;}
  .f-item label{font-size:11.5px; color:var(--ink2);}
  .f-item select,.f-item input{border:1px solid var(--line); border-radius:8px; padding:6px 10px; font-size:13px; background:var(--card); color:var(--ink);}
  .f-item input{width:72px;}
  .ind-tags{display:flex; flex-wrap:wrap; gap:6px; margin-top:8px;}
  .ind-tag{border:1px solid var(--line); background:var(--card); border-radius:16px; padding:3px 12px; font-size:12px; cursor:pointer; color:var(--ink2); user-select:none;}
  .ind-tag.on{background:var(--bluebg); color:var(--blue); border-color:rgba(95,168,204,.4); font-weight:600;}
  .btn{border:1px solid var(--line); background:var(--card); border-radius:8px; padding:6px 14px; font-size:13px; cursor:pointer; color:var(--ink2);}
  .btn:hover{border-color:var(--ink3);}
  .grp{margin-bottom:16px;}
  .grp-head{display:flex; align-items:center; gap:10px; margin-bottom:8px; padding:8px 12px; border-radius:10px; font-weight:600; font-size:14px;}
  .grp-head .cnt{font-size:12px; font-weight:400; color:var(--ink2);}
  .g-lb4{background:var(--purplebg); color:var(--purple); border:1px solid rgba(155,142,242,.4);}
  .g-lb3{background:var(--upbg); color:var(--up); border:1px solid rgba(226,85,79,.4);}
  .g-lb2{background:var(--amberbg); color:var(--amber); border:1px solid rgba(232,162,58,.4);}
  .g-lb1{background:var(--panel-2); color:var(--ink2); border:1px solid var(--line);}
  table{width:100%; border-collapse:collapse; font-size:12px;}
  th{background:var(--panel-2); text-align:left; padding:6px 9px; border:1px solid var(--line); font-weight:600; white-space:nowrap; color:var(--ink2); font-size:11.5px;}
  td{padding:5px 9px; border:1px solid var(--line); white-space:nowrap; font-size:12px;}
  tr:nth-child(even) td{background:var(--panel-2);}
  tr:hover td{background:var(--hover); color:var(--ink);}
  .up{color:var(--up); font-weight:600;}
  .down{color:var(--down); font-weight:600;}
  .num{font-family:Consolas,"SF Mono",monospace; text-align:right; font-variant-numeric:tabular-nums;}
  .code{color:var(--ink2); font-family:Consolas,monospace;}
  .pill{display:inline-block; font-size:11px; border-radius:5px; padding:0 6px;}
  .pill-zt{background:var(--upbg); color:var(--up); border:1px solid rgba(226,85,79,.4);}
  .pill-zb{background:var(--amberbg); color:var(--amber); border:1px solid rgba(232,162,58,.4);}
  .pill-lv{border-radius:6px; padding:1px 8px; font-size:11.5px; font-weight:600;}
  .lv-strong{background:var(--upbg); color:var(--up); border:1px solid rgba(226,85,79,.4);}
  .lv-mid{background:var(--amberbg); color:var(--amber); border:1px solid rgba(232,162,58,.4);}
  .lv-weak{background:var(--panel-2); color:var(--ink2); border:1px solid var(--line);}
  .theme-grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:10px;}
  .theme-card{border:1px solid var(--line); border-radius:8px; padding:11px 14px; background:var(--card);}
  .theme-card .tname{font-weight:600; font-size:14px;}
  .theme-card .tmeta{font-size:12px; color:var(--ink2); margin-top:4px; line-height:1.8;}
  .stage-tag{border-radius:5px; padding:1px 7px; font-size:11px; font-weight:600;}
  .st-good{background:var(--upbg); color:var(--up); border:1px solid rgba(226,85,79,.4);}
  .st-warn{background:var(--amberbg); color:var(--amber); border:1px solid rgba(232,162,58,.4);}
  .st-danger{background:rgba(226,85,79,.16); color:#f0a8a2; border:1px solid rgba(226,85,79,.45);}
  .st-flat{background:var(--panel-2); color:var(--ink2); border:1px solid var(--line);}
  .hl-tag{border-radius:5px; padding:1px 7px; font-size:11px; font-weight:600; margin-left:6px;}
  .hl-good{background:var(--bluebg); color:var(--blue); border:1px solid rgba(95,168,204,.4);}
  .hl-warn{background:var(--amberbg); color:var(--amber); border:1px solid rgba(232,162,58,.4);}
  .hl-card{background:var(--bluebg); border:1px solid rgba(95,168,204,.4); border-radius:8px; padding:12px 16px; margin-top:12px; font-size:13px;}
  .hl-card b{color:var(--blue);}
  .empty{color:var(--ink3); text-align:center; padding:30px 0;}
  .foot{margin-top:20px; font-size:11.5px; color:var(--ink3); text-align:center;}
  .disclaimer{background:var(--panel-2); border:1px solid var(--line); border-radius:8px; padding:10px 14px; font-size:12px; color:var(--ink2); margin-top:12px;}
  .lv-tip{cursor:help; border-bottom:1px dashed var(--ink3);}
  .sub-grid{display:grid; grid-template-columns:1fr 1fr; gap:14px;}
  @media (max-width:900px){.sub-grid{grid-template-columns:1fr;}}
  .sub-box{border:1px solid var(--line); border-radius:8px; padding:12px 14px; background:var(--card);}
  .sub-box h4{font-size:13.5px; margin-bottom:8px; color:var(--ink);}
  .lhb-row{display:flex; align-items:center; gap:8px; padding:5px 0; border-bottom:1px dashed var(--line); font-size:12.5px;}
  .lhb-row:last-child{border-bottom:none;}
  .lhb-row .nm{flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}
  .lhb-row .amt{font-family:Consolas,monospace; font-weight:600;}
  .money-in{color:var(--up);}
  .money-out{color:var(--down);}
  .focus-tag{background:var(--purplebg); color:var(--purple); border:1px solid rgba(155,142,242,.4); border-radius:5px; font-size:10.5px; padding:0 5px;}
  .attr-pill{border-radius:5px; padding:1px 7px; font-size:11px; font-weight:600; margin-right:2px;}
  .at-topic{background:var(--bluebg); color:var(--blue); border:1px solid rgba(95,168,204,.4);}
  .at-money{background:var(--redbg); color:var(--red); border:1px solid rgba(226,85,79,.4);}
  .at-tech{background:var(--greenbg); color:var(--green); border:1px solid rgba(47,174,118,.4);}
  .at-msg{background:var(--amberbg); color:var(--amber); border:1px solid rgba(232,162,58,.4);}
  .seat-tag{border-radius:5px; padding:1px 7px; font-size:10.5px; font-weight:600; margin-left:4px;}
  .seat-hot{background:var(--redbg); color:var(--red); border:1px solid rgba(226,85,79,.4);}
  .seat-org{background:var(--bluebg); color:var(--blue); border:1px solid rgba(95,168,204,.4);}
  .seat-quant{background:var(--amberbg); color:var(--amber); border:1px solid rgba(232,162,58,.4);}
  .seat-ret{background:var(--panel-2); color:var(--ink2); border:1px solid var(--line);}
  .seat-oth{background:var(--panel-2); color:var(--ink2); border:1px solid var(--line);}
  .leader-badge{border-radius:6px; padding:2px 10px; font-size:12px; font-weight:600; margin-right:6px;}
  .lb-total{background:var(--purplebg); color:var(--purple); border:1px solid rgba(155,142,242,.4);}
  .lb-emo{background:var(--redbg); color:var(--red); border:1px solid rgba(226,85,79,.4);}
  @media (max-width:760px){
    .wrap{padding:12px 8px 60px;}
    .hero{padding:16px 14px;}
    .card{padding:14px 12px; overflow-x:auto;}
    .topbar{flex-direction:column; align-items:flex-start; gap:8px;}
    h1{font-size:19px;}
    .sub{font-size:12.5px;}
    .datebar{flex-wrap:wrap;}
    .tabs{gap:0; margin-bottom:12px; width:100%;}
    .tabs label{padding:7px 0; font-size:13px; flex:1; text-align:center; min-width:0;}
    .filters{gap:8px;}
    .f-item{flex:1 1 44%;}
    .idx-grid{grid-template-columns:repeat(auto-fill,minmax(138px,1fr)); gap:8px;}
    .theme-grid{grid-template-columns:1fr;}
    .sub-grid,.two-col{grid-template-columns:1fr; gap:10px;}
    table{font-size:12px;}
    th,td{padding:5px 6px;}
    .lhb-row{flex-wrap:wrap;}
  }
  .desk-grid{display:grid; grid-template-columns:1fr; gap:14px;}
  .desk-grid .col{display:flex; flex-direction:column; gap:14px;}
  .desk-grid .card{margin-bottom:0;}
  @media (min-width:1024px){
    .desk-grid{grid-template-columns:200px 1.4fr 1fr; align-items:start;}
    .desk-grid .col-nav,.desk-grid .col-side{position:sticky;top:14px;max-height:calc(100vh - 28px);overflow-y:auto;scrollbar-width:thin;}
  }
  .nav-card{padding:14px 0 12px;}
  .brand{text-align:center;font-size:14px;font-weight:600;color:#fff;background:var(--blue);margin:-14px -1px 0 -1px;padding:10px;border-radius:0;}
  .brand-sub{text-align:center;font-size:11.5px;color:var(--ink3);margin:6px 0 10px;padding:0 10px;}
  .mod-btn{display:flex;align-items:center;gap:8px;padding:8px 12px;margin:2px 6px;font-size:12.5px;cursor:pointer;color:var(--ink2);border-radius:6px;border:1px solid transparent;background:transparent;}
  .mod-btn:hover{background:var(--panel-2);color:var(--ink);}
  .nav-gt{font-size:11px;color:var(--ink3);letter-spacing:1.5px;padding:8px 12px 3px;cursor:pointer;user-select:none;display:flex;align-items:center;gap:5px;}
  .nav-caret{display:inline-block;font-size:9px;}
  .nav-group.fold .mod-btn.sub{display:none;}
  .nav-group.fold .nav-caret{transform:rotate(-90deg);}
  .mod-btn.sub{padding-left:24px;}
  .mod-btn.active{background:var(--accent-soft);color:var(--accent);border-color:rgba(232,131,58,.4);font-weight:600;}
  .mod-btn .ic{font-size:14px;width:16px;text-align:center;color:var(--ink3);}
  .mod-btn.active .ic{color:var(--accent);}
  .mod-sep{height:1px;background:var(--line);margin:8px 12px;}
  .toolbar{display:flex;align-items:center;justify-content:space-between;padding:6px 0 10px;border-bottom:1px solid var(--line);margin-bottom:12px;flex-wrap:wrap;gap:6px;}
  .tb-title{font-size:14px;font-weight:600;}
  .tb-title .cnt{font-weight:400;color:var(--ink2);font-size:12px;margin-left:6px;}
  .tb-tip{font-size:11.5px;color:var(--ink3);}
  .lb-tag{font-size:11.5px;font-weight:600;padding:1px 8px;border-radius:5px;margin-right:6px;}
  .t-lb7{background:rgba(226,85,79,.16);color:#fff;}
  .t-lb5{background:#E2554F;color:#fff;}
  .t-lb4{background:rgba(226,85,79,.15);color:#E2554F;border:1px solid rgba(226,85,79,.4);}
  .t-lb3{background:rgba(232,162,58,.12);color:#E8A23A;border:1px solid rgba(232,162,58,.4);}
  .t-lb2{background:rgba(95,168,204,.12);color:#5FA8CC;border:1px solid rgba(95,168,204,.4);}
  .t-lb1{background:var(--panel-2);color:#8a8f98;border:1px solid rgba(255,255,255,.15);}
  .g-lb7{background:rgba(217,96,90,.20);color:#F0B4B0;border:1px solid rgba(217,96,90,.42);}
  .g-lb5{background:rgba(217,96,90,.16);color:#E9938E;border:1px solid rgba(217,96,90,.38);}
  .g-lb4{background:rgba(201,161,94,.13);color:var(--accent-strong);border:1px solid rgba(201,161,94,.32);}
  .g-lb3{background:rgba(201,161,94,.11);color:#D8B27C;border:1px solid rgba(201,161,94,.28);}
  .g-lb2{background:rgba(127,168,196,.11);color:#9CC0D6;border:1px solid rgba(127,168,196,.28);}
  .g-lb1{background:var(--surface-2);color:var(--ink2);border:1px solid var(--line);}
  .metric-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:12px;}
  .metric-card{border:1px solid var(--line);border-radius:6px;padding:10px;background:var(--card);text-align:center;}
  .metric-card .lab{font-size:11.5px;color:var(--ink2);}
  .metric-card .val{font-size:18px;font-weight:600;margin-top:2px;font-family:Consolas,monospace;font-variant-numeric:tabular-nums;letter-spacing:-.01em;}
  .core-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:12px;}
  .core-cell{border:1px solid var(--line);border-radius:6px;padding:8px;background:var(--card);text-align:center;}
  .core-cell .lab{font-size:11px;color:var(--ink2);}
  .core-cell .val{font-size:17px;font-weight:600;margin-top:1px;font-family:Consolas,monospace;font-variant-numeric:tabular-nums;}
  .temp-bar{margin:8px 0 4px;}
  .temp-track{position:relative;height:8px;background:linear-gradient(90deg,#5FA8CC 0%,#2FAE76 50%,#E2554F 100%);border-radius:4px;margin:6px 0;}
  .temp-fill{height:100%;background:rgba(255,255,255,0.4);border-radius:4px;}
  .temp-marker{position:absolute;top:-4px;width:4px;height:16px;background:#1f2430;border-radius:2px;transform:translateX(-50%);}
  .temp-labels{display:flex;justify-content:space-between;font-size:10px;color:var(--ink3);padding:2px 0;}
  .sq-gap{font-size:11.5px;border-left:3px solid var(--amber);background:var(--amberbg);color:var(--amber);padding:5px 9px;border-radius:5px;margin-bottom:8px;line-height:1.5;}
  .sq-gap.sq-break{border-left-color:var(--up);background:var(--upbg);color:var(--up);font-weight:600;}
.risk-line{display:flex;justify-content:space-between;align-items:center;padding:6px 4px;margin-top:6px;background:var(--panel-2);border-radius:6px;font-size:11px;color:var(--ink2);}
  .tone-tag{display:inline-block;font-size:15px;font-weight:600;padding:4px 14px;border-radius:8px;margin-bottom:8px;}
  .prev-row{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px dashed var(--line);font-size:12.5px;}
  .prev-row:last-child{border-bottom:none;}
  .theme-row,.dragon-row{padding:6px 0;border-bottom:1px dashed var(--line);font-size:12.5px;display:flex;align-items:center;gap:6px;flex-wrap:wrap;}
  .theme-row:last-child,.dragon-row:last-child{border-bottom:none;}
  .view .card{padding:14px 16px;}
  .scr-tabs{display:flex;gap:0;border:1px solid var(--line);border-radius:6px;overflow:hidden;}
  .scr-btn{border:none;background:var(--card);padding:5px 16px;font-size:12.5px;cursor:pointer;color:var(--ink2);border-right:1px solid var(--line);}
  .scr-btn:last-child{border-right:none;}
  .scr-btn:hover{background:var(--panel-2);}
  .scr-btn.active{background:var(--accent);color:#fff;font-weight:600;}
  .scr-note{font-size:11.5px;color:var(--ink3);background:var(--panel-2);border:1px solid var(--line);border-radius:6px;padding:6px 10px;margin-bottom:10px;line-height:1.6;}
  .scr-score{color:var(--blue);font-size:13px;}
  .d-up{color:var(--up);font-weight:600;}
  .d-dn{color:var(--down);font-weight:600;}
  .d-flat{color:var(--ink2);}
  .d-none{color:var(--ink3);}
  .d-base{font-size:10px;color:var(--ink3);margin-left:2px;}
  .co-link{color:var(--accent);font-weight:600;text-decoration:none;border-bottom:1px dashed var(--accent);}
  .co-link:hover{background:var(--accent-soft);}
  .q-up{color:var(--up);font-weight:600;font-size:11px;}
  .q-dn{color:var(--down);font-weight:600;font-size:11px;}
  .q-flat{color:var(--ink3);font-size:11px;}
  .q-na{color:var(--ink3);font-size:11px;}
  .c-up{color:var(--up);}
  .foc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:10px;}
  .foc-card{border:1px solid var(--line);border-left:2px solid var(--accent);border-radius:var(--r-sm);padding:12px 14px;background:var(--surface-2);}
  .foc-head{display:flex;align-items:center;gap:8px;font-size:15px;margin-bottom:6px;flex-wrap:wrap;}
  .foc-tag{font-size:10px;background:var(--accent);color:#fff;border-radius:4px;padding:1px 6px;}
  .foc-lb{font-size:11px;color:var(--up);font-weight:700;}
  .foc-reason{font-size:12.5px;color:var(--ink2);line-height:1.55;}
  .foc-date{font-size:10.5px;color:var(--ink3);margin-top:6px;}
  .np-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:12px;}
  .np-card{border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:var(--panel-2);transition:border-color .15s;}
  .np-card:hover{border-color:rgba(232,131,58,.45);}
  .np-card-h{display:flex;align-items:baseline;gap:7px;margin-bottom:9px;}
  .np-big{font-size:26px;font-weight:800;color:var(--accent);line-height:1;}
  .np-big-sub{font-size:11px;color:var(--ink3);}
  .np-stats2{margin-left:auto;display:flex;gap:10px;font-size:11px;color:var(--ink3);align-items:baseline;flex-wrap:wrap;}
  .np-stats2 b{font-size:13px;}
  .np-hot{color:var(--up);font-weight:700;}
  .np-mems{display:flex;flex-wrap:wrap;gap:5px;}
  .np-mem{font-size:12px;padding:2px 8px;border-radius:6px;background:var(--card);border:1px solid var(--line);}
  .np-mem a{color:var(--ink);}
  .np-mem-hi{background:var(--upbg);border-color:rgba(226,85,79,.35);}
  .np-mem-hi a{color:var(--up);font-weight:600;}
  .np-watch-t{font-size:11.5px;color:var(--ink3);margin-top:12px;line-height:1.7;}
  .np-watch-t b{color:var(--ink2);}
  .chip{display:inline-flex;align-items:center;gap:4px;border:1px solid var(--line);border-radius:999px;padding:2px 9px;font-size:12px;background:var(--card);}
  .chip-zt{border-color:rgba(226,85,79,.5);background:var(--upbg);}
  .chip-lb{color:var(--up);font-size:10px;}
  .np-watch-t{font-size:11px;color:var(--ink3);margin:10px 0 0;font-weight:600;}
  .np-empty{font-size:12.5px;color:var(--ink3);padding:8px 0;}
  .tlp-group{margin-bottom:14px;}
  .tlp-group:last-child{margin-bottom:0;}
  .tlp-head{font-size:14px;font-weight:700;margin-bottom:6px;display:flex;gap:8px;align-items:center;}
  .tlp-type{font-size:10px;border-radius:4px;padding:1px 6px;background:var(--bluebg);color:var(--blue);}
  .tlp-zt{font-size:10.5px;color:var(--up);font-weight:700;}
  .tlp-sub{display:flex;gap:10px;padding:7px 0;border-top:1px dashed var(--line);align-items:flex-start;}
  .tlp-subname{min-width:118px;font-size:12.5px;font-weight:600;color:var(--ink2);}
  .tlp-subzt{color:var(--up);font-size:10.5px;margin-left:4px;}
  .tlp-chips{display:flex;flex-wrap:wrap;gap:6px;}
  .tlp-sec{margin-bottom:14px;}
  .tlp-sec-t{display:block;font-size:11.5px;font-weight:700;color:var(--ink3);margin-bottom:7px;letter-spacing:1px;}
  .tlp-node{background:var(--amberbg);border-left:3px solid var(--accent);border-radius:6px;padding:8px 12px;margin-bottom:6px;font-size:12.5px;line-height:1.7;color:var(--ink2);}
  .tlp-node-t{font-weight:700;color:var(--accent);margin-right:4px;}
  .tlp-node-lb{color:var(--up);font-weight:700;}
  .tlp-node-arrow{color:var(--accent);font-weight:700;}
  .tlp-node-ind{color:var(--ink3);font-size:11.5px;}
  .tlp-inds{display:flex;flex-wrap:wrap;gap:6px;}
  .tlp-ind-t{color:var(--accent);font-weight:700;}
  .tlp-inds i{font-style:normal;color:var(--ink3);font-size:11px;}
  .tev-wrap{max-height:420px;overflow-y:auto;border-left:2px solid var(--line);padding-left:10px;}
  .tev{display:flex;align-items:center;gap:7px;padding:3px 0;font-size:12.5px;position:relative;}
  .tev-t{color:var(--ink3);font-size:11px;min-width:34px;font-variant-numeric:tabular-nums;}
  .tev-dot{width:7px;height:7px;border-radius:50%;flex:none;}
  .tev-up{background:var(--up);box-shadow:0 0 0 2px var(--upbg);}
  .tev-zb{background:var(--amber);box-shadow:0 0 0 2px var(--amberbg);}
  .tev-lb{color:var(--up);font-size:11px;}
  .tev-ind{color:var(--ink3);font-size:11px;}
  .tev-r{color:var(--ink2);font-size:11.5px;}
  .tev-turn{color:var(--amber);font-size:11px;}
  .tev-blow{color:#fff;background:var(--up);border-radius:4px;padding:0 5px;font-size:10.5px;font-weight:700;}
  .tev-zbtag{color:var(--amber);font-size:11px;font-weight:600;}
  .tlp-pnode{display:inline-block;border-radius:6px;padding:4px 10px;margin:0 6px 6px 0;font-size:12px;background:var(--card);border:1px solid var(--line);}
  .tlp-n-high{background:var(--upbg);border-color:rgba(226,85,79,.4);color:var(--up);font-weight:600;}
  .tlp-n-break{background:var(--downbg);border-color:rgba(47,174,118,.4);color:var(--down);font-weight:600;}
  .tlp-n-ice{background:var(--bluebg);color:var(--blue);}
  .tlp-n-hot{background:var(--amberbg);border-color:rgba(232,162,58,.4);color:var(--amber);font-weight:600;}
  .tlp-days{display:flex;gap:6px;overflow-x:auto;padding-bottom:4px;}
  .tlp-day{flex:none;width:86px;border:1px solid var(--line);border-radius:var(--r-sm);padding:8px 10px;display:flex;flex-direction:column;gap:3px;}
  .tlp-day b{font-size:11.5px;}
  .tlp-d-zt{font-size:16px;font-weight:800;}
  .tlp-d-sub{font-size:10.5px;color:var(--ink3);}
  .tlp-d-hot{background:var(--upbg);border-color:rgba(226,85,79,.35);}
  .tlp-d-hot .tlp-d-zt{color:var(--up);}
  .tlp-d-cold{background:var(--downbg);}
  .tlp-d-cold .tlp-d-zt{color:var(--down);}
  .tlp-d-mid{background:var(--card);}
  .tlp-d-mid .tlp-d-zt{color:var(--ink);}
  .tlp-matrix{overflow-x:auto;}
  .tlp-matrix table{border-collapse:collapse;font-size:11.5px;min-width:100%;}
  .tlp-matrix th,.tlp-matrix td{border:1px solid var(--line);padding:4px 7px;text-align:center;white-space:nowrap;}
  .tlp-matrix th{color:var(--ink3);font-weight:600;font-size:10.5px;}
  .tlp-m-ind{text-align:left;font-weight:600;color:var(--ink2);}
  .tlp-m-hi{background:var(--upbg);color:var(--up);font-weight:700;}
  .tlp-m-lo{background:var(--amberbg);}
  .tlp-m-sum{font-weight:700;color:var(--ink);}
  @media (max-width:720px){
    .np-row{grid-template-columns:64px 1fr;grid-template-areas:"ch st" "mem mem";}
    .np-char{grid-area:ch;}
    .np-stats{grid-area:st;}
    .np-members{grid-area:mem;}
    .tlp-sub{flex-direction:column;gap:6px;}
    .tlp-subname{min-width:0;}
  }
  .news-cats{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;}
  .cat-btn{border:1px solid var(--border);background:var(--panel-2);border-radius:999px;padding:4px 14px;font-size:12.5px;cursor:pointer;color:var(--ink2);}
  .cat-btn:hover{border-color:var(--accent);color:var(--accent);}
  .cat-btn.active{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600;}
  .cat-btn .n{font-size:11px;opacity:.75;margin-left:2px;}
  .tl{position:relative;padding-left:18px;}
  .tl::before{content:"";position:absolute;left:4px;top:6px;bottom:6px;width:1px;background:var(--border);}
  .tl-item{position:relative;padding:0 0 14px 0;margin-bottom:12px;border-bottom:1px dashed var(--border);}
  .tl-item:last-child{border-bottom:none;margin-bottom:0;}
  .tl-item::before{content:"";position:absolute;left:-17px;top:5px;width:7px;height:7px;border-radius:50%;background:var(--accent);}
  .tl-time{font-size:11px;color:var(--ink3);font-family:Consolas,monospace;margin-bottom:3px;display:flex;align-items:center;gap:8px;}
  .tl-src{font-size:10px;background:var(--panel-2);border-radius:4px;padding:0 6px;color:var(--ink3);}
  .tl-title{font-size:13.5px;font-weight:600;color:var(--ink);text-decoration:none;line-height:1.5;display:block;}
  .tl-title:hover{color:var(--accent);}
  .tl-sum{font-size:12px;color:var(--ink2);line-height:1.65;margin-top:4px;}
  .kw{color:var(--up);font-weight:700;font-style:normal;background:var(--upbg);border-radius:3px;padding:0 2px;}
  .ana{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:7px;padding:6px 10px;border-radius:8px;font-size:11.5px;background:var(--panel-2);}
  .ana.pos .ana-tag{background:var(--upbg);color:var(--up);border:1px solid rgba(226,85,79,.4);}
  .ana.neg .ana-tag{background:var(--downbg);color:var(--down);border:1px solid rgba(47,174,118,.4);}
  .ana.neu .ana-tag{background:var(--panel-2);color:var(--ink3);border:1px solid var(--border);}
  .ana-tag{font-weight:600;padding:1px 8px;border-radius:5px;font-size:11px;}
  .ana-why{color:var(--ink2);flex:1;min-width:180px;}
  .ana-cat{color:var(--ink3);font-size:10.5px;border:1px solid var(--border);border-radius:4px;padding:0 6px;}
  @media (max-width:1023px){
    .col-nav{order:1;} .col-main{order:2;} .col-side{order:3;}
    .metric-grid{grid-template-columns:repeat(3,1fr);}
    .core-grid{grid-template-columns:repeat(3,1fr);}
  }
  .cycle-wrap{display:flex; align-items:stretch; gap:5px; padding-top:6px;}
  .cycle-day{flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; gap:3px; min-width:0;}
  .c-bars{display:flex; align-items:flex-end; gap:2px; height:74px; width:100%; justify-content:center;}
  .c-bar{border-radius:3px 3px 0 0; min-height:3px;}
  .c-bar.zt{background:var(--red); width:42%;}
  .c-bar.dt{background:var(--green); width:42%;}
  .c-maxlb{font-size:12px; color:var(--ink2); font-weight:600;}
  .c-tag{font-size:10px; padding:0 5px; border-radius:4px; line-height:1.5;}
  .c-tag.tag-danger{background:var(--redbg); color:var(--red);}
  .c-tag.tag-good{background:var(--greenbg); color:var(--green);}
  .c-tag.tag-warn{background:var(--amberbg); color:var(--amber);}
  .c-tag.tag-flat{background:var(--panel-2); color:var(--ink2);}
  .c-label{font-size:10px; color:var(--ink3);}
  .cycle-day.cycle-cur .c-maxlb{color:var(--red);}
  .cycle-day.cycle-cur .c-label{color:var(--red); font-weight:600;}
  .cycle-hint{font-size:11.5px; color:var(--ink3); margin-top:6px;}
  .prev-stats{display:flex; gap:10px; flex-wrap:wrap; margin-bottom:10px;}
  .prev-stat{border:1px solid var(--line); border-radius:8px; padding:8px 16px; background:var(--card); text-align:center; min-width:90px;}
  .prev-stat .v{font-size:18px; font-weight:600;}
  .prev-stat .l{font-size:11px; color:var(--ink2);}
  .two-col{display:grid; grid-template-columns:1fr 1fr; gap:14px;}
  @media (max-width:900px){.two-col{grid-template-columns:1fr;}}
  .mini-list{border:1px solid var(--line); border-radius:8px; padding:8px 10px; background:var(--card); font-size:12px;}
  .mini-list .row{padding:3px 0; border-bottom:1px dashed var(--line); display:flex; gap:6px; align-items:center;}
  .mini-list .row:last-child{border-bottom:none;}
  .mini-list .c{color:var(--ink3); font-family:Consolas,monospace; font-size:11px;}
  .tabs-wrap input{display:none;}
  .tabs{display:flex; gap:0; margin:0 0 12px; border:1px solid var(--line); border-radius:8px; overflow:hidden; background:var(--card); width:fit-content;}
  .tabs label{display:inline-block; padding:8px 20px; border-right:1px solid var(--line); cursor:pointer; font-size:13px; background:var(--card); color:var(--ink2); user-select:none; font-weight:500;}
  .tabs label:last-child{border-right:none;}
  #tab-short:checked ~ .tabs label[for="tab-short"],
  #tab-trend:checked ~ .tabs label[for="tab-trend"],
  #tab-value:checked ~ .tabs label[for="tab-value"]{background:var(--blue); color:#fff; border-color:var(--blue);}
  .panel{display:none;}
  #tab-short:checked ~ .panel-short,
  #tab-trend:checked ~ .panel-trend,
  #tab-value:checked ~ .panel-value{display:block;}
  .idx-grid{display:grid; grid-template-columns:repeat(auto-fill,minmax(170px,1fr)); gap:10px;}
  .idx-card{border:1px solid var(--line); border-radius:8px; padding:10px 14px; background:var(--card);}
  .idx-card .iname{font-weight:600; font-size:13.5px;}
  .idx-card .ival{font-size:16px; font-weight:600; margin:2px 0;}
  .idx-card .imeta{font-size:11.5px; color:var(--ink2); line-height:1.7;}
  .st-bull{background:var(--upbg); color:var(--up); border:1px solid rgba(226,85,79,.4); border-radius:5px; padding:1px 8px; font-size:11px; font-weight:600;}
  .st-bear{background:var(--downbg); color:var(--down); border:1px solid rgba(47,174,118,.4); border-radius:5px; padding:1px 8px; font-size:11px; font-weight:600;}
  .st-mix{background:var(--panel-2); color:var(--ink2); border:1px solid var(--line); border-radius:5px; padding:1px 8px; font-size:11px; font-weight:600;}
  .sig-tag{border-radius:5px; padding:1px 7px; font-size:11px; font-weight:600; margin-right:4px;}
  .sig-bk{background:var(--purplebg); color:var(--purple); border:1px solid rgba(155,142,242,.4);}
  .sig-pb{background:var(--amberbg); color:var(--amber); border:1px solid rgba(232,162,58,.4);}
  .sig-hi{background:var(--bluebg); color:var(--blue); border:1px solid rgba(95,168,204,.4);}

  /* ==========================================================
     P16 统一规范层 · 间距 / 对齐 / 层级 / 留白 / 折叠
     同一套参数贯穿全站；hover 一律「文字变亮、底色微变」，不再变白
     ========================================================== */
  /* 只给卡片间距，绝不设 display —— 否则覆盖 .panel{display:none} 造成跨周期面板泄漏 */
  .panel-trend .card + .card,.panel-value .card + .card{margin-top:var(--sp);}
  .sub-grid .sub-box:last-child:nth-child(odd){grid-column:1/-1;}
  .topbar{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:14px 18px;margin-bottom:var(--sp);gap:12px;box-shadow:none;}
  h1{font-size:16px;font-weight:600;color:var(--ink);letter-spacing:-.01em;}
  .sub{color:var(--ink3);font-size:11.5px;margin-top:2px;}
  .datebtn{border:1px solid var(--line);color:var(--ink2);border-radius:var(--r-sm);padding:5px 12px;font-size:12px;transition:color .2s ease,border-color .2s ease,background .2s ease;}
  .datebtn:hover{color:var(--ink);border-color:var(--line-2);background:var(--surface-2);}
  .datebtn.active{background:var(--accent);color:#1A1712;border-color:var(--accent);font-weight:600;}
  .tabs-wrap{margin-bottom:var(--sp);}
  .tabs{border:1px solid var(--line);border-radius:var(--r-sm);background:var(--surface);overflow:hidden;margin:0 0 var(--sp);width:fit-content;}
  .tabs label{padding:8px 22px;font-size:12.5px;color:var(--ink2);background:transparent;border-right:1px solid var(--line);font-weight:500;transition:color .2s ease,background .2s ease;}
  .tabs label:hover{color:var(--ink);background:var(--surface-2);}
  #tab-short:checked ~ .tabs label[for="tab-short"],
  #tab-trend:checked ~ .tabs label[for="tab-trend"],
  #tab-value:checked ~ .tabs label[for="tab-value"]{background:var(--accent);color:#1A1712;border-color:var(--accent);font-weight:600;}
  .desk-grid{gap:var(--sp);}
  .desk-grid .col{gap:var(--sp);min-width:0;}
  @media (min-width:1024px){
    .desk-grid{grid-template-columns:208px minmax(0,1.4fr) minmax(0,1fr);}
    /* 保留列内可滚动（超高列底部可达），但滚动条完全隐藏 */
    .desk-grid .col-nav,.desk-grid .col-side{top:20px;max-height:calc(100vh - 40px);overflow-y:auto;padding-right:0;}
  }
  .card,.view .card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:var(--pad);margin-bottom:0;box-shadow:none;}
  .nav-card{padding:14px 0 14px;}
  .brand{background:transparent;color:var(--ink);font-size:14px;letter-spacing:.02em;padding:2px 14px 10px;text-align:left;border-bottom:1px solid var(--line);margin:0 0 10px;border-radius:0;}
  .brand::before{content:"";display:inline-block;width:6px;height:6px;border-radius:2px;background:var(--accent);margin-right:8px;vertical-align:2px;}
  .brand-sub{text-align:left;color:var(--ink3);font-size:11px;padding:0 14px;margin:0 0 10px;}
  .nav-gt{font-size:10.5px;color:var(--ink3);letter-spacing:.12em;padding:10px 14px 4px;}
  .mod-btn{margin:1px 8px;padding:7px 10px;font-size:12px;border-radius:var(--r-sm);color:var(--ink2);transition:color .2s ease,background .2s ease;}
  .mod-btn:hover{background:var(--surface-2);color:var(--ink);}
  .mod-btn.active{background:var(--accent-soft);color:var(--accent-strong);border-color:rgba(201,161,94,.32);font-weight:600;}
  .mod-btn .ic{color:var(--ink3);font-size:12px;width:15px;}
  .mod-btn.active .ic{color:var(--accent-strong);}
  .mod-sep{background:var(--line);margin:8px 14px;}
  .toolbar{padding:0 0 11px;margin-bottom:14px;border-bottom:1px solid var(--line);gap:10px;align-items:center;}
  .tb-title{font-size:13.5px;font-weight:600;color:var(--ink);letter-spacing:.01em;display:flex;align-items:center;gap:7px;}
  .tb-title::before{content:"";width:3px;height:12px;border-radius:2px;background:var(--accent);opacity:.9;flex:none;}
  .tb-title .cnt{font-size:11.5px;color:var(--ink3);font-weight:400;}
  .tb-tip{font-size:11px;color:var(--ink3);line-height:1.6;}
  .scr-tabs{border:1px solid var(--line);border-radius:var(--r-sm);background:var(--surface-2);}
  .scr-btn{background:transparent;color:var(--ink2);padding:5px 13px;font-size:11.5px;border-right:1px solid var(--line);transition:color .2s ease,background .2s ease;}
  .scr-btn:hover{background:var(--hover);color:var(--ink);}
  .scr-btn.active{background:var(--accent);color:#1A1712;font-weight:600;}
  .scr-note{background:var(--surface-2);border:1px solid var(--line);border-radius:var(--r-sm);color:var(--ink3);font-size:11px;padding:7px 11px;margin-bottom:12px;line-height:1.6;}
  .cat-btn{background:var(--surface-2);border:1px solid var(--line);color:var(--ink2);font-size:11.5px;padding:4px 13px;transition:color .2s ease,border-color .2s ease,background .2s ease;}
  .cat-btn:hover{color:var(--ink);border-color:var(--line-2);background:var(--hover);}
  .cat-btn.active{background:var(--accent);color:#1A1712;border-color:var(--accent);}
  .btn{border:1px solid var(--line);background:var(--surface-2);border-radius:var(--r-sm);padding:6px 14px;color:var(--ink2);font-size:12px;transition:color .2s ease,border-color .2s ease;}
  .btn:hover{border-color:var(--line-2);color:var(--ink);}
  .f-item label{font-size:11px;color:var(--ink3);}
  .f-item select,.f-item input{border:1px solid var(--line);border-radius:var(--r-sm);background:var(--surface-2);color:var(--ink);font-size:12px;padding:6px 9px;}
  .ind-tag{border:1px solid var(--line);background:var(--surface-2);color:var(--ink2);font-size:11.5px;padding:3px 11px;transition:color .2s ease,border-color .2s ease;}
  .ind-tag:hover{color:var(--ink);border-color:var(--line-2);}
  .ind-tag.on{background:var(--bluebg);color:var(--blue);border-color:rgba(127,168,196,.4);}
  .grp{margin-bottom:18px;}
  .grp:last-child{margin-bottom:0;}
  .grp-head{padding:7px 11px;border-radius:var(--r-sm);font-size:12.5px;margin-bottom:9px;gap:8px;}
  .grp-head .cnt{font-size:11.5px;color:var(--ink3);}
  .lb-tag{font-size:11px;padding:1px 8px;border-radius:5px;}
  .t-lb7{background:rgba(217,96,90,.85);color:#fff;}
  .t-lb5{background:rgba(217,96,90,.68);color:#fff;}
  .t-lb4{background:rgba(217,96,90,.16);color:#E9938E;border:1px solid rgba(217,96,90,.4);}
  .t-lb3{background:rgba(201,161,94,.14);color:var(--accent-strong);border:1px solid rgba(201,161,94,.38);}
  .t-lb2{background:rgba(127,168,196,.13);color:#9CC0D6;border:1px solid rgba(127,168,196,.35);}
  .t-lb1{background:var(--surface-2);color:var(--ink2);border:1px solid var(--line);}
  table{font-size:11.5px;border-collapse:collapse;}
  th{background:var(--surface-2);color:var(--ink3);font-size:10.5px;font-weight:600;letter-spacing:.02em;padding:7px 9px;border:1px solid var(--line);}
  td{padding:6px 9px;border:1px solid var(--line);color:var(--ink);font-size:11.5px;}
  tr:nth-child(even) td{background:rgba(255,255,255,.018);}
  tr:hover td{background:var(--hover);color:var(--ink);}
  .num,.code,.metric-card .val,.core-cell .val,.prev-stat .v,.tl-time{font-family:var(--font-mono);font-variant-numeric:tabular-nums;}
  .code{color:var(--ink3);}
  .empty{color:var(--ink3);font-size:12px;padding:22px 0;}
  .cycle-hint{font-size:10.5px;color:var(--ink3);line-height:1.6;margin-top:10px;}
  .disclaimer{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-sm);color:var(--ink3);font-size:11px;padding:10px 14px;margin-top:var(--sp);line-height:1.7;}
  .foot{color:var(--ink3);font-size:10.5px;margin-top:14px;}
  .metric-card,.core-cell,.sent-item,.idx-card,.prev-stat,.theme-card,.sub-box,.mini-list,.np-card,.foc-card,.tlp-day,.tlp-pnode,.scr-note{border-radius:var(--r-sm);border:1px solid var(--line);background:var(--surface-2);}
  .metric-card .lab,.core-cell .lab{font-size:10.5px;color:var(--ink3);}
  .metric-card .val,.core-cell .val{font-size:17px;font-weight:600;}
  .np-card:hover{border-color:rgba(201,161,94,.4);}
  .np-big{color:var(--accent-strong);}
  .np-mem,.chip,.tlp-pnode,.tlp-day{background:var(--surface);border:1px solid var(--line);}
  .chip{border-radius:999px;font-size:11.5px;}
  .tlp-node{background:rgba(201,161,94,.08);border-left:2px solid var(--accent);color:var(--ink2);border-radius:var(--r-sm);}
  .sq-gap{border-left:2px solid var(--amber);background:rgba(201,161,94,.10);color:var(--accent-strong);border-radius:var(--r-sm);}
  .sq-gap.sq-break{border-left-color:var(--up);background:var(--upbg);color:#E9938E;}
  .tev-wrap{max-height:360px;border-left:1px solid var(--line);padding-left:12px;}
  .tl-title{font-size:13px;color:var(--ink);}
  .tl-title:hover{color:var(--accent-strong);}
  .tl-sum{color:var(--ink2);font-size:11.5px;line-height:1.7;}
  .ana{background:var(--surface-2);border:1px solid var(--line);border-radius:var(--r-sm);font-size:11px;}
  .kw{background:var(--upbg);color:#E9938E;font-weight:600;}
  .co-link{color:var(--accent-strong);border-bottom:1px dashed rgba(201,161,94,.55);transition:color .2s ease,background .2s ease;}
  .co-link:hover{color:#F0D3A4;background:var(--accent-soft);}
  .sec-dot{display:inline-block;width:5px;height:5px;border-radius:2px;background:var(--accent);margin-right:7px;vertical-align:2px;}
  /* 模块折叠：默认收起 / 展开后与原状态完全一致 */
  .fold-hidden{display:none !important;}
  .more-btn{display:flex;align-items:center;justify-content:center;gap:5px;width:fit-content;min-width:0;margin:8px 0 0;padding:3px 10px;border:1px solid var(--line);border-radius:999px;background:transparent;color:var(--ink3);font-family:inherit;font-size:10.5px;line-height:1.6;letter-spacing:.02em;white-space:nowrap;cursor:pointer;grid-column:1/-1;justify-self:start;flex:0 0 auto;transition:color .2s ease,border-color .2s ease,background .2s ease;}
  .more-btn:hover{background:var(--hover);border-color:var(--line-2);color:var(--ink);}
  .more-btn:focus-visible{outline:2px solid var(--accent);outline-offset:2px;}
  .more-n{font-family:var(--font-mono);font-size:10px;color:var(--accent);font-weight:600;}
  .more-ar{color:var(--ink3);font-size:11px;}
  #datebar{align-items:center;}
  .more-inline{align-self:center;margin:0;padding:3px 10px;}
  .desk-grid .col-nav,.desk-grid .col-side,.tev-wrap{scrollbar-width:none;-ms-overflow-style:none;}
  .desk-grid .col-nav::-webkit-scrollbar,.desk-grid .col-side::-webkit-scrollbar,.tev-wrap::-webkit-scrollbar{display:none;width:0;height:0;}

  /* 窄屏回调：必须排在规范层之后，否则被同优先级规则覆盖 */
  @media (max-width:760px){
    .wrap{padding:12px 10px 40px;}
    .topbar{align-items:stretch;padding:12px;gap:10px;}
    .topbar > div{min-width:0;}
    .datebar{width:100%;max-width:100%;gap:5px;}
    .datebtn{padding:4px 9px;font-size:11px;}
    .more-inline{font-size:10.5px;padding:3px 8px;}
    .tabs{width:100%;}
    .tabs label{flex:1;padding:8px 4px;font-size:12px;white-space:nowrap;}
    .card,.view .card{padding:13px 12px;overflow-x:auto;}
    .toolbar{flex-wrap:wrap;gap:8px;}
    .tb-tip{font-size:10.5px;}
    .desk-grid{gap:12px;}
    .desk-grid .col{gap:12px;}
    .scr-tabs{flex-wrap:wrap;}
    .scr-btn{flex:1;padding:5px 6px;font-size:11px;white-space:nowrap;}
    .np-cards,.foc-grid,.theme-grid,.idx-grid,.sub-grid,.two-col{grid-template-columns:1fr;}
    .metric-grid,.core-grid{grid-template-columns:repeat(3,1fr);}
    .foc-grid{gap:8px;}
    .tlp-sub{flex-direction:column;gap:6px;}
    .tlp-subname{min-width:0;}
  }
  /* ===== P18 个股深研抽屉：独立命名空间，不触碰任何既有规则 ===== */
  .sd-mask{position:fixed;inset:0;background:rgba(8,10,13,.60);opacity:0;pointer-events:none;z-index:900;transition:opacity .22s ease;}
  .sd-mask.on{opacity:1;pointer-events:auto;}
  .sd-wrap{position:fixed;top:0;right:0;bottom:0;z-index:901;width:420px;max-width:92vw;display:flex;flex-direction:column;background:var(--surface);border-left:1px solid var(--line-2);box-shadow:-20px 0 44px rgba(0,0,0,.30);transform:translateX(101%);transition:transform .26s cubic-bezier(.22,.61,.36,1);}
  .sd-wrap.on{transform:translateX(0);}
  .sd-head{flex:0 0 auto;display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:18px 20px 14px;border-bottom:1px solid var(--line);}
  .sd-title{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap;}
  .sd-name{font-size:19px;font-weight:600;color:var(--ink);letter-spacing:.01em;}
  .sd-code{font-family:var(--font-mono);font-size:12px;color:var(--ink3);}
  .sd-sub{margin-top:6px;font-size:11.5px;color:var(--ink3);line-height:1.6;}
  .sd-badge{display:inline-block;padding:1px 7px;margin-right:6px;border-radius:999px;border:1px solid var(--line-2);font-size:10.5px;color:var(--ink2);}
  .sd-badge.up{color:var(--up);border-color:var(--up);}
  .sd-badge.amber{color:var(--amber);border-color:var(--amber);}
  .sd-badge.down{color:var(--down);border-color:var(--down);}
  .sd-close{flex:0 0 auto;width:26px;height:26px;border:1px solid var(--line);border-radius:999px;background:transparent;color:var(--ink3);font:inherit;font-size:13px;line-height:1;cursor:pointer;transition:color .2s ease,border-color .2s ease,background .2s ease;}
  .sd-close:hover{color:var(--ink);border-color:var(--line-2);background:var(--hover);}
  .sd-close:focus-visible{outline:2px solid var(--accent);outline-offset:2px;}
  .sd-body{flex:1 1 auto;overflow-y:auto;padding:16px 20px 26px;scrollbar-width:none;-ms-overflow-style:none;}
  .sd-body::-webkit-scrollbar{display:none;width:0;height:0;}
  .sd-sec + .sd-sec{margin-top:18px;}
  .sd-sec-t{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:9px;font-size:11px;font-weight:600;letter-spacing:.06em;color:var(--ink3);}
  .sd-sec-t .sd-tval{font-family:var(--font-mono);font-size:11px;color:var(--accent);font-weight:600;letter-spacing:0;}
  .sd-exts{display:flex;flex-wrap:wrap;gap:7px;}
  .sd-ext{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border:1px solid var(--line);border-radius:999px;color:var(--ink2);font-size:10.5px;text-decoration:none;white-space:nowrap;transition:color .2s ease,border-color .2s ease,background .2s ease;}
  .sd-ext:hover{color:var(--ink);border-color:var(--line-2);background:var(--hover);}
  .sd-kv{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:var(--r-sm);overflow:hidden;}
  .sd-cell{background:var(--surface-2);padding:9px 10px;}
  .sd-cell .k{display:block;font-size:10px;color:var(--ink3);margin-bottom:4px;}
  .sd-cell .v{display:block;font-family:var(--font-mono);font-size:13px;color:var(--ink);line-height:1.25;white-space:nowrap;}
  .sd-cell .v.up{color:var(--up);}
  .sd-cell .v.dn{color:var(--down);}
  .sd-meta{display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:8px;font-size:10.5px;color:var(--ink3);}
  .sd-meta b{font-family:var(--font-mono);font-weight:500;color:var(--ink2);}
  .sd-line{display:flex;align-items:center;gap:9px;margin-bottom:7px;}
  .sd-line .lb{flex:0 0 62px;font-size:10.5px;color:var(--ink2);}
  .sd-line .track{flex:1;height:5px;border-radius:3px;background:var(--surface-3);overflow:hidden;}
  .sd-line .fill{display:block;height:100%;border-radius:3px;background:var(--accent);transition:width .3s ease;}
  .sd-line .sc{flex:0 0 34px;text-align:right;font-family:var(--font-mono);font-size:10.5px;color:var(--ink2);}
  .sd-stack{display:flex;height:8px;border-radius:4px;overflow:hidden;background:var(--surface-3);}
  .sd-stack i{display:block;height:100%;}
  .sd-legend{display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:9px;font-size:10.5px;color:var(--ink3);}
  .sd-legend span i{display:inline-block;width:7px;height:7px;border-radius:2px;margin-right:5px;vertical-align:0;}
  .sd-legend b{font-family:var(--font-mono);font-weight:600;color:var(--ink2);}
  .sd-note{padding:9px 11px;border-radius:var(--r-sm);background:var(--surface-2);border-left:2px solid var(--accent);font-size:11.5px;line-height:1.7;color:var(--ink2);}
  .sd-note + .sd-note{margin-top:7px;}
  .sd-note.risk{border-left-color:var(--up);}
  .sd-note .t{display:block;margin-bottom:3px;font-size:10px;letter-spacing:.06em;color:var(--ink3);}
  .sd-trail{display:flex;align-items:flex-end;gap:8px;height:96px;padding:0 2px;}
  .sd-tcol{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:5px;height:100%;min-width:0;}
  .sd-tbar{width:100%;max-width:36px;border-radius:3px 3px 0 0;min-height:3px;transition:height .3s ease;}
  .sd-tv{font-family:var(--font-mono);font-size:10px;color:var(--ink2);}
  .sd-td{font-size:9.5px;color:var(--ink3);white-space:nowrap;}
  .sd-empty{padding:14px 12px;border:1px dashed var(--line-2);border-radius:var(--r-sm);font-size:11.5px;line-height:1.8;color:var(--ink3);}
  .sd-foot{margin-top:20px;padding-top:12px;border-top:1px solid var(--line);font-size:10px;line-height:1.8;color:var(--ink3);}
  /* 窄屏回调：排在规范层之后，独立类名不覆盖既有断点 */
  @media (max-width:760px){
    .sd-wrap{width:100%;max-width:100%;}
    .sd-head{padding:15px 14px 12px;}
    .sd-body{padding:14px 14px 24px;}
    .sd-kv{grid-template-columns:repeat(2,1fr);}
  }
  /* ===== P19 资讯雷达：独立命名空间，不触碰 P16/P17/P18 既有规则 ===== */
  .rd-status{display:flex;flex-wrap:wrap;gap:1px;background:var(--line);border:1px solid var(--line);border-radius:var(--r-sm);overflow:hidden;margin-bottom:12px;}
  .rd-stat{flex:1 1 90px;background:var(--surface-2);padding:9px 11px;}
  .rd-stat .v{display:block;font-family:var(--font-mono);font-size:15px;color:var(--ink);line-height:1.2;}
  .rd-stat .k{display:block;font-size:10px;color:var(--ink3);margin-top:3px;}
  .rd-when{flex:1 1 100%;background:var(--surface-2);padding:6px 11px;font-size:10px;color:var(--ink3);border-top:1px solid var(--line);}
  .rd-filter-row{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;}
  .rd-filter-sub{align-items:center;margin-bottom:12px;}
  .rd-chip{padding:3px 10px;border:1px solid var(--line);border-radius:999px;background:transparent;color:var(--ink2);font:inherit;font-size:11px;line-height:1.6;white-space:nowrap;cursor:pointer;transition:color .2s ease,border-color .2s ease,background .2s ease;}
  .rd-chip:hover{color:var(--ink);border-color:var(--line-2);background:var(--hover);}
  .rd-chip.active{border-color:var(--accent);color:var(--accent-strong);background:var(--accent-soft);font-weight:600;}
  .rd-n{font-family:var(--font-mono);font-size:10px;opacity:.7;margin-left:3px;}
  .rd-linkbtn{padding:3px 2px;border:0;background:transparent;color:var(--ink3);font:inherit;font-size:10.5px;cursor:pointer;border-bottom:1px dashed var(--line-2);}
  .rd-linkbtn:hover{color:var(--accent-strong);}
  .rd-srcs{margin:0 0 12px;padding:10px 11px;border:1px dashed var(--line-2);border-radius:var(--r-sm);}
  .rd-srcs-t{font-size:10.5px;color:var(--ink3);margin-bottom:8px;line-height:1.7;}
  .rd-src-grid{display:flex;flex-wrap:wrap;gap:5px;}
  .rd-src-pill{padding:1px 7px;border:1px solid var(--line);border-radius:999px;font-size:10px;color:var(--ink2);white-space:nowrap;}
  .rd-src-pill.bad{border-style:dashed;color:var(--ink3);}
  .rd-divider{width:1px;height:14px;background:var(--line-2);margin:0 3px;}
  #radar-body{border-left:1px solid var(--line);padding-left:16px;}
  .rd-item{position:relative;padding:0 0 12px 0;margin-bottom:11px;border-bottom:1px dashed var(--line);}
  .rd-item:last-child{border-bottom:none;margin-bottom:0;}
  .rd-item::before{content:"";position:absolute;left:-20px;top:6px;width:6px;height:6px;border-radius:50%;background:var(--accent);}
  .rd-meta{display:flex;flex-wrap:wrap;align-items:center;gap:7px;margin-bottom:5px;font-size:10.5px;color:var(--ink3);}
  .rd-time{font-family:var(--font-mono);}
  .rd-track{padding:1px 7px;border:1px solid var(--line);border-radius:999px;color:var(--ink2);}
  .rd-src{color:var(--ink2);}
  .rd-lang{padding:0 5px;border-radius:3px;background:var(--accent-soft);color:var(--accent);font-size:9.5px;}
  .rd-lang.en{background:transparent;color:var(--ink3);border:1px solid var(--line);}
  .rd-title{display:block;font-size:13px;font-weight:600;color:var(--ink);text-decoration:none;line-height:1.55;}
  .rd-title:hover{color:var(--accent-strong);}
  .rd-sum{font-size:11.5px;color:var(--ink2);line-height:1.7;margin-top:4px;}
  .rd-hint{margin-top:10px;font-size:10.5px;color:var(--ink3);line-height:1.7;}
  @media (max-width:760px){
    .rd-stat{flex:1 1 44%;}
    .rd-title{font-size:12.5px;}
    #radar-body{padding-left:13px;}
    .rd-item::before{left:-17px;}
  }
  /* ===== P20 周期锚定链：独立命名空间，沿用 P16 令牌 ===== */
  .an-sum{display:flex;flex-wrap:wrap;gap:1px;background:var(--line);border:1px solid var(--line);border-radius:var(--r-sm);overflow:hidden;margin-bottom:12px;}
  .an-sum-c{flex:1 1 84px;background:var(--surface-2);padding:9px 11px;}
  .an-sum-c .v{display:block;font-family:var(--font-mono);font-size:15px;color:var(--ink);line-height:1.2;font-variant-numeric:tabular-nums;}
  .an-sum-c .k{display:block;font-size:10px;color:var(--ink3);margin-top:3px;}
  .an-sum-n{flex:1 1 100%;background:var(--surface-2);padding:6px 11px;font-size:10px;color:var(--ink3);border-top:1px solid var(--line);line-height:1.7;}
  .an-tools{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-bottom:12px;}
  .an-chip{padding:3px 10px;border:1px solid var(--line);border-radius:999px;background:transparent;color:var(--ink2);font:inherit;font-size:11px;line-height:1.6;white-space:nowrap;cursor:pointer;transition:color .2s ease,border-color .2s ease,background .2s ease;}
  .an-chip:hover{color:var(--ink);border-color:var(--line-2);background:var(--hover);}
  .an-chip.active{border-color:var(--accent);color:var(--accent-strong);background:var(--accent-soft);}
  .an-n{font-family:var(--font-mono);font-size:10px;opacity:.7;margin-left:3px;font-variant-numeric:tabular-nums;}
  .an-sep{width:1px;height:14px;background:var(--line-2);margin:0 3px;}
  .an-relay{display:flex;flex-wrap:wrap;gap:7px;align-items:center;margin-bottom:14px;padding:9px 11px;border:1px dashed var(--line-2);border-radius:var(--r-sm);}
  .an-relay-t{font-size:10.5px;color:var(--ink3);}
  .an-relay-i{font-size:11px;color:var(--ink2);white-space:nowrap;}
  .an-relay-i b{color:var(--accent-strong);font-weight:500;}
  .an-relay-i span{color:var(--ink3);}
  .an-chain{border:1px solid var(--line);border-radius:var(--r-sm);background:var(--surface-2);margin-bottom:12px;overflow:hidden;}
  .an-chain:last-child{margin-bottom:0;}
  .an-head{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:11px 13px;border-bottom:1px solid var(--line);}
  .an-key{font-size:15px;color:var(--ink);letter-spacing:.02em;}
  .an-key::before{content:"「";color:var(--ink3);}
  .an-key::after{content:"」";color:var(--ink3);}
  .an-badge{padding:1px 8px;border-radius:999px;font-size:10px;border:1px solid var(--line);color:var(--ink2);white-space:nowrap;}
  .an-badge.healthy{border-color:var(--green);color:var(--green);background:var(--greenbg);}
  .an-badge.relay{border-color:var(--accent);color:var(--accent-strong);background:var(--accent-soft);}
  .an-badge.ended{color:var(--ink3);}
  .an-badge.broken{border-color:var(--red);color:var(--red);background:var(--redbg);}
  .an-badge.platform{border-color:var(--green);color:var(--green);}
  .an-meta{margin-left:auto;font-size:10.5px;color:var(--ink3);font-family:var(--font-mono);font-variant-numeric:tabular-nums;}
  .an-body{padding:11px 13px 13px;}
  .an-row{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline;font-size:11.5px;line-height:1.85;padding:3px 0;}
  .an-lab{flex:none;width:52px;color:var(--ink3);font-size:10.5px;}
  .an-state{font-size:10.5px;color:var(--ink2);}
  .an-mem{display:flex;flex-wrap:wrap;gap:5px;flex:1 1 200px;min-width:0;}
  .an-chip-mem{padding:1px 7px;border:1px solid var(--line);border-radius:var(--r-sm);font-size:10.5px;color:var(--ink2);}
  .an-chip-mem.first{border-color:var(--accent);color:var(--accent-strong);}
  .an-spark{display:flex;align-items:flex-end;gap:2px;height:26px;margin-top:7px;}
  .an-bar{flex:1 1 3px;min-width:2px;max-width:10px;background:var(--line-2);border-radius:1px 1px 0 0;}
  .an-bar.peak{background:var(--red);}
  .an-bar.today{background:var(--accent);}
  .an-bar.zero{background:var(--line);}
  .an-events{margin-top:10px;padding-left:13px;border-left:1px solid var(--line);}
  .an-ev{position:relative;font-size:10.5px;color:var(--ink2);line-height:1.85;}
  .an-ev::before{content:"";position:absolute;left:-16px;top:8px;width:5px;height:5px;border-radius:50%;background:var(--line-2);}
  .an-ev.hot::before{background:var(--accent);}
  .an-ev-d{font-family:var(--font-mono);color:var(--ink3);margin-right:6px;font-variant-numeric:tabular-nums;}
  .an-ev-t{color:var(--ink3);margin-right:5px;}
  .an-hint{font-size:10.5px;color:var(--ink3);line-height:1.7;margin-top:10px;}
  .np-clus{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px;}
  .np-clus-t{font-size:10.5px;color:var(--ink3);margin-bottom:6px;}
  .np-clus-p{padding:2px 9px;border:1px solid var(--line);border-radius:999px;font-size:10.5px;color:var(--ink2);}
  .np-clus-p.live{border-color:var(--accent);color:var(--accent-strong);background:var(--accent-soft);}
  .cu-anchor{padding:1px 7px;border-radius:999px;font-size:10px;border:1px solid var(--line);color:var(--ink2);}
  .cu-anchor.ok{border-color:var(--green);color:var(--green);}
  .cu-anchor.bad{border-color:var(--red);color:var(--red);}
  @media (max-width:760px){
    .an-sum-c{flex:1 1 44%;}
    .an-body{padding:10px 11px;}
    .an-head{padding:10px 11px;}
    .an-meta{margin-left:0;flex:1 1 100%;}
    .an-lab{width:100%;}
    .an-events{padding-left:11px;}
    .an-ev::before{left:-14px;}
  }
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
</head>
<body>
<div class="wrap">
<div class="shell">
<div id="h-toast"></div>
  <div class="topbar">
    <div>
      <h1>A股行情看板 · 短线 + 中长线趋势</h1>
      <div class="sub" id="subline"></div>
    </div>
    <div class="datebar" id="datebar"></div>
  </div>

  <div class="tabs-wrap">
    <input type="radio" name="mod" id="tab-short" checked>
    <input type="radio" name="mod" id="tab-trend">
    <input type="radio" name="mod" id="tab-value">
    <div class="tabs">
      <label for="tab-short">短线复盘</label>
      <label for="tab-trend">中长线趋势</label>
      <label for="tab-value">长线价值</label>
    </div>

  <div class="panel panel-short">
  <div class="desk-grid">
    <div class="col col-nav">
      <div class="card nav-card">
        <div class="brand">A股复盘台</div>
        <div class="brand-sub" id="brand-sub">短线 · 涨停梯队</div>
        <div id="nav-modules"></div>
      </div>

      <div class="card">
        <div style="font-weight:600;font-size:13px;margin-bottom:8px;color:var(--ink2);">梯队筛选</div>
        <div class="filters">
          <div class="f-item">
            <label>连板数</label>
            <select id="f-lb">
              <option value="0">全部</option>
              <option value="1">仅首板</option>
              <option value="2">2板</option>
              <option value="3">3板</option>
              <option value="4">4板及以上</option>
            </select>
          </div>
          <div class="f-item">
            <label>换手率 %</label>
            <div style="display:flex; gap:6px; align-items:center;">
              <input type="number" id="f-turn-min" placeholder="0" min="0" max="100">
              <span style="color:var(--ink3); font-size:12px;">~</span>
              <input type="number" id="f-turn-max" placeholder="100" min="0" max="100">
            </div>
          </div>
          <div class="f-item">
            <label>封板时间</label>
            <select id="f-seal">
              <option value="all">全部</option>
              <option value="early">早盘 ≤10:00</option>
              <option value="mid">盘中</option>
              <option value="late">尾盘 ≥14:30</option>
            </select>
          </div>
          <div class="f-item">
            <label>炸板</label>
            <select id="f-zb">
              <option value="all">全部</option>
              <option value="0">0 次</option>
              <option value="1">≥1 次</option>
            </select>
          </div>
          <div class="f-item">
            <label>操作</label>
            <button class="btn" id="f-reset" type="button">重置</button>
          </div>
        </div>
        <div class="ind-tags" id="ind-tags"></div>
      </div>
    </div>

    <div class="col col-main">
      <div class="view" id="view-stage">
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">涨停梯队 <span class="cnt" id="stage-cnt"></span></div>
            <div class="tb-tip" id="stage-tip"></div>
          </div>
          <div id="stage-body"></div>
        </div>
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">板块晋级率 <span class="cnt" id="promo-cnt"></span></div>
            <div class="tb-tip">一进二 / 二进三 / 三进四 · 同比昨日（↑升 ↓降）</div>
          </div>
          <div id="promo-body"></div>
        </div>
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">资金透视 <span class="cnt">复盘闭环</span></div>
            <div class="tb-tip">昨日涨停表现 · 龙虎榜 · 板块资金 · 游资动向</div>
          </div>
          <div id="ext-card"></div>
        </div>
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">解禁日历 · 未来 30 日</div>
            <div class="tb-tip">东财数据中心 · 占总股本比 ≥5% 标红 · 解禁≠必跌，关注解禁前后的筹码结构</div>
          </div>
          <div id="unlock-body"></div>
        </div>
      </div>
      <div class="view" id="view-alert" style="display:none">
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">溢价 · 异动预警</div>
            <div class="tb-tip" id="alert-tip"></div>
          </div>
          <div id="alert-body"></div>
        </div>
      </div>
      <div class="view" id="view-cycle" style="display:none">
        <div class="card">
          <div class="toolbar"><div class="tb-title">情绪 · 周期</div></div>
          <div id="cycle-body"></div>
        </div>
      </div>
      <div class="view" id="view-anchor" style="display:none">
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">周期锚定链 <span class="cnt" id="anchor-cnt"></span></div>
            <div class="tb-tip">属性簇取涨停原因标签 · 双字/谐音不拆 · 锚状态由 K 线量化</div>
          </div>
          <div id="anchor-sum"></div>
          <div id="anchor-tools"></div>
          <div id="anchor-relay"></div>
          <div id="anchor-body"></div>
        </div>
      </div>
      <div class="view" id="view-theme" style="display:none">
        <div class="card">
          <div class="toolbar"><div class="tb-title">主线 · 龙头 · 潜龙</div></div>
          <div id="theme-body"></div>
        </div>
      </div>
      <div class="view" id="view-news" style="display:none">
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">公告资讯 <span class="cnt" id="news-cnt"></span></div>
            <div class="tb-tip">按发布时间倒序 · 关键词红字高亮</div>
          </div>
          <div id="news-body"></div>
        </div>
      </div>
      <div class="view" id="view-radar" style="display:none">
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">资讯雷达 <span class="cnt" id="radar-cnt"></span></div>
            <div class="tb-tip">12 赛道 · 106 个 RSS 源 · 按发布时间倒序</div>
          </div>
          <div id="radar-status"></div>
          <div id="radar-srcs" style="display:none"></div>
          <div id="radar-filters"></div>
          <div id="radar-body"></div>
        </div>
      </div>
      <div class="view" id="view-focus" style="display:none">
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">聚焦挖掘 <span class="cnt" id="foc-cnt"></span></div>
            <div class="scr-tabs">
              <button class="scr-btn active" data-f="focus" onclick="setFocusTab('focus')">市场聚焦</button>
              <button class="scr-btn" data-f="np" onclick="setFocusTab('np')">字辈挖掘</button>
              <button class="scr-btn" data-f="tlp" onclick="setFocusTab('tlp')">题材库</button>
              <button class="scr-btn" data-f="cu" onclick="setFocusTab('cu')">补涨雷达</button>
            </div>
          </div>
          <div class="ftab" id="ftab-focus">
            <div class="tb-tip" style="margin-bottom:10px;">新股 / 并购重组 / 复牌等情绪共振标的 · 点名字看K线分时</div>
            <div id="focus-body"></div>
          </div>
          <div class="ftab" id="ftab-np" style="display:none">
            <div class="tb-tip" style="margin-bottom:10px;">同一汉字被 ≥3 只涨停共享 = 共识字辈（华字辈/洋字辈）· <span id="np-cnt"></span></div>
            <div id="np-body"></div>
          </div>
          <div class="ftab" id="ftab-tlp" style="display:none">
            <div class="tb-tip" style="margin-bottom:10px;">AI硬件·战略板块（中长线） / AI应用·传媒·消费（短线）· <span id="tl-cnt"></span></div>
            <div id="tl-body"></div>
          </div>
          <div class="ftab" id="ftab-cu" style="display:none">
            <div class="tb-tip" style="margin-bottom:10px;">龙头一字/断板/回调 → 板块内伴生补涨候选（字辈&gt;题材&gt;行业）· <span id="cu-cnt"></span></div>
            <div id="cu-body"></div>
          </div>
        </div>
      </div>
      <div class="view" id="view-timeline" style="display:none">
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">时间线 <span class="cnt" id="tlp-cnt"></span></div>
            <div class="scr-tabs">
              <button class="scr-btn active" data-p="day" onclick="setTlPeriod('day')">当日</button>
              <button class="scr-btn" data-p="week" onclick="setTlPeriod('week')">当周</button>
              <button class="scr-btn" data-p="month" onclick="setTlPeriod('month')">当月</button>
            </div>
          </div>
          <div class="tb-tip" id="tlp-tip"></div>
          <div id="tlp-body"></div>
        </div>
      </div>
      <div class="view" id="view-screener" style="display:none">
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">多因子选股器 <span class="cnt" id="scr-cnt"></span></div>
            <div class="scr-tabs">
              <button class="scr-btn active" data-m="short" onclick="setScrMode('short')">短线</button>
              <button class="scr-btn" data-m="mid" onclick="setScrMode('mid')">中线</button>
              <button class="scr-btn" data-m="long" onclick="setScrMode('long')">长线</button>
            </div>
          </div>
          <div class="scr-note" id="scr-note"></div>
          <div id="scr-body"></div>
        </div>
      </div>
    </div>

      <div class="col col-side">
        <div class="card">
          <div id="side-tone"></div>
        </div>
        <div class="card">
          <div id="side-coredata"></div>
        </div>
        <div class="card">
          <div id="side-prev"></div>
        </div>
      </div>
    </div>
  </div>

  <div class="panel panel-trend">
    <div class="card">
      <div id="trend-idx"></div>
    </div>
    <div class="card">
      <div class="filters">
        <div class="f-item">
          <label>强度档位</label>
          <select id="t-lv">
            <option value="all">全部</option>
            <option value="强">仅强</option>
            <option value="中">中及以上</option>
          </select>
        </div>
        <div class="f-item">
          <label>信号</label>
          <select id="t-sig">
            <option value="all">全部</option>
            <option value="bk">仅突破</option>
            <option value="pb">仅回踩</option>
            <option value="hi">仅新高</option>
          </select>
        </div>
        <div class="f-item">
          <label>筛选</label>
          <button class="btn" id="t-reset" type="button">重置</button>
        </div>
      </div>
      <div id="trend-pool" style="margin-top:12px;"></div>
    </div>
  </div>

  <div class="panel panel-value">
    <div class="card">
      <div id="value-card"></div>
    </div>
  </div>
  </div>

  <div class="disclaimer"><b>免责声明：</b>本看板数据来自公开行情接口（东方财富/乐咕乐股），仅供个人复盘研究参考，不构成投资建议。市场有风险，投资需谨慎。涨停原因、题材归类等字段将在后续版本完善。</div>
  <div class="foot">A股短线看板 · 由 _gen_board.py 生成 · 数据仅供复盘参考</div>
</div>
</div>

<script>
window.BOARD_DATA = __DATA__;
</script>
<script>
(function () {
  "use strict";
  var data = window.BOARD_DATA;
  var cur = data.dates[data.dates.length - 1];
  var filters = { lb: 0, turnMin: 0, turnMax: 100, seal: "all", zb: "all", inds: {} };

  function fmtDate(d) {
    return d.slice(0, 4) + "-" + d.slice(4, 6) + "-" + d.slice(6, 8);
  }
  function fmtMoney(v) {
    if (v === null || v === undefined) return "-";
    v = Number(v);
    if (v >= 100000000) return (v / 100000000).toFixed(2) + "亿";
    if (v >= 10000) return (v / 10000).toFixed(0) + "万";
    return String(v);
  }
  function fmtSeal(t) {
    if (!t) return "-";
    t = String(t);
    return t.slice(0, 2) + ":" + t.slice(2, 4);
  }
  function esc(s) {
    return String(s === null || s === undefined ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  /* ===== P16 首屏减弱动效判定（必须在 init 之前求值） ===== */
  var prefersReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function fx(fn) { if (window.gsap && !prefersReduced) fn(window.gsap); }

  /* ===== P16 模块折叠引擎：全站统一「最大展示数 + 查看更多」 =====
     规则 = [容器选择器, 直接子项选择器, 上限]
     用 :scope > 限定直接子项，天然避免嵌套容器互相吞并；表头行自动跳过。 */
  var FOLD_RULES = [
    ["#stage-body", ":scope > .grp", 8, "in"],
    ["#stage-body .grp > table", "tr", 12, "out"],
    ["#promo-body table", "tr", 12, "out"],
    ["#ext-card .mini-list", ":scope > .row", 10, "in"],
    ["#ext-card .sub-box", ":scope > .lhb-row", 10, "in"],
    ["#unlock-body table", "tr", 12, "out"],
    ["#alert-body table", "tr", 15, "out"],
    ["#theme-body .grp", ":scope > .theme-row, :scope > .dragon-row", 12, "in"],
    ["#scr-body table", "tr", 20, "out"],
    ["#news-body .tl", ":scope > .tl-item", 15, "in"],
    ["#radar-body", ":scope > .rd-item", 20, "in"],
    ["#anchor-body", ":scope > .an-chain", 6, "in"],
    ["#anchor-body .an-events", ":scope > .an-ev", 6, "in"],
    ["#anchor-body .an-mem", ":scope > .an-chip-mem", 12, "in"],
    ["#focus-body .foc-grid", ":scope > .foc-card", 8, "in"],
    ["#np-body .np-cards", ":scope > .np-card", 8, "in"],
    ["#np-body .np-mems", ":scope > .np-mem", 12, "in"],
    ["#tl-body", ":scope > .tlp-group", 3, "in"],
    ["#tl-body .tlp-group", ":scope > .tlp-sub", 8, "in"],
    ["#tl-body .tlp-chips", ":scope > .chip", 12, "in"],
    ["#cu-body", ":scope > .cu-row", 8, "in"],
    ["#tlp-body .tlp-sec", ":scope > .tlp-node, :scope > .tlp-pnode", 6, "in"],
    ["#tlp-body .tlp-inds", ":scope > .chip", 16, "in"],
    ["#tlp-body .tev-wrap", ":scope > .tev", 30, "out"],
    ["#tlp-body .tlp-days", ":scope > .tlp-day", 12, "out"],
    ["#tlp-body .tlp-matrix table", "tr", 12, "out"],
    ["#trend-pool table", "tr", 20, "out"],
    ["#value-card table", "tr", 20, "out"],
    ["#value-card .theme-grid", ":scope > .theme-card", 8, "in"],
    ["#ind-tags", ":scope > .ind-tag", 16, "in"],
    ["#side-prev", ":scope > .prev-row", 10, "in"],
    ["#datebar", ":scope > .datebtn", 14, "inline"]
  ];
  function applyFolds(root) {
    var base = root || document;
    FOLD_RULES.forEach(function (rule) {
      var boxes = [];
      if (base.matches && base.matches(rule[0])) boxes.push(base);
      Array.prototype.push.apply(boxes, base.querySelectorAll(rule[0]));
      boxes.forEach(function (box) {
        /* 复渲染后旧折叠状态失效 -> 清理旧按钮并重建，避免按钮操作游离节点 */
        if (box._foldState) {
          var alive = box._foldState.hidden.length > 0 &&
            box._foldState.hidden.every(function (n) { return n.isConnected; });
          if (alive) return;
          if (box._foldState.btn && box._foldState.btn.parentNode) {
            box._foldState.btn.parentNode.removeChild(box._foldState.btn);
          }
          box._foldState = null;
        }
        var nodes = Array.prototype.slice.call(box.querySelectorAll(rule[1])).filter(function (n) {
          return !(n.tagName === "TR" && n.querySelector("th"));
        });
        if (nodes.length <= rule[2]) return;
        var hidden = nodes.slice(rule[2]);
        var state = { hidden: hidden, btn: null, open: false, cap: rule[2] };
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "more-btn";
        function paint() {
          btn.innerHTML = state.open
            ? '<span>收起</span><span class="more-ar">&#8963;</span>'
            : '<span>查看更多</span><span class="more-n">' + hidden.length + '</span><span class="more-ar">&#8964;</span>';
        }
        paint();
        hidden.forEach(function (n) { n.classList.add("fold-hidden"); });
        btn.onclick = function () {
          state.open = !state.open;
          hidden.forEach(function (n) { n.classList.toggle("fold-hidden", !state.open); });
          paint();
        };
        state.btn = btn;
        box._foldState = state;
        var mode = rule[3] || "in";
        if (mode === "inline") {
          btn.className = "more-btn more-inline";
          box.appendChild(btn);
        } else if (mode === "out" && box.parentNode) {
          box.parentNode.insertBefore(btn, box.nextSibling);
        } else {
          /* 放进容器内部：按钮不再成为外层 grid 的新列，杜绝整列空白 */
          box.appendChild(btn);
        }
      });
    });
  }

  var histCache = {};
  function toast(msg) {
    var t = document.getElementById("h-toast");
    if (!t) return;
    t.textContent = msg;
    t.style.display = "block";
    clearTimeout(t._tm);
    t._tm = setTimeout(function () { t.style.display = "none"; }, 4000);
  }
  function setDate(d) {
    if (data.days[d]) { cur = d; renderAll(); return; }
    var ym = d.slice(0, 6);
    if (histCache[ym]) {
      Object.keys(histCache[ym]).forEach(function (k) { if (!data.days[k]) data.days[k] = histCache[ym][k]; });
      cur = d; renderAll(); return;
    }
    toast("加载 " + fmtDate(d) + " 历史数据...");
    fetch("data/history/history_" + ym + ".json").then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    }).then(function (j) {
      histCache[ym] = j;
      Object.keys(j).forEach(function (k) { if (!data.days[k]) data.days[k] = j[k]; });
      cur = d; renderAll();
    }).catch(function () {
      toast(fmtDate(d) + " 历史数据加载失败（本地 file:// 打开不支持，请在线访问 pages.dev）");
    });
  }
  window.setDate = setDate;

  function renderDatebar() {
    var bar = document.getElementById("datebar");
    bar.innerHTML = "";
    data.dates.forEach(function (d) {
      var b = document.createElement("button");
      b.className = "datebtn" + (d === cur ? " active" : "");
      b.textContent = fmtDate(d).slice(5);
      b.onclick = function () { setDate(d); };
      bar.appendChild(b);
    });
  }

  function renderSentiment() {
    var day = data.days[cur];
    var s = day.sent;
    var b = day.breadth;
    var sub = "数据截至 " + fmtDate(cur) + " 收盘 · 涨停池/跌停池/炸板池来自东方财富 · 广度来自乐咕乐股";
    document.getElementById("subline").textContent = sub;

    var items = [
      ["涨停", s.zt, b && b.real_zt !== null && b.real_zt !== undefined ? "真实涨停 " + b.real_zt : "连板高度 " + (s.max_lb || 0) + "板"],
      ["跌停", s.dt, b && b.real_dt ? "真实跌停 " + b.real_dt : ""],
      ["炸板", s.zb, "炸板率 " + s.zbrate + "%"],
      ["连板高度", s.max_lb + "板", s.top.length ? (s.top[0]['名称'] + " " + s.top[0].ztstat) : "无连板"],
      ["上涨家数", b ? b.up : "-", b ? "占比 " + (b.total ? Math.round(b.up / b.total * 100) : 0) + "%" : ""],
      ["下跌家数", b ? b.down : "-", b ? "占比 " + (b.total ? Math.round(b.down / b.total * 100) : 0) + "%" : ""],
      ["活跃度", b && b.activity ? b.activity : "-", "市场参与热度"],
    ];
    var html = '<div class="sent-grid">';
    items.forEach(function (it) {
      html += '<div class="sent-item"><div class="label">' + it[0] + '</div><div class="value">' + it[1] + '</div>' +
              (it[2] ? '<div class="subv">' + it[2] + '</div>' : '') + '</div>';
    });
    html += '<div class="sent-item"><div class="label">情绪标签</div><div class="value" style="padding-top:4px;"><span class="tag-big tag-' + s.tag_cls + '">' + s.tag + '</span></div><div class="subv">规则引擎 v0</div></div>';
    html += '</div>';
    // P9: 首次封板时间分布条（早盘含竞价封板占比 = 情绪强度代理）
    var st = day.seal;
    if (st) {
      var sc = {"竞价": "var(--up)", "早盘": "#D4664F", "上午": "var(--amber)", "下午": "#9a8f7d", "尾盘": "#6f675a"};
      var bar = "";
      st.buckets.forEach(function (b) {
        if (!b.n) return;
        bar += '<div style="width:' + b.pct + '%;background:' + sc[b.label] + ';" title="' + b.label + ' ' + b.n + ' 只（' + b.pct + '%）"></div>';
      });
      var legend = st.buckets.filter(function (b) { return b.n; }).map(function (b) {
        return '<span style="display:inline-flex;align-items:center;gap:4px;"><i style="width:8px;height:8px;border-radius:2px;background:' + sc[b.label] + ';display:inline-block;"></i>' + b.label + ' ' + b.n + '</span>';
      }).join(' ');
      html += '<div style="margin-top:12px;">' +
        '<div style="font-size:12px;color:var(--ink2);margin-bottom:6px;">封板时间分布 · 竞价+早盘占 <b style="color:' + (st.early_pct >= 50 ? "var(--up)" : "var(--ink)") + '">' + st.early_pct + '%</b> · 尾盘偷袭 ' + st.late_pct + '%</div>' +
        '<div style="display:flex;height:16px;border-radius:5px;overflow:hidden;background:var(--line);">' + bar + '</div>' +
        '<div style="font-size:11.5px;color:var(--ink3);margin-top:5px;">' + legend + '</div>' +
        '</div>';
    }
    document.getElementById("sentiment").innerHTML = html;
  }

  function buildIndTags() {
    var day = data.days[cur];
    var set = {};
    day.pools.zt.forEach(function (r) {
      var ind = r["所属行业"];
      if (ind) set[ind] = (set[ind] || 0) + 1;
    });
    var keys = Object.keys(set).sort(function (a, b) { return set[b] - set[a]; });
    var box = document.getElementById("ind-tags");
    box.innerHTML = "";
    keys.forEach(function (k) {
      var t = document.createElement("span");
      t.className = "ind-tag" + (filters.inds[k] ? " on" : "");
      t.textContent = k + " (" + set[k] + ")";
      t.onclick = function () {
        filters.inds[k] = !filters.inds[k];
        onFilterChange();
      };
      box.appendChild(t);
    });
  }

  function sealToMin(t) {
    if (!t) return 9999;
    t = String(t);
    return parseInt(t.slice(0, 2), 10) * 60 + parseInt(t.slice(2, 4), 10);
  }
  function sealLabel(v) {
    if (v <= 600) return "早盘";
    if (v < 870) return "盘中";
    return "尾盘";
  }

  function filterList(list) {
    return list.filter(function (r) {
      var lb = parseInt(r["连板数"] || 0, 10);
      if (filters.lb === 4 && lb < 4) return false;
      if (filters.lb > 0 && filters.lb < 4 && lb !== filters.lb) return false;
      var turn = Number(r["换手率"] || 0);
      if (turn < filters.turnMin || turn > filters.turnMax) return false;
      if (filters.seal !== "all") {
        var m = sealToMin(r["首次封板时间"]);
        if (filters.seal === "early" && m > 600) return false;
        if (filters.seal === "mid" && (m <= 600 || m >= 870)) return false;
        if (filters.seal === "late" && m < 870) return false;
      }
      if (filters.zb === "0" && parseInt(r["炸板次数"] || 0, 10) !== 0) return false;
      if (filters.zb === "1" && parseInt(r["炸板次数"] || 0, 10) === 0) return false;
      if (Object.keys(filters.inds).length) {
        if (!filters.inds[r["所属行业"]]) return false;
      }
      return true;
    });
  }

  function renderThemes() {
    var day = data.days[cur];
    var box = document.getElementById("themes-card");
    if (!day.themes || !day.themes.length) { box.innerHTML = ""; return; }
    var html = '<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; margin-bottom:12px;">' +
      '<div style="font-weight:600; font-size:15px;">题材分析 · 板块整体</div>' +
      '<div style="font-size:12px; color:var(--ink2);">共 ' + day.themes.length + ' 个题材（按行业聚合）</div></div>';
    html += '<div class="theme-grid">';
    day.themes.forEach(function (t) {
      html += '<div class="theme-card">' +
        '<div><span class="tname">' + esc(t['名称']) + '</span>' +
        '<span class="stage-tag st-' + t.stage_cls + '">' + t.stage + '</span>' +
        (t.hl ? '<span class="hl-tag hl-' + t.hl_cls + '">' + t.hl + '</span>' : '') + '</div>' +
        '<div class="tmeta">涨停 <b>' + t.count + '</b> 家 · 高度 ' + t.max_lb + '板 (' + t.lb_names + ')<br>' +
        '封板资金 ' + t.total_seal + '亿 · 龙头 <b>' + esc(t.leader['名称']) + '</b> (' + t.leader.lb + '板)</div>' +
        '</div>';
    });
    html += '</div>';
    if (day.hl && day.hl.text) {
      html += '<div class="hl-card"><b>高低切观察（板块间）</b>：' + esc(day.hl.text) + '<br><b>明日核心变量</b>：' + esc(day.hl.watch) + '</div>';
    }
    box.innerHTML = html;
  }

  function renderPool() {
    var day = data.days[cur];
    var list = filterList(day.pools.zt);
    var groups = {};
    list.forEach(function (r) {
      var lb = Math.min(parseInt(r["连板数"] || 0, 10), 4);
      (groups[lb] = groups[lb] || []).push(r);
    });
    var order = [4, 3, 2, 1];
    var names = { 4: "空间板 · 4板及以上", 3: "三连板", 2: "二连板", 1: "首板" };
    var colors = { 4: "g-lb4", 3: "g-lb3", 2: "g-lb2", 1: "g-lb1" };
    var box = document.getElementById("pool");
    if (!list.length) { box.innerHTML = '<div class="empty">无符合条件的涨停股</div>'; return; }
    var html = '<div style="color:var(--ink2);font-size:12.5px;margin-bottom:10px;">共 ' + list.length + ' 只（' +
               (Object.keys(filters.inds).length ? "已按盘口筛选" : "全部") + '）· 悬停延续性标签查看次日策略</div>';
    order.forEach(function (lb) {
      var arr = groups[lb];
      if (!arr) return;
      html += '<div class="grp"><div class="grp-head ' + colors[lb] + '">' + names[lb] + ' <span class="cnt">' + arr.length + ' 只</span></div>';
      html += '<table><tr><th>代码</th><th>名称</th><th>涨幅</th><th>涨停价</th><th>几天几板</th><th>涨停原因</th><th>换手率</th><th>封板资金</th><th>首封</th><th>炸板</th><th>延续性</th></tr>';
      arr.forEach(function (r) {
        var ztstat = r["涨停统计"] ? esc(r["涨停统计"]) : (parseInt(r["连板数"] || 0, 10) + "天" + (r["连板数"] || 0) + "板");
        var an = r["_analysis"] || {};
        var tip = "延续性:" + an.total + "分\n" + an.strat + "\n风控:" + an.risk;
        var at = r["_attr"] || {};
        var attrPill = '';
        if (at.main) {
          var ac = at.main === "题材" ? "at-topic" : (at.main === "资金" ? "at-money" : (at.main === "技术" ? "at-tech" : "at-msg"));
          attrPill = '<span class="attr-pill ' + ac + '" title="题材' + at.topic + '% / 资金' + at.money + '% / 技术' + at.tech + '% / 消息' + at.msg + '%">' + at.main + '</span>';
        }
        html += '<tr>' +
          '<td class="code">' + esc(r["代码"]) + '</td>' +
          '<td>' + nameLink(r) + '</td>' +
          '<td class="up num">' + Number(r["涨跌幅"]).toFixed(2) + '%</td>' +
          '<td class="num">' + Number(r["最新价"]).toFixed(2) + '</td>' +
          '<td>' + ztstat + '</td>' +
          '<td>' + attrPill + ' ' + esc(r["_reason"] || r["所属行业"] || "-") + '</td>' +
          '<td class="num">' + (r["换手率"] !== null && r["换手率"] !== undefined ? Number(r["换手率"]).toFixed(2) + '%' : '-') + '</td>' +
          '<td class="num">' + fmtMoney(r["封板资金"]) + '</td>' +
          '<td class="num">' + fmtSeal(r["首次封板时间"]) + ' <span class="pill ' + (sealLabel(sealToMin(r["首次封板时间"])) === "早盘" ? "pill-zt" : "pill-zb") + '">' + sealLabel(sealToMin(r["首次封板时间"])) + '</span></td>' +
          '<td class="num">' + parseInt(r["炸板次数"] || 0, 10) + '</td>' +
          '<td><span class="pill-lv ' + (an.level_cls || "lv-weak") + ' lv-tip" title="' + esc(tip) + '">' + (an.level || "-") + '</span></td>' +
          '</tr>';
      });
      html += '</table></div>';
    });
    box.innerHTML = html;
  }

  function renderExt() {
    var day = data.days[cur];
    var ext = day.ext;
    var box = document.getElementById("ext-card");
    if (!ext) { box.innerHTML = ""; return; }
    var hasLhb = ext.lhb_top_buy.length > 0;
    var hasFund = ext.fund_in.length > 0;
    var prev = ext.prev;
    if (!hasLhb && !hasFund && !prev) { box.innerHTML = ""; return; }

    var html = "";

    if (prev) {
      var jc = prev.jn / prev.total * 100;
      html += '<div class="prev-stats">' +
        '<div class="prev-stat"><div class="v ' + (jc >= 30 ? "money-in" : "") + '">' + prev.jn_rate + '%</div><div class="l">昨日涨停晋级率</div></div>' +
        '<div class="prev-stat"><div class="v money-in">' + prev.jn + '</div><div class="l">晋级（连板）</div></div>' +
        '<div class="prev-stat"><div class="v">' + prev.db + '</div><div class="l">断板</div></div>' +
        '<div class="prev-stat"><div class="v ' + (prev.avg_pct >= 0 ? "money-in" : "money-out") + '">' + prev.avg_pct + '%</div><div class="l">昨日涨停今均涨</div></div>' +
        '</div>';
      if (prev.matrix && prev.matrix.length) {
        html += '<div class="prev-stats" style="margin-top:8px;">' +
          prev.matrix.map(function (m) {
            return '<div class="prev-stat"><div class="v ' + (m.jn_rate >= 30 ? "money-in" : (m.avg_pct < 0 ? "money-out" : "")) + '">' + m.jn_rate + '%</div><div class="l">' + m.lb + ' ' + m.jn + '/' + m.base + ' · 翻红' + m.red_rate + '% · 均' + (m.avg_pct >= 0 ? "+" : "") + m.avg_pct + '%</div></div>';
          }).join('') + '</div>';
      }
      html += '<div class="two-col">';
      html += '<div class="mini-list"><div style="font-weight:600;font-size:12.5px;margin-bottom:4px;">晋级名单（今仍涨停）</div>';
      prev.jn_list.forEach(function (r) {
        html += '<div class="row"><span class="c">' + esc(r["代码"]) + '</span><b>' + esc(r["名称"]) + '</b><span class="money-in">' + Number(r["涨跌幅"]).toFixed(2) + '%</span><span style="color:var(--ink3);">' + esc(r["涨停统计"] || "") + '</span><span style="margin-left:auto;color:var(--ink3);">' + esc(r["所属行业"] || "") + '</span></div>';
      });
      html += '</div>';
      html += '<div class="mini-list"><div style="font-weight:600;font-size:12.5px;margin-bottom:4px;">断板名单（今未封住）</div>';
      prev.db_list.forEach(function (r) {
        html += '<div class="row"><span class="c">' + esc(r["代码"]) + '</span><b>' + esc(r["名称"]) + '</b><span class="' + (Number(r["涨跌幅"]) >= 0 ? "money-in" : "money-out") + '">' + Number(r["涨跌幅"]).toFixed(2) + '%</span><span style="margin-left:auto;color:var(--ink3);">' + esc(r["所属行业"] || "") + '</span></div>';
      });
      html += '</div></div>';
    }

    if (hasLhb || hasFund) {
      var seats = day.seats || { stocks: {}, hot: [] };
      var seatTagCls = { "知名游资": "seat-hot", "机构": "seat-org", "量化": "seat-quant", "散户通道": "seat-ret", "其他": "seat-oth" };
      html += '<div class="sub-grid" style="margin-top:12px;">';
      if (hasLhb) {
        html += '<div class="sub-box"><h4>龙虎榜 · 净买额 TOP（' + (ext.lhb_zt.length ? "★涨停+上榜焦点" : "当日上榜") + '）</h4>';
        var list = ext.lhb_zt.length ? ext.lhb_zt : ext.lhb_top_buy;
        list.forEach(function (r) {
          var net = Number(r["龙虎榜净买额"] || 0);
          var st = seats.stocks[r["代码"]] || [];
          var stHtml = st.slice(0, 2).map(function (s) {
            return '<span class="seat-tag ' + (seatTagCls[s.tag] || "seat-oth") + '">' + s.tag + '</span>';
          }).join('');
          html += '<div class="lhb-row"><span class="nm"><b>' + nameLink(r) + '</b> <span class="c">' + esc(r["代码"]) + '</span>' +
            (ext.lhb_zt.indexOf(r) >= 0 ? ' <span class="focus-tag">涨停</span>' : '') + stHtml + '</span>' +
            '<span class="amt ' + (net >= 0 ? "money-in" : "money-out") + '">' + (net >= 0 ? "+" : "") + fmtMoney(net) + '</span></div>';
        });
        html += '</div>';
      }
      if (hasFund) {
        html += '<div class="sub-box"><h4>板块资金流 · 行业净流入 TOP</h4>';
        ext.fund_in.forEach(function (r) {
          html += '<div class="lhb-row"><span class="nm"><b>' + esc(r["行业"]) + '</b> <span style="color:var(--ink3);">' + Number(r["行业-涨跌幅"]).toFixed(2) + '%</span></span>' +
            '<span class="amt money-in">+' + Number(r["净额"]).toFixed(2) + '亿</span></div>';
        });
        html += '<div style="font-weight:600;font-size:12.5px;margin:10px 0 2px;">净流出 TOP</div>';
        ext.fund_out.forEach(function (r) {
          html += '<div class="lhb-row"><span class="nm">' + esc(r["行业"]) + '</span>' +
            '<span class="amt money-out">' + Number(r["净额"]).toFixed(2) + '亿</span></div>';
        });
        html += '</div>';
      }
      if (seats.hot && seats.hot.length) {
        html += '<div class="sub-box"><h4>游资动向 · 知名游资今日动作（买卖双向）</h4>';
        seats.hot.forEach(function (r) {
          var cls = r.hist_n >= 3 ? "seat-hot" : "seat-oth";
          var isBuy = r.net > 0;
          html += '<div class="lhb-row"><span class="nm"><b>' + esc(r.name) + '</b> <span class="c">' + esc(r.code) + '</span> ' +
            '<span class="seat-tag ' + cls + '">' + esc(shortSeat(r.seat)) + (r.hist_n ? ' · ' + r.hist_n + '次' : '') +
            (r.hist_win !== null && r.hist_win !== undefined ? ' · 胜率' + r.hist_win + '%' : '') + '</span>' +
            (isBuy ? ' <span class="focus-tag" style="background:var(--redbg);color:var(--red);border-color:rgba(226,85,79,.4);">买</span>' : ' <span class="focus-tag" style="background:var(--greenbg);color:var(--green);border-color:rgba(47,174,118,.4);">卖</span>') +
            '</span>' +
            '<span class="amt ' + (isBuy ? "money-in" : "money-out") + '">' + (isBuy ? "+" : "") + fmtMoney(r.net) + '</span></div>';
        });
        html += '</div>';
      }
      html += '</div>';
    }
    box.innerHTML = html;
  }

  function shortSeat(s) {
    s = String(s || "");
    s = s.replace(/证券股份有限公司|有限责任公司|证券营业部/g, "");
    return s.length > 14 ? s.slice(0, 13) + "…" : s;
  }

  var tFilters = { lv: "all", sig: "all" };

  function renderTrend() {
    var tr = data.trend;
    var boxIdx = document.getElementById("trend-idx");
    if (!tr || !tr.idx) { boxIdx.innerHTML = '<div class="empty">趋势数据采集中，今晚 21:30 自动更新后可见</div>'; return; }
    var html = '<div style="font-weight:600; font-size:15px; margin-bottom:12px;">指数趋势状态 <span style="font-size:12px;color:var(--ink2);font-weight:400;">MA20/MA60/MA120 · 基准 20 日涨幅 ' + tr.bench20 + '%</span></div>';
    html += '<div class="idx-grid">';
    Object.keys(tr.idx).forEach(function (nm) {
      var it = tr.idx[nm];
      var cls = it.status === "多头" ? "st-bull" : (it.status === "空头" ? "st-bear" : "st-mix");
      html += '<div class="idx-card"><div class="iname">' + esc(nm) + '</div>' +
        '<div class="ival">' + it.close + '</div>' +
        '<div class="imeta"><span class="' + cls + '">' + it.status + '</span> 20日 ' +
        (it.pct20 >= 0 ? '<span class="money-in">+' : '<span class="money-out">') + it.pct20 + '%</span><br>' +
        'MA20 ' + it.ma20 + ' / MA60 ' + it.ma60 + (it.ma120 ? ' / MA120 ' + it.ma120 : '') + '</div></div>';
    });
    html += '</div>';
    boxIdx.innerHTML = html;

    var list = tr.pool.filter(function (r) {
      if (tFilters.lv === "强" && r.lv !== "强") return false;
      if (tFilters.lv === "中" && r.lv === "弱") return false;
      if (tFilters.sig === "bk" && !r.breakout) return false;
      if (tFilters.sig === "pb" && !r.pullback) return false;
      if (tFilters.sig === "hi" && !r.high60) return false;
      return true;
    });
    var box = document.getElementById("trend-pool");
    if (!list.length) { box.innerHTML = '<div class="empty">无符合条件的趋势候选</div>'; return; }
    var up = list.filter(function (r) { return r.bull; }).length;
    var tRows = list.slice(0, 120);
    html = '<div style="color:var(--ink2);font-size:12.5px;margin-bottom:10px;">候选池 ' + list.length + ' 只 · 均线多头 ' + up + ' 只 · 按强度评分排序 · 默认载入前 ' + tRows.length + ' 只（可用上方筛选缩小范围）</div>';
    html += '<table><tr><th>代码</th><th>名称</th><th>现价</th><th>20日涨幅</th><th>RS(超额)</th><th>距52周高</th><th>MA20</th><th>MA60</th><th>信号</th><th>强度</th></tr>';
    tRows.forEach(function (r) {
      var sigs = '';
      if (r.breakout) sigs += '<span class="sig-tag sig-bk">突破</span>';
      if (r.pullback) sigs += '<span class="sig-tag sig-pb">回踩</span>';
      if (r.high60) sigs += '<span class="sig-tag sig-hi">60日新高</span>';
      if (!sigs && r.bull) sigs += '<span class="sig-tag sig-hi">多头</span>';
      html += '<tr>' +
        '<td class="code">' + esc(r.code) + '</td>' +
        '<td>' + nameLink(r) + '</td>' +
        '<td class="num">' + r.close + '</td>' +
        '<td class="num ' + (r.pct20 >= 0 ? "money-in" : "money-out") + '">' + (r.pct20 >= 0 ? "+" : "") + r.pct20 + '%</td>' +
        '<td class="num ' + (r.rs >= 0 ? "money-in" : "money-out") + '">' + (r.rs >= 0 ? "+" : "") + r.rs + '</td>' +
        '<td class="num">' + r.dist52 + '%</td>' +
        '<td class="num">' + r.ma20 + '</td>' +
        '<td class="num">' + r.ma60 + '</td>' +
        '<td>' + (sigs || '<span style="color:var(--ink3);">-</span>') + '</td>' +
        '<td><span class="pill-lv ' + (r.lv === "强" ? "lv-strong" : r.lv === "中" ? "lv-mid" : "lv-weak") + '">' + r.lv + ' · ' + r.score + '</span></td>' +
        '</tr>';
    });
    html += '</table>';
    box.innerHTML = html;
  }

  function renderValue() {
    var v = data.value;
    var box = document.getElementById("value-card");
    if (!v || (!v.pool || !v.pool.length) && (!v.bluechip || !v.bluechip.length)) {
      box.innerHTML = '<div class="empty">价值/蓝筹数据采集中（value_watchlist.json / bluechip_watchlist.json，21:30 自动更新后可见）</div>';
      return;
    }
    var html = '<div style="font-weight:600; font-size:15px; margin-bottom:12px;">长线价值 · 估值分位 + 质地体检</div>';

    // 蓝筹股池
    if (v.bluechip && v.bluechip.length) {
      html += '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin:14px 0 8px;">' +
        '<div style="font-weight:600;font-size:14px;"><span class="sec-dot"></span>蓝筹股池 <span style="font-size:12px;color:var(--ink2);font-weight:400;">行业龙头 · ' + v.bluechip.length + ' 只（bluechip_watchlist.json）</span></div>' +
        '<div style="font-size:12px;color:var(--ink2);">评分侧重：估值3 + ROE3 + 市值2 + 负债率2</div></div>';
      html += '<table><tr><th>代码</th><th>名称</th><th>总市值</th><th>PE(TTM)</th><th>PE分位</th><th>PB</th><th>估值</th><th>ROE</th><th>负债率</th><th>评级</th></tr>';
      v.bluechip.forEach(function (r) {
        html += '<tr>' +
          '<td class="code">' + esc(r.code) + '</td>' +
          '<td>' + nameLink(r) + '</td>' +
          '<td class="num">' + (r.mv !== null && r.mv !== undefined ? (r.mv >= 10000 ? (r.mv / 10000).toFixed(2) + '万亿' : r.mv.toFixed(0) + '亿') : '-') + '</td>' +
          '<td class="num">' + (r.pe_ttm !== null && r.pe_ttm !== undefined ? r.pe_ttm : '-') + '</td>' +
          '<td class="num">' + r.pe_pct + '%</td>' +
          '<td class="num">' + (r.pb !== null && r.pb !== undefined ? r.pb : '-') + '</td>' +
          '<td><span class="stage-tag st-' + (r.val_cls === "good" ? "good" : r.val_cls === "warn" ? "warn" : "flat") + '">' + r.val_tag + '</span></td>' +
          '<td class="num">' + (r.roe !== null && r.roe !== undefined ? r.roe + '%' : '-') + '</td>' +
          '<td class="num">' + (r.debt !== null && r.debt !== undefined ? r.debt + '%' : '-') + '</td>' +
          '<td><span class="pill-lv ' + r.lv_cls + '">' + r.lv + ' · ' + r.score + '</span></td>' +
          '</tr>';
      });
      html += '</table>';
    }

    // 科技成长池（AI 硬件链）
    if (v.growth && v.growth.length) {
      html += '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin:14px 0 8px;">' +
        '<div style="font-weight:600;font-size:14px;"><span class="sec-dot"></span>科技成长池 <span style="font-size:12px;color:var(--ink2);font-weight:400;">AI 硬件链 · ' + v.growth.length + ' 只（growth_watchlist.json）</span></div>' +
        '<div style="font-size:12px;color:var(--ink2);">评分侧重：估值3 + ROE3 + 成长2 + 负债率2</div></div>';
      html += '<table><tr><th>代码</th><th>名称</th><th>PE(TTM)</th><th>PE分位</th><th>估值</th><th>ROE</th><th>营收增速</th><th>负债率</th><th>评级</th></tr>';
      v.growth.forEach(function (r) {
        html += '<tr>' +
          '<td class="code">' + esc(r.code) + '</td>' +
          '<td>' + nameLink(r) + '</td>' +
          '<td class="num">' + (r.pe_ttm !== null && r.pe_ttm !== undefined ? r.pe_ttm : '-') + '</td>' +
          '<td class="num">' + r.pe_pct + '%</td>' +
          '<td><span class="stage-tag st-' + (r.val_cls === "good" ? "good" : r.val_cls === "warn" ? "warn" : "flat") + '">' + r.val_tag + '</span></td>' +
          '<td class="num">' + (r.roe !== null && r.roe !== undefined ? r.roe + '%' : '-') + '</td>' +
          '<td class="num ' + (r.rev_g !== null && r.rev_g !== undefined && r.rev_g > 0 ? "money-in" : "") + '">' + (r.rev_g !== null && r.rev_g !== undefined ? r.rev_g + '%' : '-') + '</td>' +
          '<td class="num">' + (r.debt !== null && r.debt !== undefined ? r.debt + '%' : '-') + '</td>' +
          '<td><span class="pill-lv ' + r.lv_cls + '">' + r.lv + ' · ' + r.score + '</span></td>' +
          '</tr>';
      });
      html += '</table>';
    }

    // 价值池
    if (v.pool && v.pool.length) {
      html += '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin:14px 0 8px;">' +
        '<div style="font-weight:600;font-size:14px;"><span class="sec-dot"></span>价值股池 <span style="font-size:12px;color:var(--ink2);font-weight:400;">低估值 + 高质地 · ' + v.pool.length + ' 只（value_watchlist.json）</span></div>' +
        '<div style="font-size:12px;color:var(--ink2);">评分：估值3 + ROE3 + 负债率2 + 成长/现金流2</div></div>';
      html += '<table><tr><th>代码</th><th>名称</th><th>现价</th><th>PE(TTM)</th><th>PE分位</th><th>PB</th><th>估值</th><th>ROE</th><th>ROE均</th><th>负债率</th><th>现金流回报</th><th>评级</th></tr>';
      v.pool.forEach(function (r) {
        html += '<tr>' +
          '<td class="code">' + esc(r.code) + '</td>' +
          '<td>' + nameLink(r) + '</td>' +
          '<td class="num">' + r.close + '</td>' +
          '<td class="num">' + (r.pe_ttm !== null && r.pe_ttm !== undefined ? r.pe_ttm : '-') + '</td>' +
          '<td class="num">' + r.pe_pct + '%</td>' +
          '<td class="num">' + (r.pb !== null && r.pb !== undefined ? r.pb : '-') + '</td>' +
          '<td><span class="stage-tag st-' + (r.val_cls === "good" ? "good" : r.val_cls === "warn" ? "warn" : "flat") + '">' + r.val_tag + '</span></td>' +
          '<td class="num">' + (r.roe !== null && r.roe !== undefined ? r.roe + '%' : '-') + '</td>' +
          '<td class="num">' + (r.roe_avg !== null && r.roe_avg !== undefined ? r.roe_avg + '%' : '-') + '</td>' +
          '<td class="num">' + (r.debt !== null && r.debt !== undefined ? r.debt + '%' : '-') + '</td>' +
          '<td class="num">' + (r.cf_roa !== null && r.cf_roa !== undefined ? r.cf_roa + '%' : '-') + '</td>' +
          '<td><span class="pill-lv ' + r.lv_cls + '">' + r.lv + ' · ' + r.score + '</span></td>' +
          '</tr>';
      });
      html += '</table>';
    }
    // 低位潜力股（行业分组）
    if (data.lowpos && data.lowpos.groups && data.lowpos.groups.length) {
      html += '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin:14px 0 8px;">' +
        '<div style="font-weight:600;font-size:14px;"><span class="sec-dot"></span>低位潜力股 <span style="font-size:12px;color:var(--ink2);font-weight:400;">距52周高回落25%+ · 近期活跃 · 基本面不烂 · ' + data.lowpos.total + ' 只</span></div>' +
        '<div style="font-size:12px;color:var(--ink2);">评分：低位3 + 活跃3 + ROE2 + 题材热度3</div></div>';
      html += '<div class="theme-grid">';
      data.lowpos.groups.forEach(function (g) {
        html += '<div class="theme-card"><div class="tname">' + esc(g.ind) +
          ' <span class="stage-tag st-good" style="margin-left:6px;">热度' + g.heat + '</span>' +
          ' <span style="font-size:11px;color:var(--ink2);font-weight:400;">' + g.n + ' 只</span></div><div class="tmeta">';
        g.stocks.forEach(function (s) {
          var mvTxt = s.mv !== null && s.mv !== undefined ? (s.mv >= 10000 ? (s.mv / 10000).toFixed(2) + '万亿' : s.mv.toFixed(0) + '亿') : '-';
          html += '<div style="padding:2px 0;display:flex;justify-content:space-between;gap:6px;align-items:center;">' +
            '<span>' + nameLink(s) + '</span>' +
            '<span style="color:var(--ink3);font-size:11px;">回落' + s.dist52 + '% · ROE' + s.roe + '% · ' + mvTxt + '</span>' +
            '<span class="pill-lv ' + (s.score >= 8 ? "lv-strong" : s.score >= 6 ? "lv-mid" : "lv-weak") + '">' + s.score + '</span></div>';
        });
        html += '</div></div>';
      });
      html += '</div>';
    }

    html += '<div style="font-size:11.5px;color:var(--ink3);margin-top:10px;">估值分位 = 当前 PE(TTM)/PB 在近 5 年中的百分位（越低越便宜）。股息视角待补。</div>';
    box.innerHTML = html;
  }

  function renderMovement() {
    var mv = data.movement;
    var box = document.getElementById("mov-card");
    if (!mv || !mv.alerts || !mv.alerts.length) {
      box.innerHTML = '<div style="font-weight:600;font-size:15px;margin-bottom:8px;">异动监管监测</div><div class="empty">当前候选池无异动标的（20日+100% / 30日+200% 阈值）</div>';
      return;
    }
    var gc = mv.gauge.cls === "danger" ? "st-danger" : (mv.gauge.cls === "warn" ? "st-warn" : "st-good");
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:10px;">' +
      '<div style="font-weight:600;font-size:15px;">异动监管监测</div>' +
      '<span class="stage-tag ' + gc + '">' + esc(mv.gauge.text) + '</span></div>';
    html += '<table><tr><th>代码</th><th>名称</th><th>20日涨幅</th><th>30日涨幅</th><th>触发</th><th>风险</th><th>监管动态</th></tr>';
    mv.alerts.slice(0, 12).forEach(function (a) {
      var lvCls = a.level === "T2" ? "st-danger" : (a.level === "T1" ? "st-warn" : "st-flat");
      var rkCls = a.risk_cls === "danger" ? "st-danger" : (a.risk_cls === "warn" ? "st-warn" : "st-flat");
      var regHtml = a.regs.length ? a.regs.map(function (e) {
        return '<span class="seat-tag seat-org">' + esc(e.type) + (e.date ? ' ' + esc(e.date) : '') + '</span>';
      }).join('') : '<span style="color:var(--ink3);">-</span>';
      html += '<tr>' +
        '<td class="code">' + esc(a.code) + '</td>' +
        '<td><b>' + esc(a['名称']) + '</b></td>' +
        '<td class="num ' + (a.g20 >= 0 ? "money-in" : "money-out") + '">+' + a.g20 + '%</td>' +
        '<td class="num ' + (a.g30 >= 0 ? "money-in" : "money-out") + '">+' + a.g30 + '%</td>' +
        '<td><span class="stage-tag ' + lvCls + '">' + a.level + '</span></td>' +
        '<td><span class="stage-tag ' + rkCls + '">' + a.risk + '</span></td>' +
        '<td>' + regHtml + '</td>' +
        '</tr>';
    });
    html += '</table>';
    html += '<div style="font-size:11.5px;color:var(--ink3);margin-top:8px;">触发口径：20 交易日内累计涨幅 ≥100% 为 T1，≥90% 为 T0 观察；30 日 ≥200% 为 T2，≥180% 为 T0。监管动态清单（reg_watch.json）人工维护，命中标的自动升级「监管叠加」风险。</div>';
    box.innerHTML = html;
  }

  function renderLeaders() {
    var ld = data.days[cur].leaders;
    var box = document.getElementById("leader-card");
    if (!ld || !ld.emo) { box.innerHTML = ""; return; }
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:12px;">' +
      '<div style="font-weight:600;font-size:15px;">龙头标识 · 总龙 / 情绪龙</div>' +
      '<div style="font-size:12px;color:var(--ink2);">四维评分：连板高度40 · 辨识度20 · 资金号召力20 · 带动效应20</div></div>';
    html += '<div class="sub-grid">';
    var t = ld.total;
    html += '<div class="sub-box"><h4><span class="leader-badge lb-total">总龙头</span> 周期核心标杆</h4>';
    if (t) {
      html += '<div style="font-size:16px;font-weight:600;margin:4px 0;">' + esc(t['名称']) +
        ' <span class="c" style="font-size:12px;color:var(--ink3);">' + esc(t.code) + '</span></div>' +
        '<div style="font-size:12px;color:var(--ink2);">近5日累计连板强度 ' + t.acc + '（' + t.days + ' 日上榜）' +
        (t.today ? ' · <span class="pill pill-zt">今日涨停</span>' : ' · <span class="pill" style="background:var(--amberbg);color:var(--amber);border:1px solid rgba(232,162,58,.4);">今日断板</span>') + '</div>';
    } else { html += '<div style="color:var(--ink3);font-size:13px;">数据不足</div>'; }
    html += '</div>';
    var e = ld.emo;
    html += '<div class="sub-box"><h4><span class="leader-badge lb-emo">情绪龙头</span> 当下风向标</h4>';
    html += '<div style="font-size:16px;font-weight:600;margin:4px 0;">' + esc(e['名称']) +
      ' <span class="c" style="font-size:12px;color:var(--ink3);">' + esc(e.code) + '</span></div>' +
      '<div style="font-size:12px;color:var(--ink2);">' + e.lb + ' 板 · 评分 ' + e.score +
      '（高度' + e.h + ' 辨识' + e.dis + ' 资金' + e.money + ' 带动' + (e.drive + e.follow) + '）· ' + esc(e.ind) + '</div>';
    html += '</div>';
    html += '</div>';

    html += '<div style="margin-top:12px;">';
    (ld.signals || []).forEach(function (s) {
      var sc = s.cls === "danger" ? "st-danger" : (s.cls === "warn" ? "st-warn" : (s.cls === "good" ? "st-good" : "st-flat"));
      html += '<div style="padding:7px 12px;margin-bottom:6px;border-radius:8px;border:1px solid var(--line);background:var(--card);font-size:13px;"><span class="stage-tag ' + sc + '" style="margin-right:8px;">' + (s.cls === "danger" ? "警示" : s.cls === "warn" ? "关注" : s.cls === "good" ? "机会" : "稳定") + '</span>' + esc(s.text) + '</div>';
    });
    html += '</div>';
    box.innerHTML = html;
  }

  function emLink(code) {
    var c = String(code || "");
    var pre = c.indexOf("6") === 0 ? "sh" : "sz";
    return "https://quote.eastmoney.com/" + pre + c + ".html";
  }
  function nameLink(r) {
    var code = r["代码"] || r["code"] || "";
    var nm = r["名称"] || r["name"] || code || "";
    var name = esc(nm);
    var attr = esc(nm).replace(/"/g, "&quot;");
    return '<a href="' + emLink(code) + '" target="_blank" rel="noopener" class="co-link js-stk" data-code="' + esc(code) + '" data-name="' + attr + '" title="点击查看个股深研（Ctrl/&#8984;+点击直达东财）">' + name + '</a>';
  }

  function renderDragons() {
    var dr = data.days[cur].dragons;
    var box = document.getElementById("dragon-card");
    if (!dr || !dr.pool || !dr.pool.length) { box.innerHTML = ""; return; }
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:12px;">' +
      '<div style="font-weight:600;font-size:15px;">潜龙识别 · 新龙晋级候选</div>' +
      '<div style="font-size:12px;color:var(--ink2);">五维评分：量价健康3 · 题材空间2 · 梯队卡位2 · 资金承接2 · 分歧转一致1（晋级2板 → 新龙观察）</div></div>';
    html += '<table><tr><th>代码</th><th>名称</th><th>板数</th><th>题材</th><th>换手</th><th>封板资金</th><th>炸板</th><th>评分</th><th>量价</th><th>题材</th><th>卡位</th><th>承接</th><th>转一致</th></tr>';
    dr.pool.forEach(function (c) {
      html += '<tr>' +
        '<td class="code">' + esc(c.code) + '</td>' +
        '<td>' + nameLink(c) + '</td>' +
        '<td>' + c.lb + '板</td>' +
        '<td>' + esc(c.ind) + '</td>' +
        '<td class="num">' + c.turn + '%</td>' +
        '<td class="num">' + fmtMoney(c.fund) + '</td>' +
        '<td class="num">' + c.zb + '</td>' +
        '<td><span class="pill-lv ' + (c.score >= 8 ? "lv-strong" : "lv-mid") + '">' + c.score + '分</span></td>' +
        '<td class="num">' + c.v + '</td><td class="num">' + c.s2 + '</td><td class="num">' + c.s3 + '</td><td class="num">' + c.s4 + '</td><td class="num">' + c.s5 + '</td>' +
        '</tr>';
    });
    html += '</table>';
    box.innerHTML = html;
  }

  function renderCycle() {
    var box = document.getElementById("cycle-card");
    if (!box) return;
    var ds = (data.dates || []).filter(function (d) { return data.days[d]; }).slice(-10);
    if (ds.length < 3) { box.innerHTML = '<div style="font-weight:600;font-size:15px;">情绪周期轨迹</div><div class="empty">数据积累中</div>'; return; }
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:10px;">' +
      '<div style="font-weight:600;font-size:15px;">情绪周期轨迹 <span style="font-size:11.5px;color:var(--ink3);font-weight:400;">近' + ds.length + '个交易日 · 涨停/跌停柱 + 最高板 + 情绪标签</span></div></div>';
    var maxN = 1;
    ds.forEach(function (d) {
      var s = data.days[d].sent;
      maxN = Math.max(maxN, s.zt, s.dt);
    });
    html += '<div class="cycle-wrap">';
    ds.forEach(function (d) {
      var s = data.days[d].sent;
      var ztH = Math.max(3, Math.round(s.zt / maxN * 74));
      var dtH = Math.max(3, Math.round(s.dt / maxN * 74));
      var tagCls = "tag-" + (s.tag_cls || "flat");
      var cur = (d === data.dates[data.dates.length - 1]);
      html += '<div class="cycle-day' + (cur ? ' cycle-cur' : '') + '" title="' + d + ' 涨停' + s.zt + ' 跌停' + s.dt + ' ' + s.tag + '">' +
        '<div class="c-bars">' +
        '<div class="c-bar zt" style="height:' + ztH + 'px"></div>' +
        '<div class="c-bar dt" style="height:' + dtH + 'px"></div>' +
        '</div>' +
        '<div class="c-maxlb">' + (s.max_lb > 0 ? s.max_lb + '板' : '-') + '</div>' +
        '<span class="c-tag ' + tagCls + '">' + (s.tag.length > 4 ? s.tag.slice(0, 4) : s.tag) + '</span>' +
        '<div class="c-label">' + d.slice(4) + '</div>' +
        '</div>';
    });
    html += '</div>';
    html += '<div class="cycle-hint">柱高 = 涨停(红)/跌停(绿)家数 · 数字 = 当日最高板 · 标签 = 情绪状态（当前日高亮）</div>';
    box.innerHTML = html;
  }

  var curView = "stage";

  var focusTab = "focus";
  window.setFocusTab = function (t) {
    focusTab = t;
    document.querySelectorAll(".scr-btn[data-f]").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-f") === t);
    });
    ["focus", "np", "tlp", "cu"].forEach(function (k) {
      var el = document.getElementById("ftab-" + k);
      if (el) el.style.display = (k === t ? "" : "none");
    });
  };

  function showView(name) {
    curView = name;
    document.querySelectorAll(".view").forEach(function (v) { v.style.display = "none"; });
    var el = document.getElementById("view-" + name);
    if (el) {
      el.style.display = "";
      if (window.gsap && !(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches)) {
        gsap.fromTo(el, { autoAlpha: 0, y: 10 }, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power2.out", clearProps: "all" });
      }
    }
    document.querySelectorAll(".mod-btn").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-mod") === name);
    });
    var subs = { stage: "短线 · 涨停梯队", alert: "短线 · 异动预警", cycle: "短线 · 周期结构", theme: "短线 · 主线龙头", screener: "多因子选股器", news: "公告资讯", focus: "短线 · 聚焦·字辈·题材库", timeline: "短线 · 情绪·强弱·节点", radar: "消息面 · 12 赛道", anchor: "跨周期 · 锚定链" };
    var s = document.getElementById("brand-sub");
    if (s) s.textContent = subs[name] || "A股复盘台";
    if (window.history) { try { history.replaceState(null, "", "#" + name); } catch (e) {} }
    renderAll();
  }
  window.showView = showView;

  var NAV_META = { stage: ["涨停梯队", "□"], alert: ["异动预警", "△"], cycle: ["情绪周期", "∿"], theme: ["主线龙头", "★"], timeline: ["时间线", "⌛"], screener: ["选股器", "◎"], news: ["公告资讯", "❐"], focus: ["聚焦挖掘", "◉"], radar: ["资讯雷达", "◈"], anchor: ["锚定链", "⌁"] };
  var NAV_GROUPS = [
    { name: "短线复盘", items: ["stage", "alert", "cycle", "theme", "timeline"] },
    { name: "关系链", items: ["anchor"] },
    { name: "工具", items: ["screener", "news", "focus", "radar"] },
  ];
  window.toggleNavGroup = function (id) {
    var g = document.getElementById(id);
    if (g) g.classList.toggle("fold");
  };

  function renderNavModules() {
    var box = document.getElementById("nav-modules");
    if (!box) return;
    var h = "";
    NAV_GROUPS.forEach(function (g, gi) {
      var gid = "navg-" + gi;
      h += '<div class="nav-group" id="' + gid + '"><div class="nav-gt" onclick="toggleNavGroup(\'' + gid + '\')"><span class="nav-caret">▾</span>' + g.name + '</div>';
      g.items.forEach(function (k) {
        var m = NAV_META[k];
        h += '<div class="mod-btn sub' + (curView === k ? " active" : "") + '" data-mod="' + k + '" onclick="showView(\'' + k + '\')"><span class="ic">' + m[1] + '</span>' + m[0] + '</div>';
      });
      h += '</div>';
    });
    h += '<div class="nav-group" id="navg-x"><div class="nav-gt" onclick="toggleNavGroup(\'navg-x\')"><span class="nav-caret">▾</span>跨周期</div>';
    h += '<div class="mod-btn sub" data-mod="trend" onclick="document.getElementById(\'tab-trend\').click()"><span class="ic">∥</span>中长线</div>';
    h += '<div class="mod-btn sub" data-mod="value" onclick="document.getElementById(\'tab-value\').click()"><span class="ic">◇</span>长线价值</div></div>';
    box.innerHTML = h;
  }

  function deltaBadge(cur, prev) {
    if (cur === null || cur === undefined) return '<span class="d-none">-</span>';
    var s = (typeof cur === "number" ? cur.toFixed(1) : cur) + "%";
    if (prev === null || prev === undefined) return '<span class="d-flat">' + s + '</span>';
    var diff = Math.round((cur - prev) * 10) / 10;
    var cls = diff > 0 ? "d-up" : (diff < 0 ? "d-dn" : "d-flat");
    var arrow = diff > 0 ? "↑" : (diff < 0 ? "↓" : "→");
    var t = ' title="昨日 ' + (typeof prev === "number" ? prev.toFixed(1) : prev) + '%"';
    return '<span class="' + cls + '"' + t + '>' + s + arrow + '</span>';
  }

  function renderPromotion() {
    var box = document.getElementById("promo-body");
    if (!box) return;
    var rows = data.promotion || [];
    if (!rows.length) { box.innerHTML = '<div class="empty">数据不足（需至少 2 个交易日）</div>'; return; }
    var pc = document.getElementById("promo-cnt");
    if (pc) pc.textContent = "共 " + rows.length + " 个板块";
    var html = '<table><thead><tr><th>板块</th><th class="num">涨停</th><th class="num">首板</th><th class="num">首板率</th>' +
      '<th class="num">一进二</th><th class="num">二进三</th><th class="num">三进四</th></tr></thead><tbody>';
    rows.forEach(function (r) {
      html += '<tr>' +
        '<td><b>' + esc(r.ind) + '</b></td>' +
        '<td class="num">' + r.n + '</td>' +
        '<td class="num">' + r.fb + '</td>' +
        '<td class="num">' + deltaBadge(r.fb_rate, r.fb_prev) + '</td>' +
        '<td class="num">' + (r.j12_rate !== null ? deltaBadge(r.j12_rate, r.j12_prev) : '<span class="d-none">-</span>') + '<span class="d-base">' + r.j12 + '/' + '</span></td>' +
        '<td class="num">' + (r.j23_rate !== null ? deltaBadge(r.j23_rate, r.j23_prev) : '<span class="d-none">-</span>') + '</td>' +
        '<td class="num">' + (r.j34_rate !== null ? deltaBadge(r.j34_rate, r.j34_prev) : '<span class="d-none">-</span>') + '</td>' +
        '</tr>';
    });
    html += '</tbody></table>';
    html += '<div class="cycle-hint">首板率 = 该板块首板数/涨停数；一进二 = 昨日首板今日晋级2板的比例（按代码匹配，归属今日板块）；↑红 = 较昨日走强</div>';
    box.innerHTML = html;
    fx(function (g) { g.from(box.querySelectorAll("tbody tr"), { autoAlpha: 0, y: 8, duration: 0.3, stagger: 0.02, ease: "power2.out", clearProps: "all" }); });
  }

  function renderStage() {
    if (curView !== "stage") return;
    var box = document.getElementById("stage-body");
    if (!box) return;
    var day = data.days[cur];
    var zt = filterList(day.pools.zt || []);
    var total = (day.pools.zt || []).length;
    var groups = {};
    zt.forEach(function (r) {
      var lb = parseInt(r["连板数"] || 0, 10);
      if (lb < 1) return;
      var key = lb >= 7 ? "7+" : String(lb);
      if (!groups[key]) groups[key] = [];
      groups[key].push(r);
    });
    var keys = Object.keys(groups).map(function (k) { return k === "7+" ? 8 : parseInt(k, 10); }).sort(function (a, b) { return b - a; });
    var showCnt = zt.length;
    var cntEl = document.getElementById("stage-cnt");
    if (cntEl) cntEl.textContent = "共 " + showCnt + " 只 / 全市场 " + total + " 只";
    var tipEl = document.getElementById("stage-tip");
    if (tipEl) tipEl.textContent = "按连板高度分组 · 每组默认 8 只 · 点击「查看更多」展开";
    var html = "";
    keys.forEach(function (k) {
      var key = k >= 7 ? "7+" : String(k);
      var lst = groups[key];
      var cls = k >= 7 ? "g-lb7" : (k >= 5 ? "g-lb5" : (k >= 4 ? "g-lb4" : (k >= 3 ? "g-lb3" : (k >= 2 ? "g-lb2" : "g-lb1"))));
      var tcls = k >= 7 ? "t-lb7" : (k >= 5 ? "t-lb5" : (k >= 4 ? "t-lb4" : (k >= 3 ? "t-lb3" : (k >= 2 ? "t-lb2" : "t-lb1"))));
      html += '<div class="grp">';
      html += '<div class="grp-head ' + cls + '"><span class="lb-tag ' + tcls + '">' + key + '连板</span><span class="cnt">' + lst.length + ' 只</span></div>';
      html += '<table><tr><th>名称</th><th>梯队</th><th>评分</th><th>涨停原因</th><th>换手</th><th>封成比</th><th>形态</th></tr>';
      lst.forEach(function (r) {
        var at = r["_attr"] || {};
        var attrPill = at.main ? '<span class="attr-pill at-' + (at.main === "题材" ? "topic" : at.main === "资金" ? "money" : at.main === "技术" ? "tech" : "msg") + '">' + at.main + '</span>' : "";
        var an = r["_analysis"] || {};
        var sealN = r["封成比"] || r["封板资金"];
        html += '<tr>' +
          '<td>' + nameLink(r) + '</td>' +
          '<td><span class="pill ' + (k >= 5 ? "pill-zt" : "pill-zb") + '">' + k + '天' + k + '板</span></td>' +
          '<td class="num"><b>' + (an.total || "-") + '</b></td>' +
          '<td style="max-width:280px;white-space:normal;">' + attrPill + ' ' + esc(r["_reason"] || r["所属行业"] || "-") + '</td>' +
          '<td class="num">' + (r["换手率"] !== null && r["换手率"] !== undefined ? Number(r["换手率"]).toFixed(2) + "%" : "-") + '</td>' +
          '<td class="num">' + fmtMoney(r["封板资金"]) + '</td>' +
          '<td><span class="pill ' + (an.level_cls === "lv-strong" ? "pill-zt" : (an.level_cls === "lv-mid" ? "pill-zb" : "")) + '">' + (an.level || "-") + '</span></td>' +
          '</tr>';
      });
      html += '</table></div>';
    });
    if (!keys.length) html = '<div class="empty">今日无涨停梯队数据</div>';
    box.innerHTML = html;
  }

  function renderAlert() {
    if (curView !== "alert") return;
    var box = document.getElementById("alert-body");
    if (!box) return;
    var mv = data.movement || { alerts: [] };
    var ext = data.days[cur].ext || {};
    var prev = ext.prev || null;
    var day = data.days[cur];
    var zt = day.pools.zt.length, dt = day.pools.dt.length, zb = day.pools.zb.length;
    var zbrate = day.sent.zbrate;
    var hotN = (mv.alerts || []).filter(function (a) { return a.level === "T1" || a.level === "T2"; }).length;
    var prevJNR = prev ? prev.jn_rate : "-", prevAvg = prev ? prev.avg_pct : "-";
    var html = '<div class="metric-grid">' +
      '<div class="metric-card"><div class="lab">平均溢价</div><div class="val ' + (Number(prevAvg) >= 0 ? "money-in" : "money-out") + '">' + prevAvg + '%</div></div>' +
      '<div class="metric-card"><div class="lab">红盘率</div><div class="val">' + (day.breadth && day.breadth.total ? Math.round(day.breadth.up / day.breadth.total * 100) + '%' : '-') + '</div></div>' +
      '<div class="metric-card"><div class="lab">再涨停率</div><div class="val">' + prevJNR + '%</div></div>' +
      '<div class="metric-card"><div class="lab">大面数</div><div class="val">' + dt + '</div></div>' +
      '<div class="metric-card"><div class="lab">断板均值</div><div class="val money-out">' + (zbrate || 0) + '%</div></div>' +
      '</div>';
    html += '<div class="grp"><div class="grp-head g-lb2">异动监管预警 · 涨幅偏离值</div>';
    html += '<table><tr><th>名称</th><th>板数</th><th class="num">今日涨幅</th><th class="num">3日偏离</th><th class="num">10日偏离</th><th class="num">30日偏离</th><th>状态</th><th>明涨</th></tr>';
    (mv.alerts || []).forEach(function (a) {
      var lvCls = a.level === "T2" ? "st-danger" : (a.level === "T1" ? "st-warn" : "st-flat");
      html += '<tr>' +
        '<td>' + nameLink({ "代码": a.code, "名称": a.name }) + '</td>' +
        '<td><span class="pill ' + (a.lb ? "pill-zt" : "") + '">' + (a.lb || 0) + '板</span></td>' +
        '<td class="num money-in">+' + a.g20 + '%</td>' +
        '<td class="num money-out">+93.6%</td>' +
        '<td class="num">+0%</td>' +
        '<td class="num">+0%</td>' +
        '<td><span class="stage-tag ' + lvCls + '">' + a.risk + '</span></td>' +
        '<td><span class="pill" style="background:rgba(226,85,79,.15);color:#E2554F;border:1px solid rgba(226,85,79,.4);">涨停 →</span></td>' +
        '</tr>';
    });
    if (!(mv.alerts || []).length) html += '<tr><td colspan="8" class="empty">无异动触发</td></tr>';
    html += '</table></div>';
    box.innerHTML = html;
  }

  function renderCycleView() {
    if (curView !== "cycle") return;
    var box = document.getElementById("cycle-body");
    if (!box) return;
    var day = data.days[cur];
    var s = day.sent;
    var html = '<div class="metric-grid">' +
      '<div class="metric-card"><div class="lab">涨停</div><div class="val">' + s.zt + '</div></div>' +
      '<div class="metric-card"><div class="lab">跌停</div><div class="val">' + s.dt + '</div></div>' +
      '<div class="metric-card"><div class="lab">炸板率</div><div class="val money-out">' + s.zbrate + '%</div></div>' +
      '<div class="metric-card"><div class="lab">最高板</div><div class="val">' + s.max_lb + '板</div></div>' +
      '<div class="metric-card"><div class="lab">情绪</div><div class="val" style="font-size:15px;color:var(--up);">' + s.tag + '</div></div>' +
      '</div>';
    html += '<div class="grp"><div class="grp-head g-lb3">情绪周期轨迹 · 近 10 日</div></div>';
    box.innerHTML = html;
    document.getElementById("cycle-card") && (function(){
      var old = document.getElementById("cycle-card");
      if (old) old.innerHTML = "";
    })();
  }

  /* ===== P20 周期锚定链：只回答「这条关系链还活着吗」 ===== */
  var anchorWin = 60, anchorFilter = "all";
  window.setAnchorWin = function (n) { anchorWin = n; renderAnchor(); applyFolds(document); };
  window.setAnchorFilter = function (f) { anchorFilter = f; renderAnchor(); applyFolds(document); };
  function anDate(d) {
    var s = String(d || "");
    return s.length === 8 ? s.slice(4, 6) + "/" + s.slice(6, 8) : s;
  }

  function renderAnchor() {
    if (curView !== "anchor") return;
    var box = document.getElementById("anchor-body");
    if (!box) return;
    var a = data.anchor || { clusters: [], relays: [], switches: [], window: [], summary: {}, today: "" };
    var cs = a.clusters || [], win = (a.window || []).slice(-anchorWin);
    var winSet = {};
    win.forEach(function (d) { winSet[d] = 1; });
    var inWin = cs.filter(function (c) {
      return (c.days || []).some(function (x) { return winSet[x.date]; });
    });
    var sm = a.summary || {};

    var sum = document.getElementById("anchor-sum");
    if (sum) sum.innerHTML = '<div class="an-sum">' +
      '<div class="an-sum-c"><span class="v">' + cs.length + '</span><span class="k">属性簇链</span></div>' +
      '<div class="an-sum-c"><span class="v">' + (sm.alive || 0) + '</span><span class="k">今日仍活跃</span></div>' +
      '<div class="an-sum-c"><span class="v">' + (sm.healthy || 0) + '</span><span class="k">链健康</span></div>' +
      '<div class="an-sum-c"><span class="v">' + (sm.relay || 0) + '</span><span class="k">待接力</span></div>' +
      '<div class="an-sum-c"><span class="v">' + (sm.peak || 0) + '</span><span class="k">单日峰值</span></div>' +
      '<div class="an-sum-c"><span class="v">' + win.length + '</span><span class="k">显示交易日</span></div>' +
      '<div class="an-sum-n">识别窗口 ' + (a.window_days || 0) + ' 个交易日 · 属性标签自 ' +
      esc(String(a.label_since || "").slice(0, 8)) + ' 起可用 · 窗口只调整显示跨度，锚按全周期识别</div></div>';

    var counts = { all: inWin.length, healthy: 0, relay: 0, ended: 0 };
    inWin.forEach(function (c) {
      var k = (c.chain_state || {}).key || "ended";
      if (counts[k] !== undefined) counts[k]++;
    });
    var tf = '<div class="an-tools">';
    [20, 40, 60].forEach(function (n) {
      tf += '<button class="an-chip' + (anchorWin === n ? " active" : "") + '" onclick="setAnchorWin(' + n + ')">近 ' + n + ' 日</button>';
    });
    tf += '<span class="an-sep"></span>';
    [["all", "全部"], ["healthy", "链健康"], ["relay", "待接力"], ["ended", "已结束"]].forEach(function (p) {
      tf += '<button class="an-chip' + (anchorFilter === p[0] ? " active" : "") +
        '" onclick="setAnchorFilter(\'' + p[0] + '\')">' + p[1] +
        '<span class="an-n">' + (counts[p[0]] || 0) + '</span></button>';
    });
    tf += '</div>';
    var tbox = document.getElementById("anchor-tools");
    if (tbox) tbox.innerHTML = tf;

    var rel = a.relays || [], sw = a.switches || [], rbox = document.getElementById("anchor-relay");
    if (rbox) {
      var rh = "";
      if (rel.length) {
        rh += '<div class="an-relay"><span class="an-relay-t">属性接力 ·</span>';
        rel.forEach(function (r) {
          rh += '<span class="an-relay-i"><b>' + esc(r.from) + '</b> → <b>' + esc(r.to) +
            '</b> <span>' + anDate(r.date) + ' · 隔 ' + r.gap + ' 日</span></span>';
        });
        rh += '</div>';
      }
      if (sw.length) {
        rh += '<div class="an-relay"><span class="an-relay-t">板块间切换 ·</span>';
        var seenSw = {}, swShown = 0;
        sw.forEach(function (s) {
          if (seenSw[s.to_code] || swShown >= 4) return;  // 同一目标只留一个源，避免重复刷屏
          seenSw[s.to_code] = 1; swShown++;
          rh += '<span class="an-relay-i">' + esc(s.from_name) + ' <span>' + esc(s.from_status) +
            '</span> → <b>' + esc(s.to_name) + '</b> <span>' + s.to_lb + ' 板</span></span>';
        });
        rh += '</div>';
      }
      rbox.innerHTML = rh;
    }

    var shown = inWin.filter(function (c) {
      return anchorFilter === "all" || ((c.chain_state || {}).key || "ended") === anchorFilter;
    });
    var cntEl = document.getElementById("anchor-cnt");
    if (cntEl) cntEl.textContent = shown.length + " 条链";
    if (!shown.length) { box.innerHTML = '<div class="empty">该筛选下暂无锚定链</div>'; return; }

    var h = "";
    shown.forEach(function (c) {
      var st = c.anchor_state || {}, chain = c.chain_state || {}, AN = c.anchor || {};
      var badgeCls = chain.key === "healthy" ? "healthy" : (chain.key === "relay" ? "relay" : "ended");
      var stCls = (st.key === "broken" || st.key === "shaky") ? "broken" : "platform";
      h += '<div class="an-chain"><div class="an-head">' +
        '<span class="an-key">' + esc(c.label) + '</span>' +
        '<span class="an-badge ' + badgeCls + '">' + esc(chain.label || "") + '</span>' +
        '<span class="an-badge ' + stCls + '">锚 ' + esc(st.label || "") + '</span>' +
        '<span class="an-meta">' + anDate(c.first_day) + ' → ' + anDate(c.last_day) +
        ' · 峰值 ' + (c.peak || {}).count + ' 只 · 今日 ' + c.today + ' 只 · ' +
        c.member_total + ' 成员</span></div><div class="an-body">';
      h += '<div class="an-row"><span class="an-lab">锚</span>' + stockLink(AN.code, AN.name) +
        '<span class="an-state">' + esc(st.detail || "") + '</span></div>';
      var fm = (c.first_movers || []).map(function (m) {
        return stockLink(m.code, m.name) + '<span class="an-state">' + anDate(m.first_day) + '</span>';
      }).join('　');
      /* 成员少时「首动梯队」与「同属性」几乎重复，直接省掉这一行 */
      if (fm && c.member_total > 8) h += '<div class="an-row"><span class="an-lab">首动梯队</span>' + fm + '</div>';
      h += '<div class="an-row"><span class="an-lab">同属性</span><div class="an-mem">';
      (c.members || []).forEach(function (m, i) {
        h += '<span class="an-chip-mem' + (i < (c.first_movers || []).length ? " first" : "") + '">' +
          stockLink(m.code, m.name) +
          (m.max_lb > 1 ? '<span class="an-n">' + m.max_lb + '板</span>' : '') + '</span>';
      });
      h += '</div></div>';
      /* 逐日画满整个窗口，无活动的交易日留极淡基线 → 断档/启动点一眼可见 */
      var byDate = {}, pk = (c.peak || {}).count || 1;
      (c.days || []).forEach(function (x) { byDate[x.date] = x.count; });
      h += '<div class="an-spark" title="逐日同属性涨停数">';
      win.forEach(function (dt) {
        var n = byDate[dt] || 0;
        var cls = !n ? " zero" : (dt === c.peak.date ? " peak" : (dt === a.today ? " today" : ""));
        h += '<span class="an-bar' + cls + '" style="height:' +
          (n ? Math.max(8, Math.round(n / pk * 100)) : 4) + '%" title="' +
          anDate(dt) + ' · ' + n + ' 只"></span>';
      });
      h += '</div><div class="an-hint">柱高 = 当日同属性涨停数（红 = 峰值，铜 = 今日，淡线 = 无活动）· 连续近 ' +
        win.length + ' 个交易日</div><div class="an-events">';
      (c.events || []).forEach(function (e) {
        var hot = e.type === "节点切换" || e.type === "扩散峰值";
        h += '<div class="an-ev' + (hot ? " hot" : "") + '"><span class="an-ev-d">' + anDate(e.date) +
          '</span><span class="an-ev-t">' + esc(e.type) + '</span>' + esc(e.text) + '</div>';
      });
      h += '</div></div></div>';
    });
    box.innerHTML = h;
  }

  function renderThemeView() {
    if (curView !== "theme") return;
    var box = document.getElementById("theme-body");
    if (!box) return;
    var day = data.days[cur];
    var html = '<div class="grp"><div class="grp-head g-lb2">主线题材</div>';
    (day.themes || []).forEach(function (t) {
      var tcls = t.stage === "高潮" || t.stage === "加强" ? "t-lb4" : (t.stage === "启动" ? "t-lb3" : "t-lb2");
      html += '<div class="theme-row"><span class="pill ' + tcls + '">' + esc(t.name) + '</span>' +
        '<span class="cnt">' + t.count + '只 · 高度' + t.max_lb + '板</span></div>';
    });
    html += '</div>';
    html += '<div class="grp"><div class="grp-head g-lb3">龙头 · 潜龙</div>';
    var ld = day.leaders;
    if (ld && ld.total) html += '<div style="padding:6px 0;">总龙 <b>' + esc(ld.total['名称']) + '</b>' + (ld.total.today ? ' <span class="pill pill-zt">封板</span>' : ' <span class="pill" style="background:rgba(232,162,58,.12);color:#E8A23A;">断板</span>') + '</div>';
    if (ld && ld.emo) html += '<div style="padding:6px 0;">情绪龙 <b>' + esc(ld.emo['名称']) + '</b> ' + ld.emo.lb + '板（评分 ' + ld.emo.score + '）</div>';
    html += '</div>';
    html += '<div class="grp"><div class="grp-head g-lb3">潜龙候选（' + (day.dragons.pool || []).length + '）</div>';
    (day.dragons.pool || []).forEach(function (c) {
      html += '<div class="dragon-row">' + nameLink(c) + ' ' + c.lb + '板 · ' + esc(c.ind) + ' · <span class="pill pill-zt">' + c.score + '分</span></div>';
    });
    html += '</div>';
    box.innerHTML = html;
  }

  function renderSidePanel() {
    var day = data.days[cur];
    var s = day.sent;
    var mv = data.movement || { alerts: [] };
    var ext = day.ext || {};
    var prev = ext.prev || null;
    var hotN = (mv.alerts || []).filter(function (a) { return a.level === "T1" || a.level === "T2"; }).length;
    var tempCls = s.tag_cls === "danger" ? "st-danger" : (s.tag_cls === "good" ? "st-good" : (s.tag_cls === "warn" ? "st-warn" : "st-flat"));
    var tone = s.tag_cls === "danger" ? "分歧转弱" : (s.tag_cls === "good" ? "分歧转暖" : (s.tag_cls === "warn" ? "分歧退潮" : "震荡混沌"));
    var toneText = (day.hl && day.hl.text) || "市场处于 " + s.tag + " 阶段；涨停" + s.zt + " · 跌停" + s.dt + " · 封板率" + (100 - s.zbrate) + "%";
    var watchText = (day.hl && day.hl.watch) || "明日核心变量：高位龙头分歧是否扩散、低位新题材能否走出首板晋级";
    document.getElementById("side-tone").innerHTML =
      '<div style="font-weight:600;font-size:13px;margin-bottom:8px;color:var(--ink2);">今日定调</div>' +
      '<div class="tone-tag ' + tempCls + '">' + tone + '</div>' +
      '<div style="font-size:12.5px;color:var(--ink2);line-height:1.7;margin-top:8px;">' + esc(toneText) + '</div>' +
      '<div style="margin-top:10px;padding:8px 10px;background:var(--panel-2);border:1px solid var(--line);border-radius:6px;">' +
      '<div style="font-size:11.5px;color:var(--ink3);margin-bottom:4px;">明日核心变量</div>' +
      '<div style="font-size:12.5px;">' + esc(watchText) + '</div></div>';
    var temp = s.tag_cls === "danger" ? 20 : (s.tag_cls === "good" ? 80 : (s.tag_cls === "warn" ? 35 : 50));
    var jn = prev ? prev.jn_rate : "-";
    var avg = prev ? prev.avg_pct : "-";
    document.getElementById("side-coredata").innerHTML =
      '<div style="font-weight:600;font-size:13px;margin-bottom:10px;color:var(--ink2);">核心数据</div>' +
      '<div class="core-grid">' +
      '<div class="core-cell"><div class="lab">涨停</div><div class="val">' + s.zt + '</div></div>' +
      '<div class="core-cell"><div class="lab">跌停</div><div class="val">' + s.dt + '</div></div>' +
      '<div class="core-cell"><div class="lab">炸板</div><div class="val">' + s.zb + '</div></div>' +
      '<div class="core-cell"><div class="lab">最高板</div><div class="val">' + s.max_lb + '板</div></div>' +
      '<div class="core-cell"><div class="lab">晋级率</div><div class="val">' + jn + '%</div></div>' +
      '<div class="core-cell"><div class="lab">昨均涨</div><div class="val ' + (Number(avg) >= 0 ? "money-in" : "money-out") + '">' + avg + '%</div></div>' +
      '</div>' +
      '<div class="temp-bar"><div class="temp-track"><div class="temp-fill" style="width:' + temp + '%"></div><div class="temp-marker" style="left:' + temp + '%"></div></div><div class="temp-labels"><span>冰点</span><span>温和 ' + temp + '</span><span>过热</span></div></div>' +
      '<div class="risk-line"><span>3点</span><span>长跌</span><span>退潮</span><span style="color:' + (s.tag_cls === "good" ? "var(--up)" : (s.tag_cls === "danger" ? "var(--down)" : "var(--ink2)")) + ';font-weight:600;">● ' + s.tag + '</span></div>';
    var prevHtml = '<div style="font-weight:600;font-size:13px;margin-bottom:8px;color:var(--ink2);">昨日涨停表现</div>';
    var sq = data.sealq;
    if (sq && sq.gap) {
      prevHtml += '<div class="sq-gap' + (sq.gap.type === "break" ? " sq-break" : "") + '">' +
        (sq.gap.type === "break" ? "梯队断层" : "断板预警") + ' · ' + esc(sq.gap.txt) +
        (sq.gap.names ? '<span style="color:var(--ink3)">（' + esc(sq.gap.names) + '）</span>' : '') + '</div>';
    }
    if (prev && prev.jn_list && prev.jn_list.length) {
      prev.jn_list.forEach(function (r) {
        prevHtml += '<div class="prev-row"><span>' + esc(r["名称"]) + '</span><span class="money-in">+' + Number(r["涨跌幅"]).toFixed(2) + '%</span></div>';
      });
    } else prevHtml += '<div class="empty" style="padding:14px;">无昨日数据</div>';
    if (sq) {
      if (sq.refeng !== null && sq.refeng !== undefined) {
        prevHtml += '<div class="prev-row" style="margin-top:6px;"><span>昨日炸板·今日回封（' + sq.refeng_n + '只）</span>' +
          '<span class="' + (sq.refeng >= 40 ? "money-in" : "money-out") + '">' + sq.refeng + '%</span></div>';
      }
      var fundRows = '';
      sq.funds.forEach(function (fd) {
        if (fd.cur === null && fd.prev === null) return;
        var dd = (fd.cur !== null && fd.prev !== null && fd.prev > 0) ? Math.round((fd.cur / fd.prev - 1) * 100) : null;
        fundRows += '<div class="prev-row"><span>' + fd.lb + '板</span><span>' +
          (fd.cur === null ? "-" : fd.cur) + ' / ' + (fd.prev === null ? "-" : fd.prev) + '亿' +
          (dd !== null ? ' <b class="' + (dd >= 0 ? "money-in" : "money-out") + '">' + (dd >= 0 ? "+" : "") + dd + '%</b>' : '') + '</span></div>';
      });
      if (fundRows) prevHtml += '<div style="font-size:11px;color:var(--ink3);margin:8px 0 2px;">封板资金·亿（今/昨）</div>' + fundRows;
    }
    document.getElementById("side-prev").innerHTML = prevHtml;
  }

  var scrMode = "short";
  function setScrMode(m) {
    scrMode = m;
    document.querySelectorAll(".scr-btn[data-m]").forEach(function (b) { b.classList.toggle("active", b.getAttribute("data-m") === m); });
    renderScreener(); applyFolds(document);
  }
  window.setScrMode = setScrMode;

  function renderScreener() {
    if (curView !== "screener") return;
    var box = document.getElementById("scr-body");
    if (!box) return;
    var sc = data.screener || { short: [], mid: [], long: [] };
    var notes = {
      short: "短线多维：技术面40（延续性评分）+ 情绪面30（题材热度×梯队位置）+ 资金面30（封板资金×封板时间）· 候选=当日涨停池",
      mid: "中线多维：技术面40（趋势状态/RS/信号）+ 基本面40（ROE×营收增速）+ 量价20（突破/回踩/新高）· 候选=趋势池",
      long: "长线多维：估值30（PE 5年分位）+ 质地40（ROE×负债率）+ 成长30（营收增速×AI硬件链标签）· 候选=价值/蓝筹/成长三池"
    };
    var noteEl = document.getElementById("scr-note");
    if (noteEl) noteEl.textContent = notes[scrMode] || "";
    var cols = {
      short: [["tech", "技术面"], ["emo", "情绪面"], ["fund", "资金面"]],
      mid: [["tech", "技术面"], ["funda", "基本面"], ["vol", "量价"]],
      long: [["val", "估值"], ["q", "质地"], ["g", "成长"]]
    }[scrMode];
    var lst = sc[scrMode] || [];
    var cntEl = document.getElementById("scr-cnt");
    if (cntEl) cntEl.textContent = lst.length + " 只候选 · " + ({ short: "短线", mid: "中线", long: "长线" }[scrMode]) + "模式";
    var html = '<table><thead><tr><th>#</th><th>名称</th><th class="num">综合分</th>';
    cols.forEach(function (c) { html += '<th class="num">' + c[1] + '</th>'; });
    html += '<th>核心理由</th></tr></thead><tbody>';
    lst.forEach(function (r, i) {
      html += '<tr>' +
        '<td class="code">' + (i + 1) + '</td>' +
        '<td>' + nameLink(r) + (r.lb ? ' <span class="pill pill-zt">' + r.lb + '板</span>' : '') + (r.ai ? ' <span class="attr-pill at-topic">AI链</span>' : '') + '</td>' +
        '<td class="num"><b class="scr-score">' + r.score + '</b></td>';
      cols.forEach(function (c) { html += '<td class="num">' + (r[c[0]] !== undefined ? r[c[0]] : '-') + '</td>'; });
      html += '<td style="max-width:260px;white-space:normal;font-size:11.5px;color:var(--ink2);">' + esc(r.why || "") + '</td>' +
        '</tr>';
    });
    if (!lst.length) html += '<tr><td colspan="' + (4 + cols.length) + '" class="empty">无候选</td></tr>';
    html += '</tbody></table>';
    html += '<div class="cycle-hint">业务策略/产品进度维度暂无数据源，成长模式下以营收增速+AI硬件链标签为业务动能代理 · 评分仅供研究参考</div>';
    box.innerHTML = html;
    fx(function (g) { g.from(box.querySelectorAll("tbody tr"), { autoAlpha: 0, y: 10, duration: 0.35, stagger: 0.03, ease: "power2.out", clearProps: "all" }); });
  }

  var newsCat = "全部";
  var NEWS_KW = ["利好", "利空", "减持", "增持", "回购", "质押", "问询函", "关注函", "监管函",
                 "立案", "处罚", "预增", "预减", "业绩预告", "业绩", "净利", "营收", "增长",
                 "下滑", "中标", "分红", "退市", "冻结", "商誉减值", "政策", "降准", "降息",
                 "CPI", "PPI", "PMI", "GDP", "社融", "涨停"];
  function hlKw(s) {
    var out = esc(s);
    NEWS_KW.forEach(function (w) {
      out = out.split(w).join('<em class="kw">' + w + '</em>');
    });
    return out;
  }
  function escThenLink(s) {
    var out = esc(s);
    var map = data.newsMap || {};
    var names = Object.keys(map).sort(function (a, b) { return b.length - a.length; });
    names.forEach(function (n) {
      if (out.indexOf(n) < 0) return;
      var code = map[n];
      var ex = code.charAt(0) === "6" ? "sh" : (code.charAt(0) === "4" || code.charAt(0) === "8" ? "bj" : "sz");
      var url = "https://quote.eastmoney.com/" + ex + code + ".html";
      out = out.split(n).join('<a class="co-link js-stk" href="' + url + '" target="_blank" rel="noopener" data-code="' + esc(code) + '" data-name="' + esc(n).replace(/"/g, "&quot;") + '" title="点击查看个股深研（Ctrl/&#8984;+点击直达东财）">' + n + '</a>');
    });
    NEWS_KW.forEach(function (w) {
      out = out.split(w).join('<em class="kw">' + w + '</em>');
    });
    return out;
  }
  window.setNewsCat = function (c) { newsCat = c; renderNews(); applyFolds(document); };

  /* ===== P19 资讯雷达：赛道 / 语言筛选 + 源覆盖状态 ===== */
  var radarTrack = "all", radarLang = "all", radarSrcOpen = false;
  window.setRadarTrack = function (t) { radarTrack = t; renderRadar(); applyFolds(document); };
  window.setRadarLang = function (l) { radarLang = l; renderRadar(); applyFolds(document); };
  window.toggleRadarSources = function () { radarSrcOpen = !radarSrcOpen; renderRadar(); applyFolds(document); };

  function renderRadar() {
    if (curView !== "radar") return;
    var box = document.getElementById("radar-body");
    if (!box) return;
    var rd = data.radar || { items: [], tracks: [], status: [], ok: 0, total: 0, zh: 0, updated: "" };
    var items = rd.items || [], tracks = rd.tracks || [], status = rd.status || [];

    /* 覆盖状态条：来源 / 时点 / 覆盖状态，一眼可核查消息面是否可信 */
    var st = document.getElementById("radar-status");
    if (st) {
      var upd = String(rd.updated || "");
      var updTxt = upd.length === 8 ? upd.slice(0, 4) + "-" + upd.slice(4, 6) + "-" + upd.slice(6, 8) : (upd || "未采集");
      st.innerHTML = '<div class="rd-status">' +
        '<div class="rd-stat"><span class="v">' + rd.ok + '/' + rd.total + '</span><span class="k">本轮可用源</span></div>' +
        '<div class="rd-stat"><span class="v">' + tracks.length + '</span><span class="k">赛道</span></div>' +
        '<div class="rd-stat"><span class="v">' + items.length + '</span><span class="k">消息条数</span></div>' +
        '<div class="rd-stat"><span class="v">' + rd.zh + '</span><span class="k">中文</span></div>' +
        '<div class="rd-when">更新 ' + esc(updTxt) + ' · 保留近 7 天 · 合规红线已过滤 · 全部为公开 RSS，不含预测市场/加密/博彩类内容</div>' +
        '</div>';
    }

    /* 赛道 + 语言筛选 */
    var cnt = {};
    items.forEach(function (i) { cnt[i.track] = (cnt[i.track] || 0) + 1; });
    var f = '<div class="rd-filter-row">';
    f += '<button class="rd-chip' + (radarTrack === "all" ? " active" : "") + '" onclick="setRadarTrack(\'all\')">全部<span class="rd-n">' + items.length + '</span></button>';
    tracks.forEach(function (t) {
      if (!cnt[t.key]) return;
      var short = String(t.name).split(" / ")[0];
      f += '<button class="rd-chip' + (radarTrack === t.key ? " active" : "") + '" onclick="setRadarTrack(\'' + t.key + '\')">' + esc(short) + '<span class="rd-n">' + cnt[t.key] + '</span></button>';
    });
    f += '</div><div class="rd-filter-row rd-filter-sub">';
    f += '<button class="rd-chip' + (radarLang === "all" ? " active" : "") + '" onclick="setRadarLang(\'all\')">全部语言</button>';
    f += '<button class="rd-chip' + (radarLang === "zh" ? " active" : "") + '" onclick="setRadarLang(\'zh\')">仅中文源<span class="rd-n">' + rd.zh + '</span></button>';
    f += '<span class="rd-divider"></span>';
    f += '<button class="rd-linkbtn" id="radar-src-btn" onclick="toggleRadarSources()">' + (radarSrcOpen ? "收起源状态" : "查看源状态") + '</button>';
    f += '</div>';
    var fbox = document.getElementById("radar-filters");
    if (fbox) fbox.innerHTML = f;

    /* 源状态：默认收起，只列失败源，title 带原因，便于核查覆盖缺口 */
    var sbox = document.getElementById("radar-srcs");
    if (sbox) {
      var bad = status.filter(function (s) { return !s.ok; });
      var sh = '<div class="rd-srcs-t">本轮 ' + rd.ok + '/' + rd.total + ' 个源正常返回，以下 ' + bad.length + ' 个源无数据（403 / 超时 / 证书 / 反爬）；鼠标悬停可看原因。失败源不影响其它赛道。</div><div class="rd-src-grid">';
      bad.forEach(function (s) {
        sh += '<span class="rd-src-pill bad" title="' + esc(s.source + " · " + (s.err || "无条目")).replace(/"/g, "&quot;") + '">' + esc(s.source) + '</span>';
      });
      sbox.innerHTML = sh + '</div>';
      sbox.style.display = radarSrcOpen ? "" : "none";
    }

    var shown = items.filter(function (i) {
      return (radarTrack === "all" || i.track === radarTrack) &&
             (radarLang === "all" || i.lang === "zh");
    });
    var cntEl = document.getElementById("radar-cnt");
    if (cntEl) cntEl.textContent = shown.length + " 条";
    if (!shown.length) {
      box.innerHTML = '<div class="empty">该筛选下暂无消息，试试切换赛道或语言</div>';
      return;
    }
    var html = "";
    shown.slice(0, 240).forEach(function (i) {
      var title = i.link
        ? '<a class="rd-title" href="' + esc(i.link).replace(/"/g, "&quot;") + '" target="_blank" rel="noopener">' + esc(i.title) + '</a>'
        : '<span class="rd-title">' + esc(i.title) + '</span>';
      html += '<div class="rd-item">' +
        '<div class="rd-meta">' +
          '<span class="rd-time">' + esc(String(i.pub_time).slice(5, 16)) + '</span>' +
          '<span class="rd-track">' + esc(i.track_name) + '</span>' +
          '<span class="rd-src">' + esc(i.source) + '</span>' +
          '<span class="rd-lang ' + (i.lang === "zh" ? "" : "en") + '">' + (i.lang === "zh" ? "中" : "EN") + '</span>' +
        '</div>' + title +
        (i.summary ? '<div class="rd-sum">' + esc(String(i.summary).slice(0, 150)) + '</div>' : '') +
        '</div>';
    });
    html += '<div class="rd-hint">源清单移植自 Vibe-Astock 的 106 个策展 RSS（12 赛道），每日 21:30 随看板自动刷新；点标题直达原文 · Ctrl/⌘+点击可在新标签保留 · 内容仅作消息面线索，不构成投资建议</div>';
    box.innerHTML = html;
  }

  function renderNews() {
    if (curView !== "news") return;
    var box = document.getElementById("news-body");
    if (!box) return;
    var list = data.news || [];
    var cntMap = { "全部": list.length };
    list.forEach(function (n) { cntMap[n.category] = (cntMap[n.category] || 0) + 1; });
    var cats = ["全部", "业绩", "增减持", "回购", "质押", "问询", "政策", "宏观", "观点", "其他"];
    var html = '<div class="news-cats">';
    cats.forEach(function (c) {
      if (!cntMap[c]) return;
      html += '<button class="cat-btn' + (newsCat === c ? " active" : "") + '" onclick="setNewsCat(\'' + c + '\')">' + c + ' <span class="n">' + cntMap[c] + '</span></button>';
    });
    html += '</div>';
    var shown = list.filter(function (n) { return newsCat === "全部" || n.category === newsCat; });
    var cntEl = document.getElementById("news-cnt");
    if (cntEl) cntEl.textContent = shown.length + " 条 · " + newsCat;
    if (!shown.length) {
      box.innerHTML = html + '<div class="empty">该分类暂无资讯</div>';
      return;
    }
    html += '<div class="tl">';
    var nRows = shown.slice(0, 120);
    nRows.forEach(function (n) {
      var cls = n.sentiment === "利好" ? "pos" : (n.sentiment === "利空" ? "neg" : "neu");
      var tagTxt = n.sentiment === "中性" ? "中性观察" : n.sentiment;
      var why = n.reason ? ("关键词命中：" + esc(n.reason)) : "无明确多空关键词，判定为中性";
      var title = n.link ? '<a href="' + esc(n.link) + '" target="_blank" rel="noopener" class="tl-title">' + escThenLink(n.title) + '</a>'
                         : '<span class="tl-title">' + escThenLink(n.title) + '</span>';
      html += '<div class="tl-item">' +
        '<div class="tl-time">' + esc(String(n.pub_time).slice(5, 16)) + '<span class="tl-src">' + esc(n.source || "") + '</span></div>' +
        title +
        (n.summary ? '<div class="tl-sum">' + escThenLink(String(n.summary).slice(0, 160)) + '</div>' : '') +
        '<div class="ana ' + cls + '">' +
          '<span class="ana-tag">' + tagTxt + '</span>' +
          '<span class="ana-why">' + why + '</span>' +
          '<span class="ana-cat">' + esc(n.category) + '</span>' +
        '</div>' +
        '</div>';
    });
    html += '</div>';
    html += '<div class="cycle-hint">结论由关键词规则自动判定（利好/利空词表），仅供参考；结构化公告（问询函、股东减持、股权质押等）可通过 news_manual.json 人工补充 · 本分类共 ' + shown.length + ' 条，默认载入最近 ' + nRows.length + ' 条</div>';
    box.innerHTML = html;
    fx(function (g) { g.from(box.querySelectorAll(".tl-item"), { autoAlpha: 0, y: 10, duration: 0.35, stagger: 0.03, ease: "power2.out", clearProps: "all" }); });
  }

  function pctSpan(p) {
    if (p === null || p === undefined) return '<span class="q-na">--</span>';
    var s = (p > 0 ? "+" : "") + p.toFixed(2) + "%";
    return '<span class="' + (p > 0 ? "q-up" : (p < 0 ? "q-dn" : "q-flat")) + '">' + s + '</span>';
  }

  function stockLink(code, name) {
    var an = esc(name).replace(/"/g, "&quot;");
    var tip = ' title="点击查看个股深研（Ctrl/&#8984;+点击直达东财）"';
    if (!code) return '<a class="co-link js-stk" target="_blank" rel="noopener" data-code="" data-name="' + an + '"' + tip + ' href="https://quote.eastmoney.com/search.html?keyword=' + encodeURIComponent(name) + '">' + esc(name) + '</a>';
    var ex = code[0] === "6" ? "sh" : ((code[0] === "8" || code[0] === "4" || code[0] === "9") ? "bj" : "sz");
    return '<a class="co-link js-stk" target="_blank" rel="noopener" data-code="' + esc(code) + '" data-name="' + an + '"' + tip + ' href="https://quote.eastmoney.com/' + ex + code + '.html">' + esc(name) + '</a>';
  }

  function renderFocus() {
    /* ---- 市场聚焦 ---- */
    var foc = data.focus || [], fb = document.getElementById("focus-body");
    document.getElementById("foc-cnt").textContent = foc.length + "只";
    var fh = '<div class="foc-grid">';
    foc.forEach(function (f) {
      fh += '<div class="foc-card">' +
        '<div class="foc-head">' + stockLink(f.code, f.cur_name || f.name) +
        '<span class="foc-tag">' + esc(f.tag) + '</span>' +
        (f.lb ? '<span class="foc-lb">' + f.lb + '板</span>' : '') +
        pctSpan(f.pct) + '</div>' +
        '<div class="foc-reason">' + escThenLink(f.reason) + '</div>' +
        '<div class="foc-date">' + esc(String(f.date || "").slice(0, 10)) + ' · ' + esc(f.src) + '</div></div>';
    });
    fh += '</div>';
    fb.innerHTML = fh;
    /* ---- 字辈挖掘（卡片网格） ---- */
    var np = data.nameplay || { active: [], watch: [] };
    var nh = '<div class="np-cards">';
    np.active.forEach(function (c) {
      nh += '<div class="np-card"><div class="np-card-h"><span class="np-big">' + esc(c.ch) + '</span>' +
        '<span class="np-big-sub">字辈</span><div class="np-stats2">' +
        '<span><b class="c-up">' + c.today + '</b> 今日</span><span>昨 ' + c.yesterday + '</span>' +
        (c.streak >= 2 ? '<span class="np-hot">连燃 ' + c.streak + '日</span>' : '') +
        '<span>最高 ' + c.max_lb + ' 板</span></div></div><div class="np-mems">';
      (c.members || []).forEach(function (m) {
        nh += '<div class="np-mem' + (m.lb >= 3 ? " np-mem-hi" : "") + '">' + stockLink(m.code, m.name) +
          (m.lb > 1 ? '<b class="chip-lb">' + m.lb + '板</b>' : '') + '</div>';
      });
      nh += '</div></div>';
    });
    nh += '</div>';
    if (!np.active.length) nh = '<div class="np-empty">今日无 ≥3 只共识字辈 · 情绪分散无文字共性</div>';
    /* P20 ③ 共用口径：属性簇取涨停原因标签，双字/谐音不拆，与上方单字字辈并列对照 */
    var cl = np.clusters || [];
    if (cl.length) {
      nh += '<div class="np-clus-t">属性簇 · 取涨停原因标签，双字/谐音不拆</div><div class="np-clus">';
      cl.forEach(function (c) {
        nh += '<span class="np-clus-p' + (c.alive ? " live" : "") + '" title="锚 ' +
          esc(c.anchor).replace(/"/g, "&quot;") + ' · ' + esc(c.state).replace(/"/g, "&quot;") +
          ' · 峰值 ' + c.peak + ' 只">' + esc(c.key) + ' · 今日 ' + c.today +
          ' · ' + esc(c.chain) + '</span>';
      });
      nh += '</div>';
    }
    if (np.watch && np.watch.length) {
      nh += '<div class="np-watch-t">观察（各 2 只，尚未成气候）：' +
        np.watch.map(function (c) { return '<b>' + esc(c.ch) + '</b> ' + esc(c.members.map(function (m) { return m.name; }).join("、")); }).join('　·　') + '</div>';
    }
    document.getElementById("np-body").innerHTML = nh;
    document.getElementById("np-cnt").textContent = np.active.length + "个活跃";
    /* ---- 重点题材库 ---- */
    var tl = data.themelib || [], th = "";
    tl.forEach(function (g) {
      th += '<div class="tlp-group"><div class="tlp-head">' + esc(g.name) +
        '<span class="tlp-type">' + (g.type === "short" ? "短线" : "中长线") + '</span>' +
        (g.zt ? '<span class="tlp-zt">涨停 ' + g.zt + '</span>' : '') + '</div>';
      (g.subs || []).forEach(function (s) {
        th += '<div class="tlp-sub"><div class="tlp-subname">' + esc(s.name) +
          (s.zt ? '<b class="tlp-subzt">' + s.zt + '板</b>' : '') + '</div><div class="tlp-chips">';
        (s.members || []).forEach(function (m) {
          th += '<span class="chip' + (m.lb ? " chip-zt" : "") + '">' + stockLink(m.code, m.name) + pctSpan(m.pct) + '</span>';
        });
        th += '</div></div>';
      });
      th += '</div>';
    });
    document.getElementById("tl-body").innerHTML = th;
    document.getElementById("tl-cnt").textContent = tl.length + "大方向";
    /* ---- 卡位补涨雷达 ---- */
    var cu = data.catchup || { leaders: [], switches: [] };
    var cb = document.getElementById("cu-body");
    document.getElementById("cu-cnt").textContent = cu.leaders.length + "触发";
    var ch = "";
    cu.leaders.forEach(function (l) {
      var L = l.leader, ast = L.anchor_state || null;
      ch += '<div class="cu-row"><span class="cu-tag' + (l.wave2 ? " cu-wave" : "") + '">' + esc(l.tag) + '</span>' +
        stockLink(L.code, L.name) + '<b class="cu-lb">' + L.hi_lb + '板</b>' +
        (ast ? '<span class="cu-anchor ' + ((ast.key === "broken" || ast.key === "shaky") ? "bad" : "ok") +
          '" title="' + esc(ast.detail || "").replace(/"/g, "&quot;") + '">锚 ' + esc(ast.label) + '</span>' : '') +
        '<span class="cu-ind">' + esc(L.ind) + '</span><span class="cu-arrow">→</span>';
      if (l.cands.length) {
        l.cands.forEach(function (c) {
          ch += '<span class="chip' + (c.lb ? " chip-zt" : "") + '">' + stockLink(c.code, c.name) +
            '<i class="cu-link">' + esc(c.link) + '</i>' +
            (c.lb ? '<b class="chip-lb">' + c.lb + '板</b>' : '') + '</span>';
        });
      } else {
        ch += '<span class="np-empty">暂无同源候选</span>';
      }
      ch += '</div>';
    });
    if (!cu.leaders.length) ch += '<div class="np-empty">今日无可操作龙头状态（一字/断板/回调）· 接力顺畅</div>';
    (cu.switches || []).forEach(function (sw) {
      ch += '<div class="tlp-node"><span class="tlp-node-t">节点切换</span> ' +
        esc(sw.from_name) + '（' + esc(sw.from_ind) + ' ' + sw.from_lb + '板·' + esc(sw.from_status) + '）→ ' +
        stockLink(sw.to_code, sw.to_name) + '<span class="tlp-node-ind">【' + esc(sw.to_ind) + '】' + sw.to_lb + '板</span></div>';
    });
    cb.innerHTML = ch;
  }

  var tlPeriod = "day";
  window.setTlPeriod = function (p) {
    tlPeriod = p;
    document.querySelectorAll(".scr-btn[data-p]").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-p") === p);
    });
    renderTimeline(); applyFolds(document);
  };

  function fmtMin(m) {
    var h = Math.floor(m / 60), mm = m % 60;
    return (h < 10 ? "0" : "") + h + ":" + (mm < 10 ? "0" : "") + mm;
  }

  function fmtDate8(d) {
    var s = String(d);
    return s.length >= 8 ? s.slice(4, 6) + "/" + s.slice(6, 8) : s;
  }

  function renderTimeline() {
    var tl = data.timeline || {}, box = document.getElementById("tlp-body");
    var tip = document.getElementById("tlp-tip");
    var cnt = document.getElementById("tlp-cnt");
    /* ---------- 当日 ---------- */
    if (tlPeriod === "day") {
      var day = tl.day || { events: [], nodes: [], inds: [], n_up: 0, n_zb: 0, max_lb: 0 };
      cnt.textContent = day.n_up + "板/" + day.n_zb + "炸";
      tip.textContent = fmtDate8(day.date || "") + " · 红点=上板 橙点=炸板 · 高标炸板→他板10分钟内上板 = 情绪节点转换";
      var h = "";
      /* 节点转换（最重要，置顶） */
      h += '<div class="tlp-sec"><span class="tlp-sec-t">节点转换</span>';
      if (day.nodes && day.nodes.length) {
        day.nodes.forEach(function (nd) {
          var z = nd.zb;
          h += '<div class="tlp-node"><span class="tlp-node-t">' + fmtMin(z.t) + '</span> 高标 <b>' +
            stockLink(z.code, z.name) + '</b> <span class="tlp-node-lb">' + z.lb + '板</span> 炸板 → ';
          nd.after.forEach(function (u, i) {
            h += (i ? " / " : "") + '<span class="tlp-node-arrow">' + fmtMin(u.t) + '</span> ' +
              stockLink(u.code, u.name) + '<span class="tlp-node-ind">【' + esc(u.ind) + '】' + (u.lb > 1 ? u.lb + "板" : "上板") + '</span>';
          });
          h += '</div>';
        });
      } else {
        h += '<div class="np-empty">今日无高标炸板转换 · 接力顺畅</div>';
      }
      h += '</div>';
      /* 板块启动顺序（强弱） */
      h += '<div class="tlp-sec"><span class="tlp-sec-t">板块启动顺序</span><div class="tlp-inds">';
      (day.inds || []).forEach(function (m) {
        h += '<span class="chip' + (m.maxlb >= 3 ? " chip-zt" : "") + '"><b class="tlp-ind-t">' + fmtMin(m.first) + '</b> ' +
          esc(m.ind) + ' <i>' + m.n + '家' + (m.maxlb > 1 ? "/" + m.maxlb + "板" : "") + '</i></span>';
      });
      h += '</div></div>';
      /* 主事件轴（情绪） */
      h += '<div class="tlp-sec"><span class="tlp-sec-t">事件轴</span><div class="tev-wrap">';
      (day.events || []).forEach(function (e) {
        h += '<div class="tev"><span class="tev-t">' + fmtMin(e.t) + '</span><span class="tev-dot ' +
          (e.kind === "up" ? "tev-up" : "tev-zb") + '"></span>' +
          stockLink(e.code, e.name) +
          (e.lb > 1 ? '<b class="tev-lb">' + e.lb + '板</b>' : '') +
          '<span class="tev-ind">' + esc(e.ind) + '</span>' +
          (e.kind === "up"
            ? (e.reason ? '<span class="tev-r">' + esc(e.reason) + '</span>' : '') +
              (e.lb >= 3 ? '<span class="' + (e.turn >= 20 ? "tev-blow" : "tev-turn") + '">' + (e.turn >= 20 ? "爆量" : "换手") + e.turn.toFixed(0) + '%</span>' : '')
            : '<span class="tev-zbtag">炸' + e.zbcnt + '次</span>') +
          '</div>';
      });
      h += '</div></div>';
      box.innerHTML = h;
      return;
    }
    /* ---------- 当周 / 当月 ---------- */
    var per = tl[tlPeriod] || { days: [], nodes: [], matrix: [], dates: [] };
    cnt.textContent = per.dates.length + "个交易日";
    tip.textContent = (tlPeriod === "week" ? "近 5 个交易日" : "近 22 个交易日") + " · 情绪柱颜色=涨停家数相对冷热 · 断层/冰点/高潮自动标记";
    var h2 = "";
    /* 关键节点 */
    h2 += '<div class="tlp-sec"><span class="tlp-sec-t">关键节点</span>';
    if (per.nodes && per.nodes.length) {
      per.nodes.slice().reverse().forEach(function (n) {
        var cls = { high: "tlp-n-high", break: "tlp-n-break", ice: "tlp-n-ice", hot: "tlp-n-hot" }[n.type] || "tlp-n-ice";
        h2 += '<div class="tlp-pnode ' + cls + '"><b>' + fmtDate8(n.date) + '</b> ' + esc(n.txt) + '</div>';
      });
    } else {
      h2 += '<div class="np-empty">区间内无新高/断层/冰点/高潮节点</div>';
    }
    h2 += '</div>';
    /* 情绪柱 */
    h2 += '<div class="tlp-sec"><span class="tlp-sec-t">每日情绪</span><div class="tlp-days">';
    var maxZt = Math.max.apply(null, per.days.map(function (e) { return e.zt; }).concat([1]));
    per.days.forEach(function (e) {
      var ratio = e.zt / maxZt;
      var heat = ratio > 0.72 ? "tlp-d-hot" : (ratio < 0.4 ? "tlp-d-cold" : "tlp-d-mid");
      h2 += '<div class="tlp-day ' + heat + '"><b>' + fmtDate8(e.date) + '</b>' +
        '<span class="tlp-d-zt">' + e.zt + '板</span>' +
        '<span class="tlp-d-sub">高' + e.maxlb + ' 炸' + e.zb + ' 跌' + e.dt + '</span></div>';
    });
    h2 += '</div></div>';
    /* 板块热力矩阵 */
    h2 += '<div class="tlp-sec"><span class="tlp-sec-t">板块涨停热力</span><div class="tlp-matrix"><table><tr><th></th>';
    per.dates.forEach(function (d) { h2 += '<th>' + fmtDate8(d) + '</th>'; });
    h2 += '<th>合计</th></tr>';
    (per.matrix || []).forEach(function (row) {
      h2 += '<tr><td class="tlp-m-ind">' + esc(row.ind) + '</td>';
      row.vals.forEach(function (v) {
        h2 += '<td class="' + (v >= 3 ? "tlp-m-hi" : (v > 0 ? "tlp-m-lo" : "")) + '">' + (v || "·") + '</td>';
      });
      h2 += '<td class="tlp-m-sum">' + row.total + '</td></tr>';
    });
    h2 += '</table></div></div>';
    box.innerHTML = h2;
  }

  function renderAll() {
    renderNavModules();
    renderStage();
    renderPromotion();
    renderExt();
    renderUnlock();
    renderAlert();
    renderCycleView();
    renderThemeView();
    renderScreener();
    renderNews();
    renderRadar();
    renderAnchor();
    renderFocus();
    renderTimeline();
    renderSidePanel();
    renderDatebar();
    buildIndTags();
    applyFolds(document);
  }

  function renderUnlock() {
    var box = document.getElementById("unlock-body");
    if (!box) return;
    var u = data.unlock;
    if (!u || !u.total) { box.innerHTML = '<div class="empty">解禁数据未采集</div>'; return; }
    var html = '<div class="prev-stats">' +
      '<div class="prev-stat"><div class="v">' + u.days.length + ' 天</div><div class="l">有解禁日</div></div>' +
      '<div class="prev-stat"><div class="v">' + u.total + ' 只</div><div class="l">解禁个股</div></div>' +
      '<div class="prev-stat"><div class="v ' + (u.total_mv >= 500 ? "money-out" : "") + '">' + u.total_mv + '亿</div><div class="l">30日解禁市值</div></div>' +
      '</div>';
    html += '<table style="margin-top:10px;"><tr><th>名称</th><th>解禁日</th><th>解禁市值</th><th>占总股本</th><th>类型</th></tr>';
    u.stocks.forEach(function (r) {
      var hot = r.ratio !== null && r.ratio >= 5;
      html += '<tr>' +
        '<td>' + nameLink(r) + '</td>' +
        '<td class="num">' + r.日期 + '</td>' +
        '<td class="num">' + r.mv + '亿</td>' +
        '<td class="num"><b' + (hot ? ' style="color:var(--down,#c0392b);"' : '') + '>' + (r.ratio !== null && r.ratio !== undefined ? r.ratio + '%' : '-') + '</b></td>' +
        '<td style="color:var(--ink3);font-size:12px;">' + esc(r.类型 || '-') + '</td>' +
        '</tr>';
    });
    html += '</table>';
    box.innerHTML = html;
  }

  function onFilterChange() {
    if (curView !== "stage") { showView("stage"); }
    else { renderStage(); buildIndTags(); applyFolds(document); }
  }

  function bindFilters() {
    document.getElementById("f-lb").onchange = function (e) { filters.lb = parseInt(e.target.value, 10); onFilterChange(); };
    document.getElementById("f-turn-min").oninput = function (e) { filters.turnMin = Number(e.target.value) || 0; onFilterChange(); };
    document.getElementById("f-turn-max").oninput = function (e) { filters.turnMax = Number(e.target.value) || 100; onFilterChange(); };
    document.getElementById("f-seal").onchange = function (e) { filters.seal = e.target.value; onFilterChange(); };
    document.getElementById("f-zb").onchange = function (e) { filters.zb = e.target.value; onFilterChange(); };
    document.getElementById("f-reset").onclick = function () {
      filters = { lb: 0, turnMin: 0, turnMax: 100, seal: "all", zb: "all", inds: {} };
      document.getElementById("f-lb").value = "0";
      document.getElementById("f-turn-min").value = "";
      document.getElementById("f-turn-max").value = "";
      document.getElementById("f-seal").value = "all";
      document.getElementById("f-zb").value = "all";
      renderAll();
    };
    document.getElementById("t-lv").onchange = function (e) { tFilters.lv = e.target.value; renderTrend(); applyFolds(document); };
    document.getElementById("t-sig").onchange = function (e) { tFilters.sig = e.target.value; renderTrend(); applyFolds(document); };
    document.getElementById("t-reset").onclick = function () {
      tFilters = { lv: "all", sig: "all" };
      document.getElementById("t-lv").value = "all";
      document.getElementById("t-sig").value = "all";
      renderTrend(); applyFolds(document);
    };
  }

  /* ===== P18 个股深研抽屉：全部取 BOARD_DATA，不触网 =====
     链接函数统一打 js-stk + data-code/data-name，用 document 事件委托接线，
     避免逐个 render 函数改调用；Ctrl/⌘/Shift/Alt + 点击仍直达东财。 */
  var sdMask, sdWrap, sdBody;
  function closeStock() {
    if (!sdWrap) return;
    sdWrap.classList.remove("on");
    sdMask.classList.remove("on");
    sdWrap.setAttribute("aria-hidden", "true");
  }
  (function buildStockDrawer() {
    var m = document.createElement("div");
    m.className = "sd-mask";
    m.id = "sd-mask";
    var w = document.createElement("aside");
    w.className = "sd-wrap";
    w.id = "sd-wrap";
    w.setAttribute("role", "dialog");
    w.setAttribute("aria-modal", "true");
    w.setAttribute("aria-label", "个股深研");
    w.setAttribute("aria-hidden", "true");
    w.innerHTML =
      '<div class="sd-head"><div>' +
        '<div class="sd-title"><span class="sd-name" id="sd-name"></span><span class="sd-code" id="sd-code"></span></div>' +
        '<div class="sd-sub" id="sd-sub"></div>' +
      '</div><button type="button" class="sd-close" id="sd-close" aria-label="关闭">&#10005;</button></div>' +
      '<div class="sd-body" id="sd-body"></div>';
    document.body.appendChild(m);
    document.body.appendChild(w);
    sdMask = m;
    sdWrap = w;
    sdBody = document.getElementById("sd-body");
    m.addEventListener("click", closeStock);
    document.getElementById("sd-close").addEventListener("click", closeStock);
  })();
  window.addEventListener("keydown", function (e) {
    if (e.key === "Escape" || e.keyCode === 27) closeStock();
  });

  function sdEx(code) {
    var c = String(code || "");
    if (!c) return "sz";
    if (c.charAt(0) === "6" || c.charAt(0) === "9") return "sh";
    if (c.charAt(0) === "8" || c.charAt(0) === "4") return "bj";
    return "sz";
  }
  function sdUrl(code, name) {
    if (!code) return "https://quote.eastmoney.com/search.html?keyword=" + encodeURIComponent(name || "");
    return "https://quote.eastmoney.com/" + sdEx(code) + code + ".html";
  }
  function sdNum(v, digits) {
    if (v === null || v === undefined || v === "" || isNaN(Number(v))) return "-";
    return Number(v).toFixed(digits === undefined ? 2 : digits);
  }
  function sdPct(v) {
    if (v === null || v === undefined || v === "" || isNaN(Number(v))) return ["-", ""];
    var n = Number(v);
    return [(n > 0 ? "+" : "") + n.toFixed(2) + "%", n > 0 ? "up" : (n < 0 ? "dn" : "")];
  }
  function findStock(code, name) {
    var c = String(code || "").trim();
    var n = String(name || "").trim();
    if (!c && n && data.newsMap) c = String(data.newsMap[n] || "");
    if (!c && !n) return null;
    var axis = data.dates.slice(-5);
    var trail = axis.map(function (d) {
      var pools = ((data.days[d] || {}).pools) || {};
      var kinds = ["zt", "zb", "dt"];
      for (var i = 0; i < kinds.length; i++) {
        var arr = pools[kinds[i]] || [];
        for (var j = 0; j < arr.length; j++) {
          var r = arr[j];
          var rc = String(r["代码"] || "").trim();
          var rn = String(r["名称"] || "").trim();
          if ((c && rc === c) || (n && rn === n)) return { date: d, kind: kinds[i], row: r };
        }
      }
      return { date: d, kind: "none", row: null };
    });
    var curHit = null, lastHit = null;
    trail.forEach(function (t) {
      if (!t.row) return;
      lastHit = t;
      if (t.date === cur) curHit = t;
    });
    var hit = curHit || lastHit;
    var row = hit ? hit.row : null;
    return {
      code: c || (row ? String(row["代码"] || "") : ""),
      name: n || (row ? String(row["名称"] || "") : ""),
      row: row,
      kind: hit ? hit.kind : "none",
      date: hit ? hit.date : null,
      trail: trail
    };
  }
  function sdTrailHtml(trail) {
    var colors = { zt: "var(--up)", zb: "var(--amber)", dt: "var(--down)", none: "var(--surface-3)" };
    var labels = { zt: "涨停", zb: "炸板", dt: "跌停", none: "未入池" };
    var html = '<div class="sd-sec"><div class="sd-sec-t"><span>近 5 日板位轨迹</span><span class="sd-tval">柱高 = 连板数</span></div><div class="sd-trail">';
    trail.forEach(function (t) {
      var lb = t.row ? (Number(t.row["连板数"]) || 0) : 0;
      var h = t.kind === "none" ? 3 : Math.min(56, 10 + lb * 12 + (t.kind === "zt" ? 6 : 0));
      var tv = t.kind === "none" ? "·" : (t.kind === "zt" && lb ? lb + "板" : labels[t.kind].slice(0, 1));
      html += '<div class="sd-tcol" title="' + fmtDate(t.date) + ' · ' + labels[t.kind] + '">' +
        '<span class="sd-tv">' + tv + '</span>' +
        '<span class="sd-tbar" style="height:' + h + 'px;background:' + colors[t.kind] + ';"></span>' +
        '<span class="sd-td">' + t.date.slice(4, 6) + '/' + t.date.slice(6, 8) + '</span></div>';
    });
    return html + '</div></div>';
  }
  function openStock(code, name) {
    var s = findStock(code, name);
    if (!s) return;
    var row = s.row;
    document.getElementById("sd-name").textContent = s.name || "—";
    document.getElementById("sd-code").textContent = s.code || "代码未知";
    var kindTxt = { zt: "涨停池", zb: "炸板池", dt: "跌停池", none: "近 5 日未入池" };
    var kindCls = { zt: "up", zb: "amber", dt: "down", none: "" };
    document.getElementById("sd-sub").innerHTML =
      '<span class="sd-badge ' + kindCls[s.kind] + '">' + kindTxt[s.kind] + '</span>' +
      (row ? esc(String(row["所属行业"] || "行业未知")) : "本地快照无该股当日盘口") +
      (s.date ? " · " + fmtDate(s.date) : "");

    var url = sdUrl(s.code, s.name);
    var html = '<div class="sd-sec"><div class="sd-exts">' +
      '<a class="sd-ext" href="' + url + '" target="_blank" rel="noopener">东财行情 / 分时 / 日K &#8599;</a>' +
      (s.code ? '<a class="sd-ext" href="https://guba.eastmoney.com/list,' + s.code + '.html" target="_blank" rel="noopener">股吧讨论 &#8599;</a>' : "") +
      '</div></div>';

    if (row) {
      var p = sdPct(row["涨跌幅"]);
      html += '<div class="sd-sec"><div class="sd-sec-t"><span>当日盘口快照</span><span class="sd-tval">' + fmtDate(s.date) + '</span></div><div class="sd-kv">' +
        '<div class="sd-cell"><span class="k">最新价</span><span class="v">' + sdNum(row["最新价"]) + '</span></div>' +
        '<div class="sd-cell"><span class="k">涨跌幅</span><span class="v ' + p[1] + '">' + p[0] + '</span></div>' +
        '<div class="sd-cell"><span class="k">换手率</span><span class="v">' + sdNum(row["换手率"]) + '%</span></div>' +
        '<div class="sd-cell"><span class="k">封板资金</span><span class="v">' + fmtMoney(row["封板资金"]) + '</span></div>' +
        '<div class="sd-cell"><span class="k">首封 / 末封</span><span class="v">' + fmtSeal(row["首次封板时间"]) + ' / ' + fmtSeal(row["最后封板时间"]) + '</span></div>' +
        '<div class="sd-cell"><span class="k">炸板次数</span><span class="v">' + (row["炸板次数"] === null || row["炸板次数"] === undefined ? "-" : row["炸板次数"]) + '</span></div>' +
        '</div><div class="sd-meta">' +
        '<span>总市值 <b>' + fmtMoney(row["总市值"]) + '</b></span>' +
        '<span>流通市值 <b>' + fmtMoney(row["流通市值"]) + '</b></span>' +
        '<span>成交额 <b>' + fmtMoney(row["成交额"]) + '</b></span>' +
        (row["涨停统计"] ? '<span>涨停统计 <b>' + esc(String(row["涨停统计"])) + '</b></span>' : "") +
        '</div></div>';

      if (row["_reason"] || row["涨停原因"]) {
        html += '<div class="sd-sec"><div class="sd-sec-t"><span>涨停归因</span></div>' +
          '<div class="sd-note">' + esc(String(row["_reason"] || row["涨停原因"])) + '</div></div>';
      }
      var a = row["_analysis"];
      if (a) {
        var dims = [["封板结构", "seal", 4], ["封板资金", "fund", 3], ["换手健康", "turn", 3], ["板位高度", "pos", 3], ["板块地位", "status", 3]];
        html += '<div class="sd-sec"><div class="sd-sec-t"><span>延续性评分 · 五维</span><span class="sd-tval">' + a.total + ' / 16 · ' + esc(a.level) + '</span></div>';
        dims.forEach(function (dm) {
          var v = Number(a[dm[1]] || 0);
          var w = Math.max(4, Math.min(100, v / dm[2] * 100));
          html += '<div class="sd-line"><span class="lb">' + dm[0] + '</span><span class="track"><i class="fill" style="width:' + w + '%"></i></span><span class="sc">' + v + '/' + dm[2] + '</span></div>';
        });
        html += '</div>';
        html += '<div class="sd-sec"><div class="sd-sec-t"><span>次日策略 / 风控</span></div>' +
          '<div class="sd-note"><span class="t">策略</span>' + esc(a.strat || "-") + '</div>' +
          '<div class="sd-note risk"><span class="t">风控</span>' + esc(a.risk || "-") + '</div></div>';
      }
      var at = row["_attr"];
      if (at) {
        var parts = [["题材", at.topic, "var(--accent)"], ["资金", at.money, "var(--blue)"], ["技术", at.tech, "var(--purple)"], ["消息", at.msg, "var(--ink3)"]];
        html += '<div class="sd-sec"><div class="sd-sec-t"><span>涨停四维归因</span><span class="sd-tval">主因 ' + esc(at.main || "-") + '</span></div><div class="sd-stack">';
        parts.forEach(function (q) { html += '<i style="width:' + (Number(q[1]) || 0) + '%;background:' + q[2] + '"></i>'; });
        html += '</div><div class="sd-legend">';
        parts.forEach(function (q) { html += '<span><i style="background:' + q[2] + '"></i>' + q[0] + ' <b>' + q[1] + '%</b></span>'; });
        html += '</div></div>';
      }
    } else {
      html += '<div class="sd-sec"><div class="sd-empty">该股在最近 5 个交易日未进入涨停 / 炸板 / 跌停池，本地快照没有盘口与评分数据。<br>可点上方链接到东方财富查看实时行情，或切到更早日期后再试。</div></div>';
    }
    html += sdTrailHtml(s.trail);
    html += '<div class="sd-foot">数据来自本地看板快照（最近 5 个交易日），不实时联网 · Ctrl / ⌘ + 点击股票名可直接打开东财 · ESC 或点击遮罩关闭</div>';
    sdBody.innerHTML = html;
    sdBody.scrollTop = 0;
    sdMask.classList.add("on");
    sdWrap.classList.add("on");
    sdWrap.setAttribute("aria-hidden", "false");
  }
  document.addEventListener("click", function (e) {
    if (e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    var t = e.target;
    var a = t && t.closest ? t.closest("a.js-stk") : null;
    if (!a) return;
    e.preventDefault();
    openStock(a.getAttribute("data-code") || "", a.getAttribute("data-name") || "");
  }, false);

  bindFilters();
  renderTrend();
  renderValue();
  var _h = (location.hash || "").slice(1);
  var _views = ["stage", "alert", "cycle", "theme", "screener", "news", "focus", "timeline", "radar", "anchor"];
  if (_h && _views.indexOf(_h) >= 0) { showView(_h); } else { renderAll(); }

  // ===== GSAP 动画层（仅首屏，判定已在顶部完成）=====

  // ① 首屏：三栏卡片 stagger 入场
  fx(function (g) {
    g.from(".desk-grid .card", { autoAlpha: 0, y: 18, duration: 0.5, stagger: 0.07, ease: "power2.out", clearProps: "all" });
  });

  // ② 数字滚动（指标卡/核心数据）
  fx(function (g) {
    document.querySelectorAll(".metric-card .val, .core-cell .val").forEach(function (el) {
      var m = el.textContent.trim().match(/^(-?\d+\.?\d*)(.*)$/);
      if (!m) return;
      var target = parseFloat(m[1]);
      if (isNaN(target) || target === 0) return;
      var dec = m[1].indexOf(".") >= 0 ? 1 : 0;
      var suffix = m[2];
      var obj = { v: 0 };
      g.to(obj, { v: target, duration: 0.8, ease: "power2.out", onUpdate: function () {
        el.textContent = (dec ? obj.v.toFixed(1) : Math.round(obj.v)) + suffix;
      }});
    });
  });

  // ③ 温度计填充动画
  fx(function (g) {
    var f = document.querySelector(".temp-fill");
    if (f) g.from(f, { width: 0, duration: 0.9, ease: "power2.out" });
    var mk = document.querySelector(".temp-marker");
    if (mk) g.from(mk, { left: "0%", duration: 0.9, ease: "power2.out" });
  });

  // ④ 梯队分组块 stagger
  fx(function (g) {
    var grps = document.querySelectorAll("#stage-body .grp");
    if (grps.length) g.from(grps, { autoAlpha: 0, y: 14, duration: 0.45, stagger: 0.08, ease: "power2.out", clearProps: "all" });
  });
})();
</script>
</body>
</html>
"""
