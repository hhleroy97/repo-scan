"""Vault audit panels and provenance tools for the Knowledge dashboard tab.

``rGraphDashboard()`` renders summary, signal matrix, histogram, thin-links, and
trend chart. ``rDashProvenanceTools()`` renders the lint/auto-link quick-action
panel in the context section below the canvas.

Vault: docs/research/sources/url-www-nngroup-com-articles-gestalt-proximity
"""

_FRAGMENT = r"""const DASH_SIGNALS=['evidence','linked','cited','fresh'];
const DASH_KINDS=['ticket','spec','analysis','source'];
const DASH_SIG_LABEL={evidence:'E',linked:'L',cited:'C',fresh:'F'};
let graphMissFilter=null;

function signalGlyphs(signals,missing){
  const have=new Set(signals||[]);
  const miss=new Set(missing||[]);
  return DASH_SIGNALS.map(s=>{
    const ok=have.has(s)&&!miss.has(s);
    const cls=ok?'dash-sig-ok':(miss.has(s)?'dash-sig-miss':'dash-sig-miss');
    return `<span class="dash-sig ${cls}" title="${s}">${DASH_SIG_LABEL[s]}</span>`;
  }).join('');
}
function dashPct(n,d){return d?Math.round(n/d*100):0;}
function dashHeat(p){
  if(p>=80)return 'dash-heat-ok';
  if(p>=50)return 'dash-heat-warn';
  return 'dash-heat-bad';
}
function setGraphMissFilter(sig){
  graphMissFilter=graphMissFilter===sig?null:sig;
  graphLayout=null;
  const el=document.getElementById('main');
  if(el&&tab==='dashboard')el.innerHTML=rGraph();
  mountGraph();
}

function sparkSVG(arr,key,color){
  const vals=(arr||[]).map(d=>d[key]).filter(v=>v!=null);
  if(vals.length<2)return '';
  const mn=Math.min(...vals),mx=Math.max(...vals),rg=mx-mn||1;
  const w=56,h=18;
  const pts=vals.map((v,i)=>`${(i/(vals.length-1))*w},${h-((v-mn)/rg)*h}`).join(' ');
  return `<svg width="${w}" height="${h}" style="display:block;margin-top:4px"><polyline fill="none" stroke="${color}" stroke-width="1.5" points="${pts}"/></svg>`;
}
function deltaTag(v,suffix){
  if(v==null||v===0)return '';
  const abs=Math.abs(v<1&&v>-1?Math.round(v*100):v);
  return ` <span style="color:var(--${v>0?'ok':'bad'});font-size:11px">${v>0?'↑':'↓'}${abs}${suffix||''}</span>`;
}

function rDashSummary(){
  const cov=graphData?.coverage||{};
  const st=graphData?.stats||{};
  const sp=S?.trend_sparkline||[];
  const vd=S?.vault_delta;
  const pct=Math.round((cov.coverage_pct||st.coverage_pct||0)*100);
  const healthy=cov.healthy??st.healthy??0;
  const docs=cov.docs||0;
  const stale=cov.stale_docs_count||0;
  const untr=cov.untracked_code_count||0;
  const debt=cov.knowledge_debt;
  const auh=cov.approved_unhealthy||0;
  return `<div class="dash-cards">
    <div class="dash-card"><div class="dash-card-val">${pct}%${deltaTag(vd?.coverage_pct,'%')}</div><div class="dash-card-lbl">vault healthy</div><div class="dim small">${healthy}/${docs} docs</div>${sparkSVG(sp,'vault_pct','#3fb96d')}</div>
    <div class="dash-card"><div class="dash-card-val" style="color:var(--${debt!=null&&debt>50?'warn':'ok'})">${debt!=null?debt:'—'}</div><div class="dash-card-lbl">knowledge debt</div><div class="dim small">0 best · 100 worst</div></div>
    <div class="dash-card"><div class="dash-card-val">${stale}</div><div class="dash-card-lbl">stale docs</div><div class="dim small">code newer than doc</div>${auh?`<div class="small" style="color:var(--warn);margin-top:4px">${auh} approved unhealthy</div>`:''}</div>
    <div class="dash-card"${untr>0?' style="cursor:pointer" onclick="openUntrackedPanel()" title="Show untracked queue"':''}><div class="dash-card-val">${untr}${deltaTag(vd?.untracked)}</div><div class="dash-card-lbl">untracked code</div><div class="dim small">ranked, no vault link</div>${sparkSVG(sp,'files','#4f9cf9')}</div>
  </div>`;
}

function rDashMatrix(){
  const matrix=graphData?.coverage?.signal_matrix;
  if(!matrix)return `<div class="card dash-panel"><div class="title">Signal coverage</div>
    <div class="dim small">Run <span class="mono">radar scan</span> to populate vault audit data.</div></div>`;
  let h=`<div class="card dash-panel"><div class="title">Signal coverage</div>
    <div class="dim small" style="margin-bottom:8px">E evidence · L linked · C cited · F fresh</div>
    <table class="dash-matrix"><thead><tr><th></th>
    ${DASH_SIGNALS.map(s=>`<th>${DASH_SIG_LABEL[s]}</th>`).join('')}</tr></thead><tbody>`;
  DASH_KINDS.forEach(kind=>{
    const row=matrix[kind]||{};
    h+=`<tr><td>${kind}</td>`;
    DASH_SIGNALS.forEach(sig=>{
      const cell=row[sig]||{pass:0,total:0};
      const p=dashPct(cell.pass,cell.total);
      const miss=cell.total-cell.pass;
      h+=`<td><span class="dash-cell ${dashHeat(p)}" style="cursor:pointer" title="${miss} ${kind} missing ${sig}" onclick="setGraphMissFilter('${sig}')">${p}%</span></td>`;
    });
    h+=`</tr>`;
  });
  return h+`</tbody></table></div>`;
}

function rDashHistogram(){
  const hist=graphData?.coverage?.score_histogram;
  if(!hist)return `<div class="card dash-panel"><div class="title">Score distribution</div>
    <div class="dim small">No scored vault docs yet.</div></div>`;
  const max=Math.max(1,...Object.values(hist).map(v=>+v||0));
  let bars='';
  for(let s=0;s<=3;s++){
    const n=+(hist[String(s)]||0);
    const h=Math.round(n/max*100);
    const col=s>=3?'var(--ok)':s>=2?'var(--accent)':s>=1?'var(--warn)':'var(--bad)';
    bars+=`<div class="dash-bar-wrap" title="score ${s}: ${n} docs">
      <div class="dash-bar" style="height:${h}%;background:${col}"></div>
      <span class="dash-bar-lbl">★${s}</span><span class="dim small">${n}</span></div>`;
  }
  return `<div class="card dash-panel"><div class="title">Score distribution</div>
    <div class="dim small" style="margin-bottom:10px">docs by provenance score (0–3) · fresh is vanity</div>
    <div class="dash-bars">${bars}</div></div>`;
}

function rDashMissFilters(){
  const orphans=(graphData?.coverage?.orphans)||[];
  const counts={};
  orphans.forEach(o=>(o.missing||[]).forEach(m=>{counts[m]=(counts[m]||0)+1}));
  if(!Object.keys(counts).length)return '';
  let h=`<div class="dash-filters"><span class="dim small">Filter graph:</span>`;
  DASH_SIGNALS.forEach(sig=>{
    const n=counts[sig]||0;
    if(!n)return;
    const on=graphMissFilter===sig?' active':'';
    h+=`<button type="button" class="dash-filter${on}" onclick="setGraphMissFilter('${sig}')">${sig} (${n})</button>`;
  });
  if(graphMissFilter)h+=`<button type="button" class="ghost dash-filter" onclick="setGraphMissFilter(null)">Clear</button>`;
  return h+`</div>`;
}

function rDashUntracked(){
  const rows=graphData?.coverage?.untracked_ranked||[];
  if(!rows.length)return '';
  let h=`<details id="dash-untracked-panel" class="card dash-panel"><summary class="title" style="cursor:pointer">Untracked code (${rows.length})</summary>
    <div class="dim small" style="margin:8px 0">High-ranked files with no vault backlink — add specs or citations.</div>
    <ul class="dash-untracked">`;
  rows.forEach(r=>{
    h+=`<li><span class="mono">${esc(r.file)}</span><span class="badge">score ${r.score}</span></li>`;
  });
  return h+`</ul></details>`;
}

function rDashThinLinks(){
  const thin=graphData?.coverage?.thin_citations||[];
  if(!thin.length)return '';
  return `<details class="card dash-panel"><summary class="title" style="cursor:pointer">Fragile code links (${thin.length})</summary>
    <div class="dim small" style="margin:8px 0">Files with ≤1 vault citation — connections that break easily.</div>
    <ul class="dash-untracked">${thin.map(r=>`<li><span class="mono">${esc(r.file)}</span><span class="badge">${r.count} cite${r.count!==1?'s':''}</span></li>`).join('')}</ul>
  </details>`;
}

function rDashTrendChart(){
  const sp=S?.trend_sparkline||[];
  if(sp.length<2)return '';
  const W=280,H=100,P=30;
  const series=[{key:'vault_pct',color:'#3fb96d',label:'Vault %',norm:v=>v},{key:'files',color:'#4f9cf9',label:'Files',norm:null}];
  let paths='';
  series.forEach(s=>{
    const raw=sp.map(d=>d[s.key]).filter(v=>v!=null);if(raw.length<2)return;
    const mn=Math.min(...raw),mx=Math.max(...raw),rg=mx-mn||1;
    const pts=raw.map((v,i)=>`${P+(i/(raw.length-1))*W},${P+H-((v-mn)/rg)*H}`).join(' ');
    paths+=`<polyline fill="none" stroke="${s.color}" stroke-width="2" points="${pts}"/>`;
  });
  if(!paths)return '';
  let grid='';
  for(let i=0;i<=4;i++){const y=P+H*(1-i/4);grid+=`<line x1="${P}" y1="${y}" x2="${W+P}" y2="${y}" stroke="#2a3240" stroke-width="0.5"/>`;}
  const first=sp[0].when?.slice(0,10)||'',last=sp[sp.length-1].when?.slice(0,10)||'';
  const xLabels=`<text x="${P}" y="${H+P+14}" fill="#8b95a5" font-size="9">${esc(first)}</text><text x="${W+P}" y="${H+P+14}" fill="#8b95a5" font-size="9" text-anchor="end">${esc(last)}</text>`;
  const legend=series.map(s=>`<span><i style="display:inline-block;width:10px;height:3px;background:${s.color};margin-right:4px;vertical-align:middle;border-radius:1px"></i>${s.label}</span>`).join(' ');
  return `<details class="card dash-panel"><summary class="title" style="cursor:pointer">Scan trend (${sp.length} scans)</summary>
    <div class="dim small" style="margin:6px 0">${legend}</div>
    <svg width="100%" viewBox="0 0 ${W+P*2} ${H+P*2}" style="display:block">${grid}${paths}${xLabels}</svg>
  </details>`;
}

function openUntrackedPanel(){
  const el=document.getElementById('dash-untracked-panel');
  if(!el)return;
  el.open=true;
  el.scrollIntoView({behavior:'smooth',block:'nearest'});
}

let _lintCache=null,_lintLoading=false;
function rDashProvenanceTools(){
  const c=_lintCache;
  const statusHtml=c
    ?`<span class="dim small">${c.total} issue${c.total!==1?'s':''}</span>`
    +(c.broken?` <span class="badge warn">${c.broken} broken</span>`:'')
    +(c.missing?` <span class="badge bad">${c.missing} no linked_files</span>`:'')
    +(!c.total?' <span class="badge ok">clean</span>':'')
    :'<span class="dim small">Not checked yet</span>';
  return `<div class="card dash-panel dash-tools-panel">
    <div class="title" style="margin-bottom:10px">Provenance tools</div>
    <div class="dash-tools-grid">
      <div class="dash-tool-row">
        <div style="flex:1">
          <div class="small" style="font-weight:600">Lint vault links</div>
          <div>${statusHtml}</div>
        </div>
        <button class="ghost" type="button" style="flex:none;padding:6px 12px;font-size:11px" onclick="runProvenanceLint(this)" ${_lintLoading?'disabled':''}>
          ${_lintLoading?'Running…':'Check'}
        </button>
      </div>
      <div class="dash-tool-row">
        <div style="flex:1">
          <div class="small" style="font-weight:600">Auto-link orphans</div>
          <div class="dim small">Propagate linked_files from sources to analyses</div>
        </div>
        <button class="ghost" type="button" style="flex:none;padding:6px 12px;font-size:11px" onclick="runProvenanceAutolink(this)">Fix</button>
      </div>
      <div class="dash-tool-row">
        <div style="flex:1">
          <div class="small" style="font-weight:600">Full audit</div>
          <div class="dim small">Run <span class="mono">radar audit-provenance</span> in terminal</div>
        </div>
      </div>
    </div>
  </div>`;
}
async function runProvenanceLint(btn){
  _lintLoading=true;
  beginPending('lint-vault','Linting vault links…',{btn,btnLabel:'Running…'});
  try{
    _lintCache=await api(API_PROVENANCE_LINT);
    const n=_lintCache.total;
    toast(n?`${n} lint issue${n!==1?'s':''} found`:'Vault links clean');
  }catch(e){toast('Lint failed: '+e.message)}
  finally{_lintLoading=false;endPending('lint-vault')}
  const el=document.getElementById('main');
  if(el&&tab==='dashboard')el.innerHTML=rGraph();
  mountGraph();
}
async function runProvenanceAutolink(btn){
  beginPending('autolink','Auto-linking orphans…',{btn,btnLabel:'Running…'});
  try{
    const res=await api(API_PROVENANCE_AUTOLINK);
    toast(res.updated?`Updated ${res.updated} file${res.updated!==1?'s':''}`:'No orphans to link');
    _lintCache=null;
  }catch(e){toast('Auto-link failed: '+e.message)}
  finally{endPending('autolink')}
  mountGraph();
}

function rGraphGuide(){
  const st=graphData?.stats||{};
  const cov=graphData?.coverage||{};
  const nodeDetail=`${st.code_nodes||0} code files and ${st.vault_nodes||0} vault documents (${(cov.docs||0)} scored)`;
  return `<details class="card dash-panel graph-guide">
    <summary class="title" style="cursor:pointer">How to read this graph</summary>
    <div class="guide-body">
      <div class="guide-section">
        <div class="guide-heading">What you're looking at</div>
        <p>This provenance graph maps <strong>${nodeDetail}</strong> in your repo. Every vault document
        (ticket, spec, analysis, research source) is scored 0–3 on three signals that measure whether it's
        actually grounded in code:</p>
        <div class="guide-signals">
          <div><span class="dash-sig dash-sig-ok">E</span> <strong>Evidence</strong> — doc contains wikilinks, analysis references, or substantive content</div>
          <div><span class="dash-sig dash-sig-ok">L</span> <strong>Linked</strong> — doc's <code>linked_files</code> frontmatter points to real code paths in scan.json</div>
          <div><span class="dash-sig dash-sig-ok">C</span> <strong>Cited</strong> — at least one Python module cites this doc via <code>Vault:</code> or <code>Spec:</code> in its docstring</div>
          <div><span class="dash-sig dash-sig-miss">F</span> <strong>Fresh</strong> — doc is newer than its linked code (vanity — shown but not scored)</div>
        </div>
      </div>
      <div class="guide-section">
        <div class="guide-heading">Edge types</div>
        <p><span class="graph-edge-loop" style="display:inline-block"></span> <strong>Closed loop</strong> — bidirectional: code cites doc AND doc links code. Strongest provenance.
        <br><span class="graph-edge-cite" style="display:inline-block"></span> <strong>Cites</strong> — code file references this doc (<code># see docs/tickets/tkt-XXXX</code>).
        <br><span class="graph-edge-link" style="display:inline-block"></span> <strong>Linked</strong> — doc's frontmatter declares <code>linked_files</code> to this code.
        <br><span class="graph-edge-wiki" style="display:inline-block"></span> <strong>Wikilink</strong> — doc references another doc via <code>[[wikilink]]</code>.</p>
      </div>
      <div class="guide-section">
        <div class="guide-heading">Layer filters</div>
        <p><strong>Coverage</strong> (default) hides code nodes with no vault connections — showing only the documented portion of the codebase.
        <strong>Vault</strong> isolates documents only. <strong>Code</strong> shows the dependency graph between modules.
        <strong>All</strong> renders everything. The signal filters (E/L/C/F) narrow vault nodes to those <em>missing</em> a specific signal.</p>
      </div>
      <div class="guide-section">
        <div class="guide-heading">How to use it</div>
        <p><strong>Tap any node</strong> to open its provenance chain — a tree showing what evidence supports that document, which signals it passes, and where the gaps are.
        Score rings around vault nodes are colored: <span style="color:var(--ok)">green</span> (3/3), <span style="color:var(--accent)">blue</span> (2/3), <span style="color:var(--warn)">amber</span> (1/3), <span style="color:var(--bad)">red</span> (0/3).</p>
        <p>Look for <strong>red/amber clusters</strong> — those are areas where documentation exists but isn't anchored to code. Fix them by adding <code>linked_files</code> frontmatter or <code>Vault:</code> citations in the relevant module.</p>
      </div>
    </div>
  </details>`;
}

function rGraphDashboard(){
  return `<div class="dash-section">
    <div class="section">Vault audit</div>
    ${rDashSummary()}
    <div class="dash-grid">${rDashMatrix()}${rDashHistogram()}</div>
    ${rDashThinLinks()}
    ${rDashTrendChart()}
  </div>`;
}

"""
