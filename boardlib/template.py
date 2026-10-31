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
    /* finesse Sage Ledger 变体 · Warm Stone 暖纸色阶 + 琥珀金 accent · 红涨绿跌语义独立 */
    --page:#16181c; --card:#1d2127; --ink:#e8eaf0; --ink2:#b9bec7; --ink3:#8a8f98;
    --line:rgba(255,255,255,.08); --up:#E2554F; --upbg:rgba(226,85,79,.13); --down:#2FAE76; --downbg:rgba(47,174,118,.13);
    --blue:#5FA8CC; --bluebg:rgba(95,168,204,.13); --amber:#E8A23A; --amberbg:rgba(232,162,58,.13);
    --purple:#9B8EF2; --purplebg:rgba(155,142,242,.13);
    --toolbar:#101216; --toolbar-line:#2a2d33;
    --accent:#E8833A; --accent-soft:rgba(232,131,58,.15);
    --shadow:none; --panel-2:#242930;
    --r:12px; --r-sm:8px;
  }
  *{box-sizing:border-box; margin:0; padding:0;}
  body{background:var(--page); color:var(--ink); font-family:"PingFang SC","Microsoft YaHei",-apple-system,sans-serif; line-height:1.55; font-size:13.5px;}
  input,select,button,textarea{color-scheme:dark;}
  .wrap{max-width:1320px; margin:0 auto; padding:22px 18px 60px;}
  .shell{background:var(--card); border:1px solid var(--border); border-radius:28px; padding:24px 26px 34px; box-shadow:0 40px 90px -50px rgba(0,0,0,.4); position:relative; overflow:hidden;}
  .shell::before{content:""; position:absolute; top:0; right:0; width:280px; height:200px; background:radial-gradient(280px 200px at 90% -10%, rgba(232,162,58,.15), transparent 60%); pointer-events:none;}
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
  tr:hover td{background:#f2f7fd;}
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
  .g-lb7{background:rgba(226,85,79,.16);color:#fff;}
  .g-lb5{background:rgba(226,85,79,.15);color:rgba(226,85,79,.16);}
  .g-lb4{background:rgba(226,85,79,.15);color:#a32d2d;}
  .g-lb3{background:rgba(232,162,58,.12);color:#854f0b;}
  .g-lb2{background:rgba(95,168,204,.12);color:#1d5fa8;}
  .g-lb1{background:var(--panel-2);color:#8a8f98;}
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
  .foc-card{border:1px solid var(--line);border-radius:var(--r-sm);padding:12px 14px;background:linear-gradient(180deg,var(--amberbg),var(--card) 60%);}
  .foc-head{display:flex;align-items:center;gap:8px;font-size:15px;margin-bottom:6px;flex-wrap:wrap;}
  .foc-tag{font-size:10px;background:var(--accent);color:#fff;border-radius:4px;padding:1px 6px;}
  .foc-lb{font-size:11px;color:var(--up);font-weight:700;}
  .foc-reason{font-size:12.5px;color:var(--ink2);line-height:1.55;}
  .foc-date{font-size:10.5px;color:var(--ink3);margin-top:6px;}
  .np-row{display:grid;grid-template-columns:76px 168px 1fr;gap:10px;padding:10px 0;border-bottom:1px dashed var(--line);align-items:start;}
  .np-row:last-child{border-bottom:none;}
  .np-dim{opacity:.62;}
  .np-char{font-size:17px;font-weight:800;color:var(--accent);}
  .np-stats{font-size:11.5px;color:var(--ink2);line-height:1.8;}
  .np-hot{color:var(--up);font-weight:700;}
  .np-hist{color:var(--ink3);font-size:10.5px;letter-spacing:2px;}
  .np-members{display:flex;flex-wrap:wrap;gap:6px;}
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
          <div id="promo-body"></div>
        </div>
        <div class="card">
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
      <div class="view" id="view-focus" style="display:none">
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">市场聚焦 <span class="cnt" id="foc-cnt"></span></div>
            <div class="tb-tip">新股 / 并购重组 / 复牌等情绪共振标的 · 点名字看K线分时</div>
          </div>
          <div id="focus-body"></div>
        </div>
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">字辈挖掘 <span class="cnt" id="np-cnt"></span></div>
            <div class="tb-tip">同一汉字被≥3只涨停共享 = 共识字辈（华字辈/洋字辈）· 市场高度共性自动识别</div>
          </div>
          <div id="np-body"></div>
        </div>
        <div class="card">
          <div class="toolbar">
            <div class="tb-title">重点题材库 <span class="cnt" id="tl-cnt"></span></div>
            <div class="tb-tip">AI硬件·战略板块（中长线） / AI应用·传媒·消费（短线）</div>
          </div>
          <div id="tl-body"></div>
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
        renderPool();
        buildIndTags();
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

    var html = '<div style="font-weight:600; font-size:15px; margin-bottom:12px;">资金透视 · 复盘闭环</div>';

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
        list.slice(0, 8).forEach(function (r) {
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
        ext.fund_in.slice(0, 6).forEach(function (r) {
          html += '<div class="lhb-row"><span class="nm"><b>' + esc(r["行业"]) + '</b> <span style="color:var(--ink3);">' + Number(r["行业-涨跌幅"]).toFixed(2) + '%</span></span>' +
            '<span class="amt money-in">+' + Number(r["净额"]).toFixed(2) + '亿</span></div>';
        });
        html += '<div style="font-weight:600;font-size:12.5px;margin:10px 0 2px;">净流出 TOP</div>';
        ext.fund_out.slice(0, 3).forEach(function (r) {
          html += '<div class="lhb-row"><span class="nm">' + esc(r["行业"]) + '</span>' +
            '<span class="amt money-out">' + Number(r["净额"]).toFixed(2) + '亿</span></div>';
        });
        html += '</div>';
      }
      if (seats.hot && seats.hot.length) {
        html += '<div class="sub-box"><h4>游资动向 · 知名游资今日动作（买卖双向）</h4>';
        seats.hot.slice(0, 8).forEach(function (r) {
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
    html = '<div style="color:var(--ink2);font-size:12.5px;margin-bottom:10px;">候选池 ' + list.length + ' 只 · 均线多头 ' + up + ' 只 · 按强度评分排序</div>';
    html += '<table><tr><th>代码</th><th>名称</th><th>现价</th><th>20日涨幅</th><th>RS(超额)</th><th>距52周高</th><th>MA20</th><th>MA60</th><th>信号</th><th>强度</th></tr>';
    list.forEach(function (r) {
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
        '<div style="font-weight:600;font-size:14px;">🏛 蓝筹股池 <span style="font-size:12px;color:var(--ink2);font-weight:400;">行业龙头 · ' + v.bluechip.length + ' 只（bluechip_watchlist.json）</span></div>' +
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
        '<div style="font-weight:600;font-size:14px;">🚀 科技成长池 <span style="font-size:12px;color:var(--ink2);font-weight:400;">AI 硬件链 · ' + v.growth.length + ' 只（growth_watchlist.json）</span></div>' +
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
        '<div style="font-weight:600;font-size:14px;">💎 价值股池 <span style="font-size:12px;color:var(--ink2);font-weight:400;">低估值 + 高质地 · ' + v.pool.length + ' 只（value_watchlist.json）</span></div>' +
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
        '<div style="font-weight:600;font-size:14px;">🌱 低位潜力股 <span style="font-size:12px;color:var(--ink2);font-weight:400;">距52周高回落25%+ · 近期活跃 · 基本面不烂 · ' + data.lowpos.total + ' 只</span></div>' +
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
    var name = esc(r["名称"] || r["代码"] || "");
    return '<a href="' + emLink(r["代码"]) + '" target="_blank" rel="noopener" style="color:inherit;text-decoration:none;border-bottom:1px dashed var(--ink3);" title="点击查看分时/日K">' + name + '</a>';
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
    var subs = { stage: "短线 · 涨停梯队", alert: "短线 · 异动预警", cycle: "短线 · 周期结构", theme: "短线 · 主线龙头", screener: "多因子选股器", news: "公告资讯", focus: "短线 · 聚焦·字辈·题材库", timeline: "短线 · 情绪·强弱·节点" };
    var s = document.getElementById("brand-sub");
    if (s) s.textContent = subs[name] || "A股复盘台";
    renderAll();
  }
  window.showView = showView;

  var NAV_META = { stage: ["涨停梯队", "□"], alert: ["异动预警", "△"], cycle: ["情绪周期", "∿"], theme: ["主线龙头", "★"], timeline: ["时间线", "⌛"], screener: ["选股器", "◎"], news: ["公告资讯", "❐"], focus: ["聚焦挖掘", "◉"] };
  var NAV_GROUPS = [
    { name: "短线复盘", items: ["stage", "alert", "cycle", "theme", "timeline"] },
    { name: "工具", items: ["screener", "news", "focus"] },
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
    var html = '<div class="toolbar"><div class="tb-title">板块晋级率 <span class="cnt">一进二 / 二进三 / 三进四 · 同比昨日（↑升 ↓降）</span></div></div>';
    html += '<table><thead><tr><th>板块</th><th class="num">涨停</th><th class="num">首板</th><th class="num">首板率</th>' +
      '<th class="num">一进二</th><th class="num">二进三</th><th class="num">三进四</th></tr></thead><tbody>';
    rows.slice(0, 14).forEach(function (r) {
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
    var zt = day.pools.zt || [];
    var total = zt.length;
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
    if (cntEl) cntEl.textContent = "共 " + showCnt + " 只（全部）";
    var tipEl = document.getElementById("stage-tip");
    if (tipEl) tipEl.textContent = "按连板高度分组 · 颜色越深越强";
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

  function renderThemeView() {
    if (curView !== "theme") return;
    var box = document.getElementById("theme-body");
    if (!box) return;
    var day = data.days[cur];
    var html = '<div class="grp"><div class="grp-head g-lb2">主线题材</div>';
    (day.themes || []).slice(0, 6).forEach(function (t) {
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
    (day.dragons.pool || []).slice(0, 8).forEach(function (c) {
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
      prev.jn_list.slice(0, 4).forEach(function (r) {
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
    document.querySelectorAll(".scr-btn").forEach(function (b) { b.classList.toggle("active", b.getAttribute("data-m") === m); });
    renderScreener();
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
      out = out.split(n).join('<a class="co-link" href="' + url + '" target="_blank" rel="noopener" title="点击查看K线图/分时图">' + n + '</a>');
    });
    NEWS_KW.forEach(function (w) {
      out = out.split(w).join('<em class="kw">' + w + '</em>');
    });
    return out;
  }
  window.setNewsCat = function (c) { newsCat = c; renderNews(); };

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
    shown.slice(0, 60).forEach(function (n) {
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
    html += '<div class="cycle-hint">结论由关键词规则自动判定（利好/利空词表），仅供参考；结构化公告（问询函、股东减持、股权质押等）可通过 news_manual.json 人工补充</div>';
    box.innerHTML = html;
    fx(function (g) { g.from(box.querySelectorAll(".tl-item"), { autoAlpha: 0, y: 10, duration: 0.35, stagger: 0.03, ease: "power2.out", clearProps: "all" }); });
  }

  function pctSpan(p) {
    if (p === null || p === undefined) return '<span class="q-na">--</span>';
    var s = (p > 0 ? "+" : "") + p.toFixed(2) + "%";
    return '<span class="' + (p > 0 ? "q-up" : (p < 0 ? "q-dn" : "q-flat")) + '">' + s + '</span>';
  }

  function stockLink(code, name) {
    if (!code) return '<a class="co-link" target="_blank" rel="noopener" href="https://quote.eastmoney.com/search.html?keyword=' + encodeURIComponent(name) + '">' + esc(name) + '</a>';
    var ex = code[0] === "6" ? "sh" : ((code[0] === "8" || code[0] === "4" || code[0] === "9") ? "bj" : "sz");
    return '<a class="co-link" target="_blank" rel="noopener" href="https://quote.eastmoney.com/' + ex + code + '.html">' + esc(name) + '</a>';
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
    /* ---- 字辈挖掘 ---- */
    var np = data.nameplay || { active: [], watch: [] };
    function npRow(c, dim) {
      var chips = "";
      (c.members || []).forEach(function (m) {
        chips += '<span class="chip' + (m.lb ? " chip-zt" : "") + '">' + stockLink(m.code, m.name) +
          (m.lb > 1 ? '<b class="chip-lb">' + m.lb + '板</b>' : '') + '</span>';
      });
      return '<div class="np-row' + (dim ? " np-dim" : "") + '">' +
        '<div class="np-char">' + esc(c.ch) + '字辈</div>' +
        '<div class="np-stats">今日涨停 <b class="c-up">' + c.today + '</b> 只 · 昨日 ' + c.yesterday +
        (c.streak >= 2 ? ' · <span class="np-hot">连燃' + c.streak + '日</span>' : '') +
        ' · 最高 ' + c.max_lb + ' 板' +
        '<br><span class="np-hist">' + (c.hist || []).join(" ") + '</span></div>' +
        '<div class="np-members">' + chips + '</div></div>';
    }
    var nh = "";
    np.active.forEach(function (c) { nh += npRow(c, false); });
    if (!np.active.length) nh = '<div class="np-empty">今日无 ≥3 只共识字辈 · 情绪分散无文字共性</div>';
    if (np.watch && np.watch.length) {
      nh += '<div class="np-watch-t">观察（今日 2 只，尚未成气候）</div>';
      np.watch.forEach(function (c) { nh += npRow(c, true); });
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
  }

  var tlPeriod = "day";
  window.setTlPeriod = function (p) {
    tlPeriod = p;
    document.querySelectorAll(".scr-btn[data-p]").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-p") === p);
    });
    renderTimeline();
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
    renderFocus();
    renderTimeline();
    renderSidePanel();
    renderDatebar();
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

  function bindFilters() {
    document.getElementById("f-lb").onchange = function (e) { filters.lb = parseInt(e.target.value, 10); renderPool(); };
    document.getElementById("f-turn-min").oninput = function (e) { filters.turnMin = Number(e.target.value) || 0; renderPool(); };
    document.getElementById("f-turn-max").oninput = function (e) { filters.turnMax = Number(e.target.value) || 100; renderPool(); };
    document.getElementById("f-seal").onchange = function (e) { filters.seal = e.target.value; renderPool(); };
    document.getElementById("f-zb").onchange = function (e) { filters.zb = e.target.value; renderPool(); };
    document.getElementById("f-reset").onclick = function () {
      filters = { lb: 0, turnMin: 0, turnMax: 100, seal: "all", zb: "all", inds: {} };
      document.getElementById("f-lb").value = "0";
      document.getElementById("f-turn-min").value = "";
      document.getElementById("f-turn-max").value = "";
      document.getElementById("f-seal").value = "all";
      document.getElementById("f-zb").value = "all";
      renderAll();
    };
    document.getElementById("t-lv").onchange = function (e) { tFilters.lv = e.target.value; renderTrend(); };
    document.getElementById("t-sig").onchange = function (e) { tFilters.sig = e.target.value; renderTrend(); };
    document.getElementById("t-reset").onclick = function () {
      tFilters = { lv: "all", sig: "all" };
      document.getElementById("t-lv").value = "all";
      document.getElementById("t-sig").value = "all";
      renderTrend();
    };
  }

  bindFilters();
  renderAll();

  // ===== GSAP 动画层（CDN 加载失败时优雅降级为无动画）=====
  var prefersReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function fx(fn) { if (window.gsap && !prefersReduced) fn(window.gsap); }

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
