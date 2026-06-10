"""Inline ``<style>`` block for the mobile-first dashboard."""

_FRAGMENT = r"""<style>
:root{
  --bg:#0e1116; --panel:#161b22; --panel2:#1c2330; --line:#2a3240;
  --text:#e6e9ee; --dim:#8b95a5; --accent:#4f9cf9; --ok:#3fb96d;
  --warn:#e0a93e; --bad:#e25d5d; --r:12px;
}
*{box-sizing:border-box;margin:0;padding:0}
[hidden]{display:none!important}
body{background:var(--bg);color:var(--text);
  font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  padding-bottom:calc(64px + env(safe-area-inset-bottom))}
header{position:sticky;top:0;z-index:5;background:var(--bg);
  padding:14px 16px 10px;border-bottom:1px solid var(--line);
  display:flex;align-items:baseline;gap:8px}
header h1{font-size:17px;font-weight:650}
header .sub{color:var(--dim);font-size:12px;margin-left:auto;display:flex;
  align-items:center;gap:8px;flex-shrink:0}
#status-pill{color:var(--accent);font-size:11px;font-weight:600;
  white-space:nowrap;max-width:42vw;overflow:hidden;text-overflow:ellipsis}
#busy-bar{position:fixed;top:0;left:0;right:0;height:2px;z-index:40;
  background:linear-gradient(90deg,transparent,var(--accent),transparent);
  background-size:200% 100%;opacity:0;transition:opacity .2s;pointer-events:none}
#busy-bar.active{opacity:1;animation:busy-slide 1.1s linear infinite}
@keyframes busy-slide{0%{background-position:200% 0}100%{background-position:-200% 0}}
.card{position:relative}
.card.card-pending>.pending-overlay{position:absolute;inset:0;border-radius:var(--r);
  background:rgba(14,17,22,.72);display:flex;align-items:center;justify-content:center;
  gap:10px;font-size:13px;font-weight:600;z-index:2}
.pending-spinner{width:16px;height:16px;border:2px solid var(--line);
  border-top-color:var(--accent);border-radius:50%;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.skeleton .card{opacity:.55;pointer-events:none}
.skeleton .stat .v{background:var(--line);color:transparent;border-radius:6px}
main{padding:14px 14px 24px;max-width:640px;margin:0 auto}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.card{background:var(--panel);border:1px solid var(--line);
  border-radius:var(--r);padding:12px 14px;margin-bottom:10px}
.stat .v{font-size:24px;font-weight:700}
.stat .l{color:var(--dim);font-size:12px;margin-top:2px}
.section{color:var(--dim);font-size:12px;text-transform:uppercase;
  letter-spacing:.08em;margin:18px 2px 8px}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;
  font-size:11px;font-weight:600;border:1px solid var(--line);color:var(--dim)}
.badge.ok{color:var(--ok);border-color:var(--ok)}
.badge.warn{color:var(--warn);border-color:var(--warn)}
.badge.bad{color:var(--bad);border-color:var(--bad)}
.badge.info{color:var(--accent);border-color:var(--accent)}
.title{font-weight:600;margin-bottom:4px}
.dim{color:var(--dim);font-size:13px}
.small{font-size:12px}
ul.plain{list-style:none}
ul.plain li{padding:3px 0 3px 14px;position:relative;font-size:13px}
ul.plain li:before{content:"–";position:absolute;left:0;color:var(--dim)}
.btnrow{display:flex;gap:8px;margin-top:10px}
button{flex:1;border:0;border-radius:9px;padding:11px 8px;font-size:14px;
  font-weight:600;color:#fff;background:var(--panel2);cursor:pointer}
button.approve{background:var(--ok)}
button.reject{background:var(--bad)}
button.ghost{background:var(--panel2);color:var(--text);border:1px solid var(--line)}
button:disabled{opacity:.45}
nav{position:fixed;bottom:0;left:0;right:0;display:flex;z-index:5;
  background:var(--panel);border-top:1px solid var(--line);
  padding-bottom:env(safe-area-inset-bottom)}
nav a{flex:1;text-align:center;padding:11px 0 9px;color:var(--dim);
  text-decoration:none;font-size:12px;font-weight:600}
nav a.active{color:var(--accent)}
nav a .n{display:inline-block;min-width:16px;border-radius:8px;font-size:10px;
  background:var(--accent);color:#fff;margin-left:3px;padding:0 4px}
.empty{color:var(--dim);text-align:center;padding:28px 0;font-size:13px}
#viewer{position:fixed;inset:0;background:rgba(8,10,14,.92);z-index:20;
  display:none;flex-direction:column}
#viewer.open{display:flex}
#viewer .bar{display:flex;align-items:center;padding:12px 14px;gap:10px;
  border-bottom:1px solid var(--line)}
#viewer .bar .path{font-size:12px;color:var(--dim);overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap;flex:1}
#viewer pre{flex:1;overflow:auto;padding:16px;font-size:12.5px;line-height:1.5;
  white-space:pre-wrap;word-break:break-word;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
#toast{position:fixed;left:50%;bottom:84px;transform:translateX(-50%);
  background:var(--panel2);border:1px solid var(--line);color:var(--text);
  padding:9px 16px;border-radius:999px;font-size:13px;opacity:0;
  transition:opacity .25s;pointer-events:none;z-index:30}
#toast.show{opacity:1}
.run{display:flex;align-items:center;gap:10px;padding:8px 0;
  border-bottom:1px solid var(--line);font-size:13px}
.run:last-child{border-bottom:0}
.dot{width:8px;height:8px;border-radius:50%;flex:none}
.dot.running,.dot.queued{background:var(--accent)}
.dot.waiting-on-gate{background:var(--warn)}
.dot.done{background:var(--ok)}
.dot.stopped,.dot.failed{background:var(--bad)}
.ticket-glance{cursor:pointer}
.ticket-expand{margin-top:10px;padding-top:10px;border-top:1px solid var(--line)}
.crit-list{list-style:none;margin:8px 0}
.crit-list li{padding:4px 0;font-size:13px}
.crit-list li:before{content:"☐ ";color:var(--dim)}
.crit-list li.done:before{content:"☑ ";color:var(--ok)}
.hint{color:var(--warn);font-size:12px;margin-top:6px}
.gate-glance{cursor:pointer}
.gate-drawer{margin-top:10px;padding-top:10px;border-top:1px solid var(--line)}
pre.excerpt{font-size:11px;line-height:1.4;max-height:220px;overflow:auto;
  background:var(--panel2);padding:10px;border-radius:8px;margin-top:8px;
  white-space:pre-wrap;word-break:break-word;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.burn-chart{margin-top:10px}
.burn-legend{display:flex;gap:14px;font-size:11px;color:var(--dim);margin-bottom:10px}
.burn-legend span{display:flex;align-items:center;gap:5px}
.burn-swatch{width:10px;height:10px;border-radius:2px;flex:none}
.burn-swatch.time{background:var(--accent)}
.burn-swatch.tok{background:var(--warn)}
.burn-row{display:grid;grid-template-columns:minmax(72px,88px) 1fr minmax(64px,76px);
  gap:8px;align-items:center;padding:7px 0;border-bottom:1px solid var(--line);font-size:12px}
.burn-row:last-child{border-bottom:0}
.burn-label{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.burn-bars{display:flex;flex-direction:column;gap:4px}
.burn-track{height:6px;background:var(--panel2);border-radius:3px;overflow:hidden}
.burn-fill{height:100%;border-radius:3px;min-width:2px;transition:width .3s ease}
.burn-fill.time{background:var(--accent)}
.burn-fill.tok{background:var(--warn)}
.burn-meta{text-align:right;color:var(--dim);font-size:11px;line-height:1.3}
.burn-tabs{display:flex;gap:6px;margin-bottom:10px}
.burn-tab{flex:1;padding:8px 4px;border-radius:8px;border:1px solid var(--line);
  background:var(--panel2);color:var(--dim);font-size:11px;font-weight:600;cursor:pointer;text-align:center}
.burn-tab.active{color:var(--accent);border-color:var(--accent);background:rgba(79,156,249,.08)}
.burn-subtitle{color:var(--dim);font-size:12px;margin-bottom:10px;line-height:1.4}
.burn-run-select{width:100%;margin-bottom:10px;padding:9px 10px;border-radius:9px;
  border:1px solid var(--line);background:var(--panel2);color:var(--text);font-size:13px}
.graph-tabs{display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap}
.graph-tab{padding:8px 10px;border-radius:8px;border:1px solid var(--line);
  background:var(--panel2);color:var(--dim);font-size:11px;font-weight:600;cursor:pointer}
.graph-tab.active{color:var(--accent);border-color:var(--accent)}
.loop-card{margin-bottom:12px}
.loop-live{margin:8px 0;padding:10px 12px;border-radius:9px;border:1px solid var(--line);
  background:var(--panel2);font-size:13px}
.loop-wait-banner{border-color:var(--warn);background:rgba(224,169,62,.08)}
.mermaid-wrap{margin:8px 0;padding:8px;border:1px solid var(--line);border-radius:9px;
  background:var(--panel2);overflow:auto;max-height:min(70vh,720px)}
.mermaid-svg svg{max-width:100%;height:auto;display:block;margin:0 auto}
.mermaid-svg .nodeLabel,.mermaid-svg .label{color:#e8eef8!important}
.mermaid-fallback{font-size:11px;white-space:pre-wrap;color:var(--dim);margin-top:8px}
.graph-wrap{position:relative;height:min(72vh,560px);min-height:320px;border:1px solid var(--line);
  border-radius:var(--r);background:radial-gradient(ellipse at center,#1a2030 0%,#0e1116 100%);
  overflow:hidden;touch-action:none;cursor:grab}
.graph-wrap:active{cursor:grabbing}
.graph-wrap canvas{display:block;width:100%;height:100%}
.graph-toolbar{display:flex;gap:8px;align-items:center;margin-bottom:8px;flex-wrap:wrap}
.graph-toolbar button{padding:7px 12px;font-size:12px}
.graph-legend{display:flex;flex-wrap:wrap;gap:8px 12px;font-size:11px;color:var(--dim);margin-top:8px}
.graph-dot{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:4px}
.graph-dot.code{background:var(--accent)}
.graph-dot.ticket{background:var(--warn)}
.graph-dot.spec{background:var(--ok)}
.graph-dot.analysis{background:#9b7cf6}
.graph-dot.source{background:var(--dim)}
.graph-hint{color:var(--dim);font-size:11px;margin-top:6px}
.graph-chain{position:fixed;inset:0;z-index:50;display:none}
.graph-chain.open{display:block}
.graph-chain-backdrop{position:absolute;inset:0;background:rgba(0,0,0,.55)}
.graph-chain-sheet{position:absolute;left:0;right:0;bottom:0;max-height:70vh;
  background:var(--panel);border-radius:16px 16px 0 0;border:1px solid var(--line);
  display:flex;flex-direction:column}
.graph-chain-bar{display:flex;align-items:center;gap:10px;padding:12px 14px;border-bottom:1px solid var(--line)}
.graph-chain-body{overflow:auto;padding:12px 14px 24px;font-size:13px}
.graph-chain-row{display:flex;align-items:flex-start;gap:8px;padding:8px 0;border-bottom:1px solid var(--line)}
.graph-chain-row:last-child{border-bottom:0}
.graph-chain-dot{width:10px;height:10px;border-radius:50%;flex:none;margin-top:4px}
.dash-section{margin-bottom:12px}
.dash-cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-bottom:12px}
@media(min-width:520px){.dash-cards{grid-template-columns:repeat(4,minmax(0,1fr))}}
.dash-card{background:var(--panel);border:1px solid var(--line);border-radius:var(--r);padding:10px 12px}
.dash-card-val{font-size:22px;font-weight:700;line-height:1.1}
.dash-card-lbl{font-size:11px;color:var(--dim);margin-top:4px}
.dash-grid{display:grid;gap:10px;margin-bottom:10px}
@media(min-width:640px){.dash-grid{grid-template-columns:1.2fr 1fr}}
.dash-panel{padding:12px 14px}
.dash-matrix{width:100%;border-collapse:collapse;font-size:12px}
.dash-matrix th,.dash-matrix td{padding:6px 8px;text-align:center;border-bottom:1px solid var(--line)}
.dash-matrix th:first-child,.dash-matrix td:first-child{text-align:left;font-weight:600}
.dash-cell{display:inline-block;min-width:36px;padding:3px 6px;border-radius:6px;font-weight:600;font-size:11px}
.dash-heat-ok{background:rgba(63,185,109,.15);color:var(--ok)}
.dash-heat-warn{background:rgba(224,169,62,.15);color:var(--warn)}
.dash-heat-bad{background:rgba(226,93,93,.12);color:var(--bad)}
.dash-bars{display:flex;align-items:flex-end;gap:10px;height:120px;padding-top:8px}
.dash-bar-wrap{flex:1;display:flex;flex-direction:column;align-items:center;gap:4px;height:100%}
.dash-bar{width:100%;max-width:40px;border-radius:4px 4px 0 0;min-height:4px}
.dash-bar-lbl{font-size:11px;font-weight:600}
.dash-sig{display:inline-flex;align-items:center;justify-content:center;width:18px;height:18px;
  border-radius:4px;font-size:10px;font-weight:700;margin-right:3px}
.dash-sig-ok{background:rgba(63,185,109,.2);color:var(--ok)}
.dash-sig-miss{background:rgba(226,93,93,.12);color:var(--bad)}
.dash-sigs{display:inline-flex;gap:2px;vertical-align:middle}
.dash-filters{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:10px}
.dash-filter{padding:6px 10px;border-radius:8px;border:1px solid var(--line);
  background:var(--panel2);color:var(--dim);font-size:11px;font-weight:600;cursor:pointer}
.dash-filter.active{color:var(--accent);border-color:var(--accent)}
.dash-untracked{list-style:none;padding:0;margin:0}
.dash-untracked li{display:flex;justify-content:space-between;gap:8px;padding:8px 0;
  border-bottom:1px solid var(--line);font-size:12px}
.dash-untracked li:last-child{border-bottom:0}
.dash-fresh-strip{display:flex;align-items:center;gap:8px;margin-top:6px}
.dash-fresh-bar{flex:1;height:6px;background:var(--panel2);border-radius:3px;overflow:hidden}
.dash-fresh-fill{height:100%;background:var(--warn);border-radius:3px}
.graph-edge-loop,.graph-edge-cite,.graph-edge-link,.graph-edge-wiki{display:inline-block;
  width:18px;height:3px;border-radius:2px;margin-right:4px;vertical-align:middle}
.graph-edge-loop{background:var(--ok);height:4px}
.graph-edge-cite{background:var(--accent)}
.graph-edge-link{background:var(--dim);border-top:1px dashed var(--dim);height:0}
.graph-edge-wiki{background:transparent;border-top:1px dotted var(--dim);height:0}
.graph-wrap{height:min(52vh,480px)}
.graph-controls-stack{display:flex;flex-direction:column;gap:5px;margin-bottom:8px;
  background:var(--panel);border:1px solid var(--line);border-radius:var(--r);padding:10px 12px}
.graph-controls-stack .dash-filters,.graph-controls-stack .graph-tabs,
.graph-controls-stack .graph-toolbar{margin-bottom:0}
.graph-context-panels{margin-bottom:12px}
.graph-context-panels .loop-card,.graph-context-panels .dash-panel{margin-bottom:8px}
.graph-context-panels .loop-card:last-child,.graph-context-panels .dash-panel:last-child{margin-bottom:0}
@media(max-width:640px){.graph-controls-stack .graph-toolbar{flex-direction:column;align-items:stretch}}
</style>
"""
