"""Shared dashboard JS: helpers, polling, SSE, ``refresh``, ``render``, contract splice point."""

_FRAGMENT = r"""let _hashTab=location.hash.replace('#','')||'now';
if(_hashTab==='graph')_hashTab='dashboard';
let S=null, tab=_hashTab;
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
  sse=new EventSource(API_EVENTS);
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
  try{S=await api(API_STATE);
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

function setTab(t){tab=t==='graph'?'dashboard':t;
  if(location.hash!=='#'+tab)location.hash=tab;
  document.querySelectorAll('nav a').forEach(a=>
    a.classList.toggle('active',a.dataset.tab===tab));
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
  if(tab==='dashboard'&&graphData&&!force){
    _updateLoopBanner();
    mountGraph();
    return;
  }
  m.innerHTML={now:rNow,gates:rGates,tickets:rTickets,activity:rActivity,dashboard:rGraph}[tab]();
  if(tab==='dashboard')mountGraph();
}
function _updateLoopBanner(){
  const el=document.querySelector('.loop-card>div:first-of-type');
  if(el)el.innerHTML=_loopLiveBanner();
}
function badge(id,n){const e=document.getElementById(id);
  e.hidden=!n;e.textContent=n}

"""
