"""Vault audit panels for the Knowledge dashboard tab.

``rGraphDashboard()`` renders summary, signal matrix, histogram, thin-links, and
trend only. Miss filters and untracked queue live in ``rGraphControlsStack`` /
``rGraphContextPanels`` (``_graph.py``) so view controls sit contiguous above the canvas.
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
  for(let s=0;s<=4;s++){
    const n=+(hist[String(s)]||0);
    const h=Math.round(n/max*100);
    const col=s>=4?'var(--ok)':s>=3?'var(--accent)':s>=1?'var(--warn)':'var(--bad)';
    bars+=`<div class="dash-bar-wrap" title="score ${s}: ${n} docs">
      <div class="dash-bar" style="height:${h}%;background:${col}"></div>
      <span class="dash-bar-lbl">★${s}</span><span class="dim small">${n}</span></div>`;
  }
  return `<div class="card dash-panel"><div class="title">Score distribution</div>
    <div class="dim small" style="margin-bottom:10px">docs by provenance score (0–4)</div>
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
