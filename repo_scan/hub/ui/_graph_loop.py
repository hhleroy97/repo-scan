"""Agentic loop — Mermaid diagram with live stage highlights."""

_FRAGMENT = r"""const MERMAID_SRC='/static/mermaid.min.js';
let mermaidReady=false,mermaidLoading=null;
let _lastMermaidSrc='',_lastMermaidSvg='';

function _loopRun(){return(S&&S.live_runs&&S.live_runs[0])||null;}
function _loopPending(){return(S&&S.gates)||[];}
function _loopLiveBanner(){
  const run=_loopRun();
  const gates=_loopPending();
  let h='';
  if(run){
    const tag=run.kind==='act'?'act':'loop';
    h+=`<div class="loop-live"><span class="badge info">${esc(tag)}</span> `;
    h+=`<strong>${esc(run.ticket||run.problem||run.id)}</strong>`;
    if(run.stage)h+=` <span class="dim">· ${esc(run.stage)}</span>`;
    if(run.stage_detail)h+=`<div class="dim small">${esc(run.stage_detail)}</div>`;
    h+=`</div>`;
  }
  if(gates.length){
    h+=`<div class="loop-live loop-wait-banner">${gates.length} gate${gates.length>1?'s':''} waiting: `;
    h+=gates.map(g=>`<span class="badge warn">${esc(g.gate)}</span>`).join(' ');
    h+=`</div>`;
  }
  const lastDone=S&&S.runs&&S.runs.find(r=>r.status==='done'||r.status==='stopped');
  if(lastDone){
    h+=`<div class="dim small" style="margin-top:6px">Last completed: <strong>${esc(lastDone.ticket||lastDone.problem||lastDone.id)}</strong> (${esc(lastDone.status)})</div>`;
  }
  if(!run&&!gates.length)h+=`<div class="dim small">No live loop or act — daemon idle or awaiting ticket.</div>`;
  return h;
}
function ensureMermaid(){
  if(mermaidReady)return Promise.resolve();
  if(mermaidLoading)return mermaidLoading;
  mermaidLoading=new Promise((resolve,reject)=>{
    const s=document.createElement('script');
    s.src=MERMAID_SRC;
    s.async=true;
    s.onload=()=>{
      mermaid.initialize({startOnLoad:false,theme:'dark',securityLevel:'loose',
        flowchart:{htmlLabels:true,curve:'basis',padding:12}});
      mermaidReady=true;
      resolve();
    };
    s.onerror=()=>reject(new Error('mermaid script failed to load'));
    document.head.appendChild(s);
  });
  return mermaidLoading;
}
async function renderAgenticLoopMermaid(){
  const host=document.getElementById('agentic-loop-host');
  const src=document.getElementById('agentic-loop-src');
  if(!host||!src)return;
  const text=(S&&S.agentic_loop_mermaid)||src.textContent||'';
  if(!text.trim()){
    host.innerHTML='<div class="dim small">No diagram source.</div>';
    _lastMermaidSrc='';_lastMermaidSvg='';
    return;
  }
  if(text===_lastMermaidSrc&&_lastMermaidSvg){
    host.innerHTML=`<div class="mermaid-svg">${_lastMermaidSvg}</div>`;
    return;
  }
  if(!_lastMermaidSvg)host.innerHTML='<div class="empty"><span class="pending-spinner"></span> Rendering diagram…</div>';
  try{
    await ensureMermaid();
    const id='agentic-loop-'+Date.now();
    const {svg}=await mermaid.render(id,text);
    _lastMermaidSrc=text;_lastMermaidSvg=svg;
    host.innerHTML=`<div class="mermaid-svg">${svg}</div>`;
  }catch(e){
    host.innerHTML=`<div class="empty">Mermaid render failed (${esc(e.message)})</div>
      <pre class="mermaid-fallback">${esc(text)}</pre>`;
  }
}
function rGraphPipeline(){
  const mmd=(S&&S.agentic_loop_mermaid)||'';
  return `<details class="card loop-card" open><summary class="title" style="cursor:pointer">Agentic loop</summary>
    <div style="margin-top:10px">${_loopLiveBanner()}</div>
    <div class="dim small" style="margin:8px 0">Blue = active stage · Amber = gate waiting · Green = last completed trail</div>
    <pre id="agentic-loop-src" class="mermaid-src" hidden>${esc(mmd)}</pre>
    <div id="agentic-loop-host" class="mermaid-wrap"><div class="empty"><span class="pending-spinner"></span> Loading diagram…</div></div>
  </details>`;
}

"""
