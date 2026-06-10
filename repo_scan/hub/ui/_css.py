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
</style>
"""
