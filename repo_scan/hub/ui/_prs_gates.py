"""``tok``, PR merge/fix, ``rFeed``/``rUsage``/``stat``, and Gates tab renderers."""

_FRAGMENT = r"""function tok(n){return n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e3?(n/1e3).toFixed(1)+'k':String(n??0)}
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
function rPRCard(p){
  const ck={passing:['ok','checks passing'],failing:['bad','checks FAILING'],
            pending:['warn','checks running'],none:['','no checks']};
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
    <div class="btnrow">${btns}</div></div>`;
}
function rPRs(){
  const prs=S.prs||[];if(!prs.length)return '';
  return `<div class="section">Pull requests</div>`+prs.map(rPRCard).join('');
}
function rNowPRsAndGates(){
  const prs=S.prs||[];
  const gates=S.gates||[];
  if(!prs.length&&!gates.length)return '';
  let h=`<div class="section">PRs &amp; gates</div>`;
  h+=gates.map((g,gi)=>rGateCard(g,gi)).join('');
  h+=prs.map(rPRCard).join('');
  return h;
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
    const r=await fetch(API_PR_PREFIX+op,{method:'POST',
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
function rGateCard(g,gi){
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
  return `<div class="card" id="gate-${gi}" style="border-color:var(--warn)">
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
}
function rGates(){
  if(!S.gates.length)return `<div class="empty">No gates waiting. All clear.</div>`;
  return S.gates.map((g,gi)=>rGateCard(g,gi)).join('');
}
async function gateDecide(gate,btn,decision){
  const g=S.gates.find(x=>x.gate===gate);if(!g)return;
  const card=btn.closest('.card');
  const key=card?.id||`gate-${gate}`;
  let comment='';
  if(decision==='reject')comment=prompt('Why? (optional)')||'';
  const label=decision==='approve'?'Approving — daemon will resume…':'Rejecting…';
  beginPending(key,label,{btn,btnLabel:label});
  try{await api(API_GATE,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({gate,problem:g.problem,decision,comment})});
    toast(decision==='approve'?'Approved — daemon will resume':'Rejected');
    setTimeout(refresh,800);}
  catch(e){toast('Failed: '+e.message)}
  finally{endPending(key)}
}

"""
