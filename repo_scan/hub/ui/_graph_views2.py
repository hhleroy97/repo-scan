"""Dashboard views 6–9: completeness radar, orphan clusters, change impact,
provenance timeline, plus the composite renderer.

Vault: docs/tickets/tkt-0032
"""

_FRAGMENT = r"""
// ── 6. Doc completeness radar chart ─────────────────────────────────
function rViewCompletenessRadar(){
  const matrix=graphData?.coverage?.signal_matrix;
  if(!matrix)return '';
  const signals=['evidence','linked','cited','fresh'];
  const kinds=['ticket','spec','analysis','source'];
  const kindColors={ticket:'#e0a93e',spec:'#3fb96d',analysis:'#9b7cf6',source:'#8b95a5'};
  const cx=120,cy=120,R=90;
  const angles=signals.map((_,i)=>-Math.PI/2+(2*Math.PI*i/signals.length));
  let svg=`<svg width="100%" viewBox="0 0 240 260" style="display:block;margin:8px auto">`;
  for(let ring=1;ring<=4;ring++){
    const r=R*ring/4;
    const pts=angles.map(a=>`${cx+Math.cos(a)*r},${cy+Math.sin(a)*r}`).join(' ');
    svg+=`<polygon points="${pts}" fill="none" stroke="var(--line)" stroke-width="0.5"/>`;
  }
  angles.forEach((a,i)=>{
    svg+=`<line x1="${cx}" y1="${cy}" x2="${cx+Math.cos(a)*R}" y2="${cy+Math.sin(a)*R}" stroke="var(--line)" stroke-width="0.5"/>`;
    const lx=cx+Math.cos(a)*(R+14);
    const ly=cy+Math.sin(a)*(R+14);
    svg+=`<text x="${lx}" y="${ly}" text-anchor="middle" dominant-baseline="central" fill="var(--dim)" font-size="10" font-weight="600">${signals[i][0].toUpperCase()}</text>`;
  });
  kinds.forEach(kind=>{
    const row=matrix[kind]||{};
    const pts=signals.map((sig,i)=>{
      const cell=row[sig]||{pass:0,total:0};
      const pct=cell.total?cell.pass/cell.total:0;
      const r=pct*R;
      return `${cx+Math.cos(angles[i])*r},${cy+Math.sin(angles[i])*r}`;
    }).join(' ');
    svg+=`<polygon points="${pts}" fill="${kindColors[kind]||'#888'}" fill-opacity="0.15" stroke="${kindColors[kind]||'#888'}" stroke-width="1.5"/>`;
  });
  svg+=`</svg>`;
  const legend=kinds.map(k=>`<span><i style="display:inline-block;width:10px;height:3px;background:${kindColors[k]};margin-right:4px;vertical-align:middle;border-radius:1px"></i>${k}</span>`).join(' ');
  return `<details class="card dash-panel"><summary class="title" style="cursor:pointer">Completeness radar</summary>
    <div class="dim small" style="margin:6px 0">${legend}</div>
    <div class="dim small">E evidence · L linked · C cited · F fresh — each axis 0–100%</div>
    ${svg}
  </details>`;
}

// ── 7. Orphan cluster view (layer toggle) ───────────────────────────
function setOrphanView(on){
  if(on){
    graphLayer='vault';
    graphMissFilter=null;
    window._orphanViewActive=true;
  }else{
    graphLayer='coverage';
    window._orphanViewActive=false;
  }
  graphLayout=null;
  const el=document.getElementById('main');
  if(el&&tab==='dashboard')el.innerHTML=rGraph();
  mountGraph();
}
function rViewOrphanCluster(){
  const nodes=(graphData?.nodes||[]).filter(n=>n.kind!=='code'&&(n.score!=null)&&n.score<=1);
  if(!nodes.length)return '';
  const byKind={};
  nodes.forEach(n=>{byKind[n.kind]=(byKind[n.kind]||0)+1});
  const summary=Object.entries(byKind).map(([k,v])=>`${v} ${k}${v>1?'s':''}`).join(', ');
  const active=window._orphanViewActive;
  return `<div class="card dash-panel">
    <div class="title" style="margin-bottom:6px">Orphan clusters <span class="badge bad">${nodes.length}</span></div>
    <div class="dim small" style="margin-bottom:10px">${summary} scoring 0–1 — these documents need the most attention</div>
    <div class="btnrow">
      <button class="ghost${active?' active':''}" type="button" style="font-size:12px" onclick="setOrphanView(${active?'false':'true'})">${active?'Exit orphan view':'Show only orphans on graph'}</button>
    </div>
  </div>`;
}

// ── 8. Change impact preview ────────────────────────────────────────
let _impactCache=null,_impactLoading=false;
function rViewChangeImpact(){
  const c=_impactCache;
  if(c&&!c.affected_docs?.length&&!c.changed?.length){
    return `<div class="card dash-panel">
      <div class="title">Change impact</div>
      <div class="dim small">No recent git changes detected (last 5 commits).</div>
    </div>`;
  }
  if(c&&c.affected_docs?.length){
    let rows='';
    c.affected_docs.forEach(d=>{
      rows+=`<li style="padding:8px 0;border-bottom:1px solid var(--line)">
        <div style="display:flex;align-items:center;gap:8px">
          <span class="badge">${d.kind}</span>
          <strong>${esc(d.label)}</strong>
          ${d.doc?`<button class="ghost" type="button" style="padding:4px 8px;font-size:11px;margin-left:auto" onclick="openDoc('${esc(d.doc)}')">open</button>`:''}
        </div>
        <div class="dim small" style="margin-top:4px">Changed: ${d.linked_changed.map(f=>`<code>${esc(f)}</code>`).join(', ')}</div>
      </li>`;
    });
    return `<details class="card dash-panel"><summary class="title" style="cursor:pointer">Change impact <span class="badge warn">${c.affected_docs.length}</span></summary>
      <div class="dim small" style="margin:8px 0">Vault docs whose linked code changed in last 5 commits — review these for accuracy</div>
      <ul class="dash-untracked">${rows}</ul>
    </details>`;
  }
  return `<div class="card dash-panel">
    <div class="title" style="margin-bottom:8px">Change impact</div>
    <div class="dim small" style="margin-bottom:8px">Check which vault docs need review based on recent code changes</div>
    <button class="ghost" type="button" style="font-size:12px" onclick="loadChangeImpact(this)" ${_impactLoading?'disabled':''}>
      ${_impactLoading?'Scanning…':'Check impact'}
    </button>
  </div>`;
}
async function loadChangeImpact(btn){
  _impactLoading=true;
  beginPending('impact','Scanning change impact…',{btn,btnLabel:'Scanning…'});
  try{
    _impactCache=await api(API_PROVENANCE_IMPACT);
    const n=(_impactCache.affected_docs||[]).length;
    toast(n?`${n} doc${n!==1?'s':''} affected by recent changes`:'No docs affected');
  }catch(e){toast('Impact scan failed: '+e.message)}
  finally{_impactLoading=false;endPending('impact')}
  const el=document.getElementById('main');
  if(el&&tab==='dashboard')el.innerHTML=rGraph();
  mountGraph();
}

// ── 9. Provenance timeline ──────────────────────────────────────────
function rViewProvenanceTimeline(){
  const sp=S?.trend_sparkline||[];
  if(sp.length<2)return '';
  const W=300,H=140,P=36;
  const series=[
    {key:'vault_pct',color:'#3fb96d',label:'Vault %',scale:v=>v},
    {key:'files',color:'#4f9cf9',label:'Files',scale:null},
    {key:'untracked',color:'#e25d5d',label:'Untracked',scale:null}
  ];
  let paths='',dots='';
  series.forEach(s=>{
    const raw=sp.map(d=>d[s.key]).filter(v=>v!=null);
    if(raw.length<2)return;
    const mn=Math.min(...raw),mx=Math.max(...raw),rg=mx-mn||1;
    const pts=raw.map((v,i)=>{
      const x=P+(i/(raw.length-1))*W;
      const y=P+H-((v-mn)/rg)*H;
      return `${x},${y}`;
    });
    paths+=`<polyline fill="none" stroke="${s.color}" stroke-width="2" points="${pts.join(' ')}"/>`;
    const lastX=P+((raw.length-1)/(raw.length-1))*W;
    const lastY=P+H-((raw[raw.length-1]-mn)/rg)*H;
    dots+=`<circle cx="${lastX}" cy="${lastY}" r="3.5" fill="${s.color}"/>`;
    dots+=`<text x="${lastX+6}" y="${lastY+4}" fill="${s.color}" font-size="10" font-weight="600">${raw[raw.length-1]}</text>`;
  });
  if(!paths)return '';
  let grid='';
  for(let i=0;i<=4;i++){
    const y=P+H*(1-i/4);
    grid+=`<line x1="${P}" y1="${y}" x2="${W+P}" y2="${y}" stroke="var(--line)" stroke-width="0.5"/>`;
  }
  const labels=sp.map((d,i)=>d.when?.slice(0,10)||'');
  const first=labels[0],last=labels[labels.length-1];
  const xLabels=`<text x="${P}" y="${H+P+16}" fill="var(--dim)" font-size="9">${esc(first)}</text>
    <text x="${W+P}" y="${H+P+16}" fill="var(--dim)" font-size="9" text-anchor="end">${esc(last)}</text>`;
  const legend=series.map(s=>`<span><i style="display:inline-block;width:10px;height:3px;background:${s.color};margin-right:4px;vertical-align:middle;border-radius:1px"></i>${s.label}</span>`).join(' ');
  return `<details class="card dash-panel" open><summary class="title" style="cursor:pointer">Provenance timeline (${sp.length} scans)</summary>
    <div class="dim small" style="margin:6px 0">${legend}</div>
    <div class="dim small">How vault health tracks code changes over scan history</div>
    <svg width="100%" viewBox="0 0 ${W+P*2} ${H+P*2+10}" style="display:block;margin-top:6px">${grid}${paths}${dots}${xLabels}</svg>
  </details>`;
}

// ── Composite: all additional views ─────────────────────────────────
function rGraphAdditionalViews(){
  return rViewDirCoverage()
    +rViewProvenanceFlow()
    +rViewCompletenessRadar()
    +rViewGovernanceRisk()
    +rViewStaleQueue()
    +rViewCitationDensity()
    +rViewOrphanCluster()
    +rViewChangeImpact()
    +rViewProvenanceTimeline();
}

"""
