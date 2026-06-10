"""Provenance chain slide-up panel for the knowledge dashboard."""

_FRAGMENT = r"""function scoreRingColor(score){
  if(score>=3)return '#3fb96d';
  if(score>=2)return '#4f9cf9';
  if(score>=1)return '#e0a93e';
  return '#e25d5d';
}
function closeGraphChain(){
  document.getElementById('graph-chain')?.classList.remove('open');
}
async function openGraphChain(node){
  if(!node)return;
  let panel=document.getElementById('graph-chain');
  if(!panel){
    panel=document.createElement('div');
    panel.id='graph-chain';
    panel.className='graph-chain';
    panel.innerHTML='<div class="graph-chain-backdrop" onclick="closeGraphChain()"></div><div class="graph-chain-sheet"><div class="graph-chain-bar"><button class="ghost" type="button" onclick="closeGraphChain()">Close</button><span class="title">Provenance chain</span></div><div id="graph-chain-body" class="graph-chain-body"></div></div>';
    document.body.appendChild(panel);
  }
  panel.classList.add('open');
  const body=document.getElementById('graph-chain-body');
  body.innerHTML='<div class="empty">Loading chain…</div>';
  try{
    const data=await api(API_GRAPH_CHAIN+'?id='+encodeURIComponent(node.id));
    body.innerHTML=renderGraphChain(data,node);
  }catch(e){
    body.innerHTML=`<div class="empty">Chain unavailable (${esc(e.message)})</div>`;
  }
}
function renderFreshStrip(r){
  if(r.stale_days==null||r.stale_days<=0)return '';
  return `<div class="dash-fresh-strip"><span class="dim small">stale</span>
    <div class="dash-fresh-bar"><div class="dash-fresh-fill" style="width:${Math.min(100,r.stale_days)}%"></div></div>
    <span class="dim small">${r.stale_days}d behind code</span></div>`;
}
function renderGraphChain(data,node){
  const rows=data.chain||[];
  if(!rows.length)return `<div class="empty">No provenance links for ${esc(node.label||node.id)}</div>`;
  let h=`<div class="dim small" style="margin-bottom:10px">E evidence · L linked · C cited · F fresh</div>`;
  rows.forEach(r=>{
    const label=esc(r.label||r.id);
    const doc=r.doc?` <button class="ghost" type="button" style="padding:4px 8px;font-size:11px" onclick="openDoc('${esc(r.doc)}')">open</button>`:'';
    const gov=r.governance_risk?' <span class="badge warn" style="font-size:10px">approved but unhealthy</span>':'';
    h+=`<div class="graph-chain-row" style="padding-left:${(r.depth||0)*12}px">
      <span class="graph-chain-dot" style="background:${scoreRingColor(r.score||0)}"></span>
      <span style="flex:1">
        <strong>${label}</strong> <span class="dash-sigs">${signalGlyphs(r.signals,r.missing)}</span>${gov}${doc}
        ${renderFreshStrip(r)}
      </span></div>`;
  });
  const obs=window._obsidianVault;
  if(obs&&node.doc){
    h+=`<div class="btnrow" style="margin-top:12px"><a class="ghost" style="text-decoration:none;text-align:center" href="obsidian://open?vault=${encodeURIComponent(obs)}&file=${encodeURIComponent(node.doc)}">Open in Obsidian</a></div>`;
  }
  return h;
}

"""
