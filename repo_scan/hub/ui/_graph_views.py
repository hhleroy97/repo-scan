"""Dashboard views 1–5: directory coverage, provenance flow, governance risk,
citation density, stale queue.

Vault: docs/tickets/tkt-0032
"""

_FRAGMENT = r"""
// ── 1. Coverage heatmap by directory ────────────────────────────────
function rViewDirCoverage(){
  const dirs=graphData?.coverage?.dir_coverage||[];
  if(!dirs.length)return '';
  const maxT=Math.max(1,...dirs.map(d=>d.total));
  let bars='';
  dirs.forEach(d=>{
    const pct=d.total?Math.round(d.tracked/d.total*100):0;
    const w=Math.round(d.total/maxT*100);
    const col=pct>=80?'var(--ok)':pct>=50?'var(--warn)':'var(--bad)';
    bars+=`<div class="hm-row">
      <span class="hm-label mono">${esc(d.dir)}</span>
      <div class="hm-track"><div class="hm-fill" style="width:${w}%;background:${col}"></div></div>
      <span class="hm-pct">${pct}%</span>
      <span class="dim small">${d.tracked}/${d.total}</span>
    </div>`;
  });
  return `<details class="card dash-panel"><summary class="title" style="cursor:pointer">Coverage by directory (${dirs.length})</summary>
    <div class="dim small" style="margin:8px 0">Tracked vs total code files per package — bar width = relative file count</div>
    <div class="hm-grid">${bars}</div>
  </details>`;
}

// ── 2. Provenance flow (Sankey-style) ───────────────────────────────
function rViewProvenanceFlow(){
  if(!graphData)return '';
  const edges=graphData.edges||[];
  const nodes=graphData.nodes||[];
  if(!edges.length)return '';
  const kindOrder=['source','analysis','spec','ticket','code'];
  const kindLabel={source:'Sources',analysis:'Analyses',spec:'Specs',ticket:'Tickets',code:'Code'};
  const kindCount={};
  nodes.forEach(n=>{const k=n.kind;kindCount[k]=(kindCount[k]||0)+1});
  const flowCounts={};
  edges.forEach(e=>{
    const sKind=(e.source||'').split(':')[0];
    const tKind=(e.target||'').split(':')[0];
    if(!sKind||!tKind||sKind===tKind)return;
    const key=sKind+'→'+tKind;
    flowCounts[key]=(flowCounts[key]||0)+1;
  });
  const W=300,H=180,colW=50,gap=(W-colW*kindOrder.length)/(kindOrder.length-1);
  const maxN=Math.max(1,...kindOrder.map(k=>kindCount[k]||0));
  const cols={};
  kindOrder.forEach((k,i)=>{
    const x=i*(colW+gap);
    const h=Math.max(16,((kindCount[k]||0)/maxN)*H);
    const y=(H-h)/2;
    cols[k]={x,y,h,n:kindCount[k]||0};
  });
  let svg=`<svg width="100%" viewBox="0 0 ${W} ${H+40}" style="display:block">`;
  const maxFlow=Math.max(1,...Object.values(flowCounts));
  Object.entries(flowCounts).forEach(([key,count])=>{
    const [sk,tk]=key.split('→');
    const s=cols[sk],t=cols[tk];
    if(!s||!t)return;
    const opacity=0.15+0.55*(count/maxFlow);
    const sw=Math.max(2,Math.min(20,(count/maxFlow)*16));
    svg+=`<path d="M${s.x+colW} ${s.y+s.h/2} C${(s.x+colW+t.x)/2} ${s.y+s.h/2} ${(s.x+colW+t.x)/2} ${t.y+t.h/2} ${t.x} ${t.y+t.h/2}"
      fill="none" stroke="var(--accent)" stroke-width="${sw}" opacity="${opacity.toFixed(2)}"/>`;
  });
  kindOrder.forEach(k=>{
    const c=cols[k];if(!c)return;
    const col=GRAPH_COLORS[k]||'var(--dim)';
    svg+=`<rect x="${c.x}" y="${c.y}" width="${colW}" height="${c.h}" rx="6" fill="${col}" opacity="0.8"/>`;
    svg+=`<text x="${c.x+colW/2}" y="${H+16}" text-anchor="middle" fill="var(--dim)" font-size="9" font-weight="600">${kindLabel[k]||k}</text>`;
    svg+=`<text x="${c.x+colW/2}" y="${H+28}" text-anchor="middle" fill="var(--text)" font-size="10" font-weight="700">${c.n}</text>`;
  });
  svg+=`</svg>`;
  return `<details class="card dash-panel"><summary class="title" style="cursor:pointer">Provenance flow</summary>
    <div class="dim small" style="margin:8px 0">Document flow from research → analysis → spec → ticket → code — thicker bands = more connections</div>
    ${svg}
  </details>`;
}

// ── 3. Governance risk list ─────────────────────────────────────────
function rViewGovernanceRisk(){
  const items=graphData?.coverage?.approved_unhealthy_list||[];
  if(!items.length)return '';
  let rows='';
  items.forEach(r=>{
    const sigs=signalGlyphs(r.signals||[],r.missing||[]);
    rows+=`<li style="display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid var(--line)">
      <span class="graph-chain-dot" style="background:${scoreRingColor(r.score||0)}"></span>
      <span style="flex:1"><strong>${esc(r.label)}</strong> <span class="dash-sigs">${sigs}</span></span>
      ${r.doc?`<button class="ghost" type="button" style="padding:4px 8px;font-size:11px" onclick="openDoc('${esc(r.doc)}')">open</button>`:''}
    </li>`;
  });
  return `<details class="card dash-panel"><summary class="title" style="cursor:pointer">Governance risk <span class="badge warn">${items.length}</span></summary>
    <div class="dim small" style="margin:8px 0">Approved specs scoring below 3/3 — approved for implementation but not fully anchored to code</div>
    <ul class="dash-untracked">${rows}</ul>
  </details>`;
}

// ── 4. Citation density map ─────────────────────────────────────────
function rViewCitationDensity(){
  const rows=graphData?.coverage?.citation_density||[];
  if(!rows.length)return '';
  const maxC=Math.max(1,...rows.map(r=>r.citations));
  let bars='';
  rows.forEach(r=>{
    const w=Math.round(r.citations/maxC*100);
    const col=r.citations>=3?'var(--ok)':r.citations>=1?'var(--accent)':'var(--bad)';
    bars+=`<div class="hm-row">
      <span class="hm-label mono">${esc(r.label)}</span>
      <div class="hm-track"><div class="hm-fill" style="width:${w}%;background:${col}"></div></div>
      <span class="hm-pct">${r.citations}</span>
    </div>`;
  });
  return `<details class="card dash-panel"><summary class="title" style="cursor:pointer">Citation density (${rows.length} files)</summary>
    <div class="dim small" style="margin:8px 0">Vault citation count per code file — sorted by ranking importance. 0 = no doc links this file.</div>
    <div class="hm-grid">${bars}</div>
  </details>`;
}

// ── 5. Stale document queue ─────────────────────────────────────────
function rViewStaleQueue(){
  const items=graphData?.coverage?.stale_queue||[];
  if(!items.length)return '';
  let rows='';
  items.forEach(r=>{
    const sigs=signalGlyphs(r.signals||[],r.missing||[]);
    const barW=Math.min(100,r.stale_days);
    rows+=`<li style="display:flex;flex-direction:column;gap:4px;padding:8px 0;border-bottom:1px solid var(--line)">
      <div style="display:flex;align-items:center;gap:8px">
        <span class="graph-chain-dot" style="background:${scoreRingColor(r.score||0)}"></span>
        <span style="flex:1"><strong>${esc(r.label)}</strong> <span class="badge">${r.kind}</span> ${sigs}</span>
        ${r.doc?`<button class="ghost" type="button" style="padding:4px 8px;font-size:11px" onclick="openDoc('${esc(r.doc)}')">open</button>`:''}
      </div>
      <div class="dash-fresh-strip"><span class="dim small">${r.stale_days}d stale</span>
        <div class="dash-fresh-bar"><div class="dash-fresh-fill" style="width:${barW}%"></div></div>
      </div>
    </li>`;
  });
  return `<details class="card dash-panel"><summary class="title" style="cursor:pointer">Stale documents <span class="badge warn">${items.length}</span></summary>
    <div class="dim small" style="margin:8px 0">Docs whose linked code files changed more recently — review and update these to restore freshness</div>
    <ul class="dash-untracked">${rows}</ul>
  </details>`;
}

"""
