"""The dashboard: one self-contained mobile-first HTML page.

No build step, no framework, no CDN — everything inline so it works on a
phone over Tailscale with zero external requests. The page polls /api/state
and renders four tabs: Now (open-ticket summary, stats, runs, agent feed),
Gates, Tickets, Activity.

Ticket cards use three-tier disclosure (aligned with ``OPEN_STATUSES`` on the
Now tab and Tickets tab): glance row (``card.outcome``, ``card.why_line``,
status, priority, criteria count), tap-to-expand checklist (and inline
criteria editor when not ready), then full markdown via ``openDoc``.
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
</style>
</head>
<body>
<header><h1 id="repo">repo-scan</h1>
<span class="sub"><span id="status-pill" hidden></span><span id="meta"></span></span></header>
<div id="busy-bar" aria-hidden="true"></div>
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
const pending=new Map();
let refreshDepth=0;

function esc(s){return String(s??'').replace(/[&<>"]/g,
  c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function toast(m){const t=document.getElementById('toast');t.textContent=m;
  t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2200)}
async function api(path,opts){const r=await fetch(path,opts);
  if(!r.ok){const j=await r.json().catch(()=>({}));
    throw new Error(j.error||j.message||r.status)}return r.json()}

function setMainLoading(msg){
  document.getElementById('main').innerHTML=
    `<div class="empty"><span class="pending-spinner" style="display:inline-block;vertical-align:middle;margin-right:8px"></span>${esc(msg)}</div>`;
}
function syncBusyChrome(){
  const pill=document.getElementById('status-pill');
  const bar=document.getElementById('busy-bar');
  const labels=[...pending.values()].map(p=>p.label);
  if(refreshDepth>0)labels.unshift('Refreshing…');
  if(labels.length){
    pill.hidden=false;
    pill.textContent=labels[labels.length-1];
    bar.classList.add('active');
  }else{
    pill.hidden=true;
    bar.classList.remove('active');
  }
  document.querySelectorAll('.card.card-pending').forEach(el=>{
    if(!pending.has(el.id)){
      el.classList.remove('card-pending');
      el.querySelector('.pending-overlay')?.remove();
    }
  });
  pending.forEach((p,key)=>{
    const el=document.getElementById(key);
    if(!el)return;
    el.classList.add('card-pending');
    let ov=el.querySelector('.pending-overlay');
    if(!ov){
      ov=document.createElement('div');
      ov.className='pending-overlay';
      ov.innerHTML='<span class="pending-spinner"></span><span></span>';
      el.appendChild(ov);
    }
    ov.querySelector('span:last-child').textContent=p.label;
  });
}
function beginPending(key,label,{btn,btnLabel}={}){
  pending.set(key,{label,btn,btnLabel:btnLabel||label});
  if(btn){
    btn.disabled=true;
    if(!btn.dataset.prevText)btn.dataset.prevText=btn.textContent;
    btn.textContent=btnLabel||label;
  }
  syncBusyChrome();
}
function endPending(key){
  const p=pending.get(key);
  if(p?.btn){
    btnRestore(p.btn);
  }
  pending.delete(key);
  syncBusyChrome();
}
function btnRestore(btn){
  btn.disabled=false;
  if(btn.dataset.prevText){
    btn.textContent=btn.dataset.prevText;
    delete btn.dataset.prevText;
  }
}

let pollMs=12000,pollTimer=null,sse=null,sseOk=false,sseRetry=null;
function schedulePoll(){
  const live=(S&&S.live_runs)||[];
  let next;
  if(sseOk){
    next=live.length?12000:30000;
  }else{
    next=live.length?3000:12000;
  }
  if(next===pollMs&&pollTimer)return;
  pollMs=next;
  if(pollTimer)clearInterval(pollTimer);
  pollTimer=setInterval(refresh,pollMs);
}
function connectSSE(){
  if(sse||typeof EventSource==='undefined')return;
  sse=new EventSource('/api/events');
  sse.onopen=()=>{sseOk=true;if(sseRetry){clearTimeout(sseRetry);sseRetry=null}schedulePoll()};
  sse.onmessage=(e)=>{
    try{
      const msg=JSON.parse(e.data);
      if(msg.type==='connected')return;
      refresh();
    }catch(_){refresh()}
  };
  sse.onerror=()=>{
    sseOk=false;
    sse.close();
    sse=null;
    schedulePoll();
    if(!sseRetry)sseRetry=setTimeout(connectSSE,5000);
  };
}
async function refresh(){
  const initial=!S;
  refreshDepth++;
  syncBusyChrome();
  if(initial)setMainLoading('Loading dashboard…');
  try{S=await api('/api/state');
    // hub restarted with new code -> pull fresh HTML/JS (unless mid-form)
    if(S.boot&&window._boot&&window._boot!==S.boot&&!formBusy()){location.reload();return}
    window._boot=S.boot;
    applyPrLast();
    render();
    schedulePoll();
    syncBusyChrome()}
  catch(e){document.getElementById('main').innerHTML=
    `<div class="empty">Cannot reach hub (${esc(e.message)})</div>`}
  finally{refreshDepth=Math.max(0,refreshDepth-1);syncBusyChrome()}
}

function setTab(t){tab=t;
  document.querySelectorAll('nav a').forEach(a=>
    a.classList.toggle('active',a.dataset.tab===t));
  render(true)}
document.querySelectorAll('nav a').forEach(a=>
  a.addEventListener('click',e=>setTab(a.dataset.tab)));

function formBusy(){
  // never repaint over someone mid-thought: a focused field or any
  // unsubmitted composer text holds the current DOM in place
  const a=document.activeElement;
  if(a&&['INPUT','TEXTAREA','SELECT'].includes(a.tagName)&&a.closest('#main'))return true;
  return ['nt-title','nt-why','nt-criteria'].some(id=>{
    const e=document.getElementById(id);return e&&e.value.trim()});
}
function render(force){
  if(!S)return;
  document.getElementById('repo').textContent=S.repo.name;
  document.getElementById('meta').textContent=
    `${S.repo.branch} · v${S.version}`;
  const open=S.tickets.filter(t=>t.status==='proposed').length;
  badge('ngates',S.gates.length);badge('ntickets',open);
  if(!force&&formBusy())return;
  const m=document.getElementById('main');
  m.innerHTML={now:rNow,gates:rGates,tickets:rTickets,activity:rActivity}[tab]();
}
function badge(id,n){const e=document.getElementById(id);
  e.hidden=!n;e.textContent=n}

// Keep OPEN_TICKET_STATUSES aligned with repo_scan.tickets.OPEN_STATUSES.
const OPEN_TICKET_STATUSES=new Set(['proposed','approved','in-progress']);
const TICKET_STATUS_ORDER={proposed:0,approved:1,'in-progress':2,done:3,rejected:4};
const TICKET_BADGE_CLS={proposed:'warn',approved:'info','in-progress':'info',done:'ok',rejected:'bad'};
function filterOpenTickets(tickets){return tickets.filter(t=>OPEN_TICKET_STATUSES.has(t.status))}
function sortTickets(tickets){
  return [...tickets].sort((a,b)=>(TICKET_STATUS_ORDER[a.status]??9)-(TICKET_STATUS_ORDER[b.status]??9))}

function ticketHeadline(t){
  const c=t.card||{};
  return c.outcome||t.title||'';
}
function ticketWhyLine(t){
  const c=t.card||{};
  return c.why_line||'';
}
function rOpenTickets(){
  const open=sortTickets(filterOpenTickets(S.tickets));
  if(!open.length)return '';
  let h=`<div class="section">Open tickets (${open.length})</div><div class="card">`;
  h+=open.map(t=>`<div class="run">
    <span class="badge ${TICKET_BADGE_CLS[t.status]||''}">${esc(t.status)}</span>
    ${t.priority?`<span class="badge">${esc(t.priority)}</span>`:''}
    <span class="badge">${t.criteria_count||0} criteria</span>
    <span style="flex:1"><span class="dim small">${esc(t.id)}</span> ${esc(ticketHeadline(t)).slice(0,90)}
    ${ticketWhyLine(t)?`<br><span class="dim small">${esc(ticketWhyLine(t)).slice(0,100)}</span>`:''}</span>
    </div>`).join('');
  h+=`</div><div class="btnrow"><button class="ghost" onclick="setTab('tickets')">View all</button></div>`;
  return h;
}

function rLiveRuns(){
  const live=S.live_runs||[];
  if(!live.length)return '';
  let h=`<div class="section">Live now (${live.length})</div>`;
  live.forEach(r=>{
    const gate=r.status==='waiting-on-gate'&&r.gate
      ?`<div class="btnrow" style="margin-top:8px"><button class="ghost" onclick="setTab('gates')">Gate: ${esc(r.gate)}</button></div>`:'';
    const ev=(S.events||[]).find(e=>r.problem&&e.summary&&e.summary.includes(r.problem.slice(0,40)));
    const evLine=ev?`<div class="dim small">${esc(ev.summary).slice(0,100)}</div>`:'';
    h+=`<div class="card" style="border-color:var(--accent)">
      <div style="display:flex;align-items:flex-start;gap:10px">
        <span class="dot ${r.status}" style="width:12px;height:12px;margin-top:4px;flex:none"></span>
        <div style="flex:1">
          <div class="title">${esc(r.stage||r.status)}</div>
          ${r.ticket?`<span class="badge info">${esc(r.ticket)}</span>`:''}
          <span class="badge">${esc(r.kind||'run')}</span>
          ${r.stage_detail?`<div class="dim small" style="margin-top:6px">${esc(r.stage_detail)}</div>`:''}
          <div class="dim small" style="margin-top:4px">${esc(r.problem).slice(0,90)}</div>
          ${evLine}${gate}
        </div>
      </div></div>`;
  });
  return h;
}

function rNow(){
  const sc=S.scan||{};
  let h=rLiveRuns();
  if(S.gates.length){
    h+=`<div class="card" style="border-color:var(--warn)">
      <div class="title">${S.gates.length} gate(s) waiting on you</div>
      <div class="dim">${esc(S.gates[0].summary).slice(0,140)}</div>
      <div class="btnrow"><button class="ghost" onclick="setTab('gates')">Review</button></div></div>`;
    h+=rOpenTickets();
  }
  h+=`<div class="grid">
    ${stat(sc.files??'–','Source files')}
    ${stat((sc.lines??0).toLocaleString(),'Lines')}
    ${stat(sc.hotspots??'–','CC hotspots')}
    ${stat(sc.critical??'–','Critical files')}
  </div>`;
  if(!S.gates.length)h+=rOpenTickets();
  if(S.runs.length){
    h+=`<div class="section">Runs</div><div class="card">`+
      S.runs.map(r=>{
        const live=['running','queued'].includes(r.status);
        const stage=r.stage?`<br><span class="dim small">${live?'&#9654; ':''}${esc(r.stage)}${r.stage_detail?' — '+esc(r.stage_detail):''}</span>`:'';
        return `<div class="run"><span class="dot ${r.status}"></span>
        <span style="flex:1">${esc(r.problem).slice(0,90)}${stage}</span>
        <span class="badge">${r.status}${r.gate?': '+r.gate:''}</span></div>`}).join('')+
      `</div>`;
  }
  h+=rPRs();
  h+=rFeed();
  h+=rUsage();
  h+=`<div class="dim small" style="text-align:center;margin-top:14px">
    last scan ${esc(sc.generated_at||'never')} · refreshed ${esc(S.now)}</div>`;
  return h;
}
function tok(n){return n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e3?(n/1e3).toFixed(1)+'k':String(n??0)}
const prLast={};
function mergePrResult(number,j){
  if(!j)return;
  prLast[number]={message:j.message||'',diagnosis:j.diagnosis||{},
    fix_started:!!j.fix_started,at:Date.now()};
  const pr=(S.prs||[]).find(p=>p.number===number);
  if(!pr)return;
  pr.diagnosis={...(pr.diagnosis||{}),...(j.diagnosis||{})};
  if(j.fix_started&&pr.diagnosis)pr.diagnosis.fix_started=true;
  if(j.message)pr.diagnosis.status_note=j.message;
}
function applyPrLast(){
  (S.prs||[]).forEach(p=>{
    const last=prLast[p.number];if(!last)return;
    p.diagnosis={...(p.diagnosis||{}),...last.diagnosis};
    if(!p.diagnosis.status_note)p.diagnosis.status_note=last.message;
    if(last.fix_started)p.diagnosis.fix_started=true;
  });
}
function prDiagBlock(d){
  if(!d)return '';
  let h='';
  if(d.status_note)
    h+=`<div class="small" style="margin-top:6px;color:var(--accent)">${esc(d.status_note)}</div>`;
  if(!d.kind)return h;
  h+=`<div class="dim small" style="margin-top:8px;white-space:pre-wrap;max-height:120px;overflow:auto">`;
  if(d.kind==='conflict'){
    const files=(d.conflict_files||[]).join(', ')||'(probing…)';
    h+=`<strong>Conflicts</strong> in ${esc(files)}`;
    if(d.excerpt)h+=`\n${esc(d.excerpt.slice(0,600))}`;
  }else if(d.kind==='tests'){
    const names=(d.failed_checks||[]).map(c=>c.name).filter(Boolean).join(', ');
    h+=`<strong>CI failing</strong>${names?' — '+esc(names):''}`;
    if(d.run_url)h+=` <a href="${esc(d.run_url)}" target="_blank" rel="noopener">run</a>`;
    if(d.log_tail)h+=`\n${esc(d.log_tail.slice(-800))}`;
    if(d.fix_status==='pushed')h+=`\n✓ fix pushed (${esc(d.fix_commit||'')})`;
    else if(d.fix_started)h+=`\n agent fixing…`;
  }
  if(d.updated_at)h+=`\n<span class="dim">${esc(d.updated_at)}</span>`;
  return h+`</div>`;
}
function prShowFixBtn(p){
  const d=p.diagnosis||{};
  if(p.checks==='failing'||p.mergeable==='CONFLICTING')return true;
  if(d.fix_started&&d.fix_status!=='pushed')return true;
  if(d.kind&&(Date.now()-(prLast[p.number]?.at||0)<300000))return true;
  return false;
}
function rPRs(){
  const prs=S.prs||[];if(!prs.length)return '';
  const ck={passing:['ok','checks passing'],failing:['bad','checks FAILING'],
            pending:['warn','checks running'],none:['','no checks']};
  return `<div class="section">Pull requests</div>`+prs.map(p=>{
    const [cls,label]=ck[p.checks]||['',p.checks];
    const conflict=p.mergeable==='CONFLICTING';
    const d=p.diagnosis||{};
    let btns=`<a class="ghost" style="text-decoration:none;text-align:center" href="${esc(p.url)}" target="_blank" rel="noopener">View</a>`;
    if(prShowFixBtn(p))
      btns+=`<button class="ghost" onclick="prAct('update',${p.number},this)">Fix &amp; update</button>`;
    btns+=`<button class="approve" ${conflict?'disabled':''} onclick="prMerge(${p.number},'${esc(p.ticket||'')}',this)">Merge</button>`;
    const border=p.checks==='failing'||conflict?'style="border-color:var(--bad)"':'';
    return `<div class="card" ${border} id="pr-${p.number}">
      <span class="badge ${cls}">${label}</span>
      ${p.ticket?`<span class="badge">${esc(p.ticket)}</span>`:''}
      ${conflict?`<span class="badge bad">conflicts</span>`:''}
      ${p.draft?`<span class="badge">draft</span>`:''}
      <div class="title" style="margin-top:8px">#${p.number} ${esc(p.title)}</div>
      <div class="dim small">${esc(p.branch)}</div>
      ${prDiagBlock(d)}
      <div class="btnrow">${btns}</div></div>`}).join('');
}
function prMerge(number,ticket,btn){
  const failing=(S.prs.find(p=>p.number===number)||{}).checks==='failing';
  if(!confirm(`Squash-merge PR #${number}${ticket?' ('+ticket+')':''}`
    +(failing?' — CHECKS ARE FAILING':'')+'?'))return;
  prAct('merge',number,btn);
}
async function prAct(op,number,btn){
  const key=`pr-${number}`;
  const label=op==='merge'?'Merging & verifying…':'Diagnosing & fixing…';
  beginPending(key,label,{btn,btnLabel:label});
  let keepPending=false;
  try{
    const r=await fetch('/api/pr/'+op,{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({number})});
    const j=await r.json().catch(()=>({}));
    if(!r.ok&&!j.message&&!j.diagnosis)
      throw new Error(j.error||r.status);
    mergePrResult(number,j);
    toast(j.message||(j.ok?'done':'see PR card'));
    if(j.fix_started){
      beginPending(key,'Agent fixing in background…',{btn,btnLabel:'Working…'});
      render(true);
      setTimeout(()=>{endPending(key);refresh()},8000);
      keepPending=true;
      return;
    }
    render(true);
    setTimeout(refresh,2500);
  }catch(e){toast('Failed: '+e.message)}
  finally{if(!keepPending)endPending(key)}
}
function rFeed(){
  const ev=S.events||[];if(!ev.length)return '';
  const icon={stage:'&#9654;',llm:'&#9889;',run:'&#10003;',scan:'&#8635;'};
  return `<div class="section">Agent feed</div><div class="card">`+
    ev.map(e=>`<div class="run"><span class="dim small" style="flex:none;width:42px">${esc((e.when||'').slice(11,16))}</span>
      <span style="flex:1" class="small">${icon[e.kind]||'·'} ${esc(e.text)}</span></div>`).join('')+
    `</div>`;
}
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

function toggleGate(gi){
  window._gateOpen=window._gateOpen===gi?null:gi;
  render(true);
}
function rGateDrawer(g){
  const dr=g.drawer||{};
  if(!dr.excerpt&&!dr.criteria?.length&&!dr.stale_warning&&!dr.analysis_doc)return '';
  let h='<div class="gate-drawer">';
  if(dr.stale_warning)h+=`<div class="hint">${esc(dr.stale_warning)}</div>`;
  if(dr.ticket_id)h+=`<span class="badge info">${esc(dr.ticket_id)}</span> `;
  if(dr.analysis_doc)
    h+=`<div class="btnrow"><button class="ghost" onclick="event.stopPropagation();openDoc('${esc(dr.analysis_doc)}')">Analysis</button></div>`;
  if(dr.criteria?.length){
    h+=`<div class="section">Acceptance criteria</div><ul class="crit-list">`;
    h+=dr.criteria.map((x,i)=>`<li class="${dr.criteria_checked?.[i]?'done':''}">${esc(x)}</li>`).join('');
    h+=`</ul>`;
  }
  if(dr.excerpt)h+=`<pre class="excerpt">${esc(dr.excerpt)}</pre>`;
  return h+`</div>`;
}
function rGates(){
  if(!S.gates.length)return `<div class="empty">No gates waiting. All clear.</div>`;
  return S.gates.map((g,gi)=>{
    const d=g.detail||{};
    const expanded=window._gateOpen===gi;
    let body='';
    if(expanded){
      if(d.confidence)body+=`<span class="badge info">confidence: ${esc(d.confidence)}</span> `;
      if(d.audit_verdict)body+=`<span class="badge ${d.audit_verdict==='pass'?'ok':'warn'}">audit: ${esc(d.audit_verdict)}</span>`;
      if((d.findings||[]).length)body+=`<div class="section">Findings</div><ul class="plain">`+
        d.findings.map(f=>`<li>${esc(f).slice(0,160)}</li>`).join('')+`</ul>`;
      if((d.issues||[]).length)body+=`<div class="section">Audit issues</div><ul class="plain">`+
        d.issues.map(f=>`<li>${esc(f).slice(0,160)}</li>`).join('')+`</ul>`;
      if((d.risks||[]).length)body+=`<div class="section">Risks</div><ul class="plain">`+
        d.risks.map(f=>`<li>${esc(f).slice(0,160)}</li>`).join('')+`</ul>`;
      body+=rGateDrawer(g);
    }
    return `<div class="card" id="gate-${gi}">
      <div class="gate-glance" onclick="toggleGate(${gi})">
        <span class="badge warn">${esc(g.gate)}</span>
        <div class="title" style="margin-top:8px">${esc(g.summary).slice(0,200)}</div>
        <div class="dim small">${esc(g.problem).slice(0,160)}</div>
        <div class="dim small" style="margin-top:4px">${expanded?'tap to collapse':'tap for spec + criteria'}</div>
      </div>
      ${body}
      ${expanded&&d.doc?`<div class="btnrow"><button class="ghost" onclick="openDoc('${esc(d.doc)}')">Read full document</button></div>`:''}
      <div class="btnrow">
        <button class="approve" onclick="gateDecide('${esc(g.gate)}',this,'approve')">Approve</button>
        <button class="reject" onclick="gateDecide('${esc(g.gate)}',this,'reject')">Reject</button>
      </div></div>`;
  }).join('');
}
async function gateDecide(gate,btn,decision){
  const g=S.gates.find(x=>x.gate===gate);if(!g)return;
  const card=btn.closest('.card');
  const key=card?.id||`gate-${gate}`;
  let comment='';
  if(decision==='reject')comment=prompt('Why? (optional)')||'';
  const label=decision==='approve'?'Approving — daemon will resume…':'Rejecting…';
  beginPending(key,label,{btn,btnLabel:label});
  try{await api('/api/gate',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({gate,problem:g.problem,decision,comment})});
    toast(decision==='approve'?'Approved — daemon will resume':'Rejected');
    setTimeout(refresh,800);}
  catch(e){toast('Failed: '+e.message)}
  finally{endPending(key)}
}

function rTickets(){
  const ts=sortTickets(S.tickets);
  let h=`<div class="card" id="new-ticket">
    <div class="title">New idea</div>
    <input id="nt-title" placeholder="What should be built or changed?" style="width:100%;margin:8px 0;padding:10px;border-radius:9px;border:1px solid var(--line);background:var(--panel2);color:var(--text);font-size:14px">
    <textarea id="nt-why" placeholder="Why? (optional)" rows="2" style="width:100%;margin-bottom:8px;padding:10px;border-radius:9px;border:1px solid var(--line);background:var(--panel2);color:var(--text);font-size:14px;font-family:inherit"></textarea>
    <textarea id="nt-criteria" placeholder="Acceptance criteria, one per line (drive the spec + tests)" rows="2" style="width:100%;margin-bottom:8px;padding:10px;border-radius:9px;border:1px solid var(--line);background:var(--panel2);color:var(--text);font-size:14px;font-family:inherit"></textarea>
    <div class="btnrow">
      <select id="nt-priority" style="flex:1;border-radius:9px;border:1px solid var(--line);background:var(--panel2);color:var(--text);padding:10px;font-size:14px">
        <option value="medium">medium</option><option value="high">high</option><option value="low">low</option>
      </select>
      <button class="approve" onclick="newTicket(this)">Create ticket</button>
    </div></div>`;
  if(!ts.length)return h+`<div class="empty">No tickets yet — run a scan or capture an idea above.</div>`;
  h+=ts.map(t=>ticketCard(t)).join('');
  return h;
}
function ticketCard(t){
  const c=t.card||{};
  const expanded=window._ticketOpen===t.id;
  const crit=(t.criteria||[]);
  let body=`<div class="card" id="ticket-${t.id}">
    <div class="ticket-glance" onclick="toggleTicket('${t.id}')">
      <span class="badge ${TICKET_BADGE_CLS[t.status]||''}">${esc(t.status)}</span>
      ${t.kind?`<span class="badge">${esc(t.kind)}</span>`:''}
      ${t.priority?`<span class="badge">${esc(t.priority)}</span>`:''}
      <span class="badge">${t.criteria_count||0} criteria</span>
      <div class="title" style="margin-top:8px">${esc(c.outcome||t.title)}</div>
      ${c.why_line?`<div class="dim small">${esc(c.why_line).slice(0,180)}</div>`:''}
      ${c.story?`<div class="dim small" style="margin-top:4px">${esc(c.story).slice(0,160)}</div>`:''}
      <div class="dim small" style="margin-top:4px">${esc(t.id)} · ${expanded?'tap to collapse':'tap for details'}</div>
    </div>`;
  if(expanded){
    body+=`<div class="ticket-expand">
      ${c.criteria_summary?`<div class="dim small">${esc(c.criteria_summary)}</div>`:''}
      <ul class="crit-list">${crit.map((x,i)=>`<li class="${(t.criteria_checked&&t.criteria_checked[i])?'done':''}">${esc(x)}</li>`).join('')}</ul>
      ${!t.criteria_ready?`<textarea id="crit-${t.id}" rows="3" placeholder="Acceptance criteria, one per line" style="width:100%;margin:8px 0;padding:10px;border-radius:9px;border:1px solid var(--line);background:var(--panel2);color:var(--text);font-size:14px;font-family:inherit">${esc(crit.join('\n'))}</textarea>
      <div class="btnrow"><button class="ghost" onclick="saveCriteria('${t.id}',this)">Save criteria</button></div>`:''}
      <div class="btnrow"><button class="ghost" onclick="openDoc('${t.doc||('tickets/'+t.id+'.md')}')">View ticket</button></div>
      ${actions(t)}
      ${!t.criteria_ready&&t.status==='proposed'?`<div class="hint">Define acceptance criteria before approving.</div>`:''}
    </div>`;
  }
  body+=`</div>`;
  return body;
}
function toggleTicket(id){
  window._ticketOpen=window._ticketOpen===id?null:id;
  render(true);
}
async function saveCriteria(id,btn){
  const el=document.getElementById('crit-'+id);
  if(!el)return;
  const criteria=el.value.split('\n').map(s=>s.trim()).filter(Boolean);
  if(!criteria.length){toast('Add at least one criterion');return}
  const key=`ticket-${id}`;
  beginPending(key,'Saving criteria…',{btn,btnLabel:'Saving…'});
  try{await api('/api/ticket',{method:'PATCH',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id,criteria})});
    toast('Criteria saved');setTimeout(refresh,500)}
  catch(e){toast('Failed: '+e.message)}
  finally{endPending(key)}
}
async function newTicket(btn){
  const title=document.getElementById('nt-title').value.trim();
  if(!title){toast('Title required');return}
  const criteria=document.getElementById('nt-criteria').value.split('\n').map(s=>s.trim()).filter(Boolean);
  beginPending('new-ticket','Creating ticket…',{btn,btnLabel:'Creating…'});
  try{const r=await api('/api/ticket/new',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({title,why:document.getElementById('nt-why').value,
      priority:document.getElementById('nt-priority').value,criteria})});
    toast(`${r.id} created — approve it to start the loop`);
    ['nt-title','nt-why','nt-criteria'].forEach(id=>document.getElementById(id).value='');
    setTimeout(refresh,500)}
  catch(e){toast('Failed: '+e.message)}
  finally{endPending('new-ticket')}
}
function actions(t){
  const approveDis=(!t.criteria_ready&&t.status==='proposed')?' disabled':'';
  const b=(a,l,c,extra='')=>`<button class="${c||'ghost'}"${extra} onclick="ticketAct('${t.id}','${a}',this)">${l}</button>`;
  if(t.status==='proposed')return `<div class="btnrow">${b('approve','Approve','approve',approveDis)}${b('reject','Reject','reject')}</div>`;
  if(t.status==='approved')return `<div class="btnrow">${b('start','Mark in-progress')}${b('reject','Reject','reject')}</div>`;
  if(t.status==='in-progress')return `<div class="btnrow">${b('done','Mark done','approve')}</div>`;
  return '';
}
async function ticketAct(id,action,btn){
  const key=`ticket-${id}`;
  const labels={approve:'Approving…',reject:'Rejecting…',start:'Starting…',done:'Closing…'};
  const label=labels[action]||'Updating…';
  beginPending(key,label,{btn,btnLabel:label});
  try{await api('/api/ticket',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id,action})});toast(`${id} ${action}`);setTimeout(refresh,500)}
  catch(e){toast('Failed: '+e.message)}
  finally{endPending(key)}
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
  const viewer=document.getElementById('viewer');
  viewer.classList.add('open');
  document.getElementById('docpath').textContent=rel;
  document.getElementById('doctext').innerHTML=
    '<span class="pending-spinner" style="display:inline-block;vertical-align:middle;margin-right:8px"></span>Loading document…';
  try{const d=await api('/api/doc?path='+encodeURIComponent(rel));
    document.getElementById('docpath').textContent=d.path;
    document.getElementById('doctext').textContent=d.text}
  catch(e){viewer.classList.remove('open');toast('Cannot load doc: '+e.message)}
}
function closeDoc(){document.getElementById('viewer').classList.remove('open')}

refresh();
connectSSE();
</script>
</body>
</html>
"""
