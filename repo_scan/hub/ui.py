"""The dashboard: one self-contained mobile-first HTML page.

No build step, no framework, no CDN — everything inline so it works on a
phone over Tailscale with zero external requests. The page polls /api/state
and renders four tabs: Now (stats + runs), Gates, Tickets, Activity.
"""

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0e1116">
<title>repo-scan hub</title>
<style>
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
header .sub{color:var(--dim);font-size:12px;margin-left:auto}
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
</style>
</head>
<body>
<header><h1 id="repo">repo-scan</h1><span class="sub" id="meta"></span></header>
<main id="main"><div class="empty">Loading…</div></main>
<nav>
  <a href="#now" class="active" data-tab="now">Now</a>
  <a href="#gates" data-tab="gates">Gates<span class="n" id="ngates" hidden></span></a>
  <a href="#tickets" data-tab="tickets">Tickets<span class="n" id="ntickets" hidden></span></a>
  <a href="#activity" data-tab="activity">Activity</a>
</nav>
<div id="viewer"><div class="bar">
  <button class="ghost" style="flex:none;padding:7px 14px" onclick="closeDoc()">Close</button>
  <span class="path" id="docpath"></span></div><pre id="doctext"></pre></div>
<div id="toast"></div>
<script>
let S=null, tab=location.hash.replace('#','')||'now';

function esc(s){return String(s??'').replace(/[&<>"]/g,
  c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function toast(m){const t=document.getElementById('toast');t.textContent=m;
  t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2200)}
async function api(path,opts){const r=await fetch(path,opts);
  if(!r.ok)throw new Error((await r.json()).error||r.status);return r.json()}

async function refresh(){
  try{S=await api('/api/state');render()}
  catch(e){document.getElementById('main').innerHTML=
    `<div class="empty">Cannot reach hub (${esc(e.message)})</div>`}
}

function setTab(t){tab=t;
  document.querySelectorAll('nav a').forEach(a=>
    a.classList.toggle('active',a.dataset.tab===t));
  render()}
document.querySelectorAll('nav a').forEach(a=>
  a.addEventListener('click',e=>setTab(a.dataset.tab)));

function render(){
  if(!S)return;
  document.getElementById('repo').textContent=S.repo.name;
  document.getElementById('meta').textContent=
    `${S.repo.branch} · v${S.version}`;
  const open=S.tickets.filter(t=>t.status==='proposed').length;
  badge('ngates',S.gates.length);badge('ntickets',open);
  const m=document.getElementById('main');
  m.innerHTML={now:rNow,gates:rGates,tickets:rTickets,activity:rActivity}[tab]();
}
function badge(id,n){const e=document.getElementById(id);
  e.hidden=!n;e.textContent=n}

function rNow(){
  const sc=S.scan||{};
  let h='';
  if(S.gates.length)
    h+=`<div class="card" style="border-color:var(--warn)">
      <div class="title">${S.gates.length} gate(s) waiting on you</div>
      <div class="dim">${esc(S.gates[0].summary).slice(0,140)}</div>
      <div class="btnrow"><button class="ghost" onclick="setTab('gates')">Review</button></div></div>`;
  h+=`<div class="grid">
    ${stat(sc.files??'–','Source files')}
    ${stat((sc.lines??0).toLocaleString(),'Lines')}
    ${stat(sc.hotspots??'–','CC hotspots')}
    ${stat(sc.critical??'–','Critical files')}
  </div>`;
  if(S.runs.length){
    h+=`<div class="section">Runs</div><div class="card">`+
      S.runs.map(r=>`<div class="run"><span class="dot ${r.status}"></span>
        <span style="flex:1">${esc(r.problem).slice(0,90)}</span>
        <span class="badge">${r.status}${r.gate?': '+r.gate:''}</span></div>`).join('')+
      `</div>`;
  }
  h+=rUsage();
  h+=`<div class="dim small" style="text-align:center;margin-top:14px">
    last scan ${esc(sc.generated_at||'never')} · refreshed ${esc(S.now)}</div>`;
  return h;
}
function tok(n){return n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e3?(n/1e3).toFixed(1)+'k':String(n??0)}
function rUsage(){
  const u=S.usage;if(!u||!u.total||!u.total.calls)return '';
  const row=(name,a)=>`<div class="run"><span style="flex:1">${esc(name)}</span>
    <span class="dim small">${a.calls} calls</span>
    <span class="badge">${tok(a.input_tokens)} in · ${tok(a.output_tokens)} out</span></div>`;
  let h=`<div class="section">LLM usage${u.total.estimated?' (some estimated)':''}</div><div class="card">`;
  h+=row('Today',u.today)+row('All time',u.total);
  h+=Object.entries(u.by_model).map(([m,a])=>row(m,a)).join('');
  if(u.total.cost_usd!=null)h+=`<div class="dim small" style="margin-top:6px">reported cost: $${u.total.cost_usd}</div>`;
  h+=`</div>`;
  return h;
}
function stat(v,l){return `<div class="card stat"><div class="v">${v}</div>
  <div class="l">${l}</div></div>`}

function rGates(){
  if(!S.gates.length)return `<div class="empty">No gates waiting. All clear.</div>`;
  return S.gates.map(g=>{
    const d=g.detail||{};
    let body='';
    if(d.confidence)body+=`<span class="badge info">confidence: ${esc(d.confidence)}</span> `;
    if(d.audit_verdict)body+=`<span class="badge ${d.audit_verdict==='pass'?'ok':'warn'}">audit: ${esc(d.audit_verdict)}</span>`;
    if((d.findings||[]).length)body+=`<div class="section">Findings</div><ul class="plain">`+
      d.findings.map(f=>`<li>${esc(f).slice(0,160)}</li>`).join('')+`</ul>`;
    if((d.issues||[]).length)body+=`<div class="section">Audit issues</div><ul class="plain">`+
      d.issues.map(f=>`<li>${esc(f).slice(0,160)}</li>`).join('')+`</ul>`;
    if((d.risks||[]).length)body+=`<div class="section">Risks</div><ul class="plain">`+
      d.risks.map(f=>`<li>${esc(f).slice(0,160)}</li>`).join('')+`</ul>`;
    return `<div class="card">
      <span class="badge warn">${esc(g.gate)}</span>
      <div class="title" style="margin-top:8px">${esc(g.summary).slice(0,200)}</div>
      <div class="dim small">${esc(g.problem).slice(0,160)}</div>
      ${body}
      ${d.doc?`<div class="btnrow"><button class="ghost" onclick="openDoc('${esc(d.doc)}')">Read full document</button></div>`:''}
      <div class="btnrow">
        <button class="approve" onclick="gateDecide('${esc(g.gate)}',this,'approve')">Approve</button>
        <button class="reject" onclick="gateDecide('${esc(g.gate)}',this,'reject')">Reject</button>
      </div></div>`;
  }).join('');
}
async function gateDecide(gate,btn,decision){
  const g=S.gates.find(x=>x.gate===gate);if(!g)return;
  let comment='';
  if(decision==='reject')comment=prompt('Why? (optional)')||'';
  btn.disabled=true;
  try{await api('/api/gate',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({gate,problem:g.problem,decision,comment})});
    toast(decision==='approve'?'Approved — daemon will resume':'Rejected');
    setTimeout(refresh,800);}
  catch(e){toast('Failed: '+e.message);btn.disabled=false}
}

function rTickets(){
  const order={proposed:0,approved:1,'in-progress':2,done:3,rejected:4};
  const ts=[...S.tickets].sort((a,b)=>(order[a.status]??9)-(order[b.status]??9));
  if(!ts.length)return `<div class="empty">No tickets yet — run a scan.</div>`;
  const cls={proposed:'warn',approved:'info','in-progress':'info',done:'ok',rejected:'bad'};
  return ts.map(t=>`<div class="card">
    <span class="badge ${cls[t.status]||''}">${esc(t.status)}</span>
    ${t.kind?`<span class="badge">${esc(t.kind)}</span>`:''}
    ${t.priority?`<span class="badge">${esc(t.priority)}</span>`:''}
    <div class="title" style="margin-top:8px">${esc(t.title)}</div>
    ${t.why?`<div class="dim small">${esc(t.why).slice(0,180)}</div>`:''}
    ${actions(t)}</div>`).join('');
}
function actions(t){
  const b=(a,l,c)=>`<button class="${c||'ghost'}" onclick="ticketAct('${t.id}','${a}',this)">${l}</button>`;
  if(t.status==='proposed')return `<div class="btnrow">${b('approve','Approve','approve')}${b('reject','Reject','reject')}</div>`;
  if(t.status==='approved')return `<div class="btnrow">${b('start','Mark in-progress')}${b('reject','Reject','reject')}</div>`;
  if(t.status==='in-progress')return `<div class="btnrow">${b('done','Mark done','approve')}</div>`;
  return '';
}
async function ticketAct(id,action,btn){
  btn.disabled=true;
  try{await api('/api/ticket',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id,action})});toast(`${id} ${action}`);setTimeout(refresh,500)}
  catch(e){toast('Failed: '+e.message);btn.disabled=false}
}

function rActivity(){
  if(!S.activity.length)return `<div class="empty">No decisions recorded yet.</div>`;
  return `<div class="card">`+S.activity.map(a=>{
    const cls=/approved|auto/.test(a.decision)?'ok':(/rejected|denied/.test(a.decision)?'bad':'warn');
    return `<div class="run"><span class="dot ${cls==='ok'?'done':(cls==='bad'?'failed':'waiting-on-gate')}"></span>
      <span style="flex:1">${esc(a.summary).slice(0,90)}<br>
      <span class="dim small">${esc(a.when)} · ${esc(a.gate)}</span></span>
      <span class="badge ${cls}">${esc(a.decision)}</span></div>`}).join('')+`</div>`;
}

async function openDoc(rel){
  try{const d=await api('/api/doc?path='+encodeURIComponent(rel));
    document.getElementById('docpath').textContent=d.path;
    document.getElementById('doctext').textContent=d.text;
    document.getElementById('viewer').classList.add('open')}
  catch(e){toast('Cannot load doc: '+e.message)}
}
function closeDoc(){document.getElementById('viewer').classList.remove('open')}

refresh();setInterval(refresh,12000);
</script>
</body>
</html>
"""
