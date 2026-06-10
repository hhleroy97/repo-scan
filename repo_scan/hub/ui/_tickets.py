"""Tickets tab: ``rTickets``, ``ticketCard``, and ticket actions."""

_FRAGMENT = r"""function rTickets(){
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
  try{await api(API_TICKET,{method:'PATCH',headers:{'Content-Type':'application/json'},
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
  try{const r=await api(API_TICKET_NEW,{method:'POST',headers:{'Content-Type':'application/json'},
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
  try{await api(API_TICKET,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id,action})});toast(`${id} ${action}`);setTimeout(refresh,500)}
  catch(e){toast('Failed: '+e.message)}
  finally{endPending(key)}
}

"""
