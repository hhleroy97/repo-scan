"""Post-contract ticket helpers, ``rOpenTickets``, ``rLiveRuns``, and ``rNow`` tab renderer."""

_FRAGMENT = r"""/* __HUB_CONTRACT__ */
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
"""
