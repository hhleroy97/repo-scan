"""Knowledge dashboard — provenance graph canvas and controls (no CDN).

Vault: docs/research/analysis/2026-06-10-move-the-agentic-loop-graph-and-untracke-analysis
Vault: docs/research/sources/url-www-nngroup-com-articles-progressive-disclosure
Vault: docs/research/sources/url-www-w3-org-wai-aria-apg-patterns-toolbar

Render order in ``rGraph()``: Vault audit (``rGraphDashboard``) → graph controls
(``rGraphControlsStack``: miss filters, layer tabs, zoom toolbar) → canvas + legend
(``rGraphCanvas``) → context panels below (``rGraphContextPanels``: agentic loop,
untracked queue, provenance tools).
"""

_FRAGMENT = r"""const GRAPH_COLORS={code:'#4f9cf9',ticket:'#e0a93e',spec:'#3fb96d',
  analysis:'#9b7cf6',source:'#8b95a5',report:'#8b95a5',doc:'#8b95a5',gate:'#e25d5d',run:'#4f9cf9'};
const GRAPH_LABEL_MIN=9, GRAPH_LABEL_MAX=18, GRAPH_LABEL_BASE=12;
let graphData=null,graphLayer='coverage',graphLayout=null,graphLayerCache='';
let graphView={x:0,y:0,scale:1},graphDrag=null,graphPinch=null;
let gfRepulsion=2200,gfSpring=0.045,gfGravity=0.002,gfDamping=0.78,gfIterations=260;
let gfShowEdges={cites:true,linked:true,wiki:true};
let gfLabelThreshold=0.55,gfNodeScale=1.0,gfFrozen=false;

function rGraphControlsStack(){
  const st=graphData?.stats||{};
  const ck=(id,on)=>`<label class="gf-check"><input type="checkbox" ${on?'checked':''} onchange="gfToggleEdge('${id}',this.checked)">${id}</label>`;
  return `<div class="graph-controls-stack" role="group" aria-label="Graph controls">
    ${rDashMissFilters()}
    <div class="graph-tabs">`+
    [['all','All'],['coverage','Coverage'],['vault','Vault'],['code','Code']].map(([k,l])=>
      `<button type="button" class="graph-tab${graphLayer===k?' active':''}" onclick="setGraphLayer('${k}')">${l}</button>`
    ).join('')+`</div>
    <div class="graph-toolbar">
      <button class="ghost" type="button" onclick="graphZoom(1.25)">+</button>
      <button class="ghost" type="button" onclick="graphZoom(0.8)">−</button>
      <button class="ghost" type="button" onclick="graphFit()">Fit</button>
      <button class="ghost" type="button" onclick="graphRelayout()">Re-layout</button>
      <button class="ghost" type="button" onclick="gfToggleFrozen()" id="gf-freeze-btn">${gfFrozen?'Unfreeze':'Freeze'}</button>
      <span class="dim small">${st.nodes||0} nodes · ${st.edges||0} edges</span>
    </div>
    <details class="gf-tuning">
      <summary class="gf-summary">Force tuning</summary>
      <div class="gf-grid">
        <div class="gf-row"><span class="gf-label">Repulsion</span>
          <input type="range" class="gf-slider" min="200" max="8000" step="100" value="${gfRepulsion}"
            oninput="gfSet('gfRepulsion',+this.value,this)"><span class="gf-val" id="gf-v-rep">${gfRepulsion}</span></div>
        <div class="gf-row"><span class="gf-label">Spring</span>
          <input type="range" class="gf-slider" min="0.005" max="0.15" step="0.005" value="${gfSpring}"
            oninput="gfSet('gfSpring',+this.value,this)"><span class="gf-val" id="gf-v-spr">${gfSpring}</span></div>
        <div class="gf-row"><span class="gf-label">Gravity</span>
          <input type="range" class="gf-slider" min="0" max="0.02" step="0.001" value="${gfGravity}"
            oninput="gfSet('gfGravity',+this.value,this)"><span class="gf-val" id="gf-v-grav">${gfGravity}</span></div>
        <div class="gf-row"><span class="gf-label">Damping</span>
          <input type="range" class="gf-slider" min="0.5" max="0.95" step="0.01" value="${gfDamping}"
            oninput="gfSet('gfDamping',+this.value,this)"><span class="gf-val" id="gf-v-damp">${gfDamping}</span></div>
        <div class="gf-row"><span class="gf-label">Iterations</span>
          <input type="range" class="gf-slider" min="50" max="800" step="10" value="${gfIterations}"
            oninput="gfSet('gfIterations',+this.value,this)"><span class="gf-val" id="gf-v-iter">${gfIterations}</span></div>
        <div class="gf-row"><span class="gf-label">Node size</span>
          <input type="range" class="gf-slider" min="0.4" max="2.5" step="0.1" value="${gfNodeScale}"
            oninput="gfSet('gfNodeScale',+this.value,this)"><span class="gf-val" id="gf-v-nsz">${gfNodeScale}</span></div>
        <div class="gf-row"><span class="gf-label">Label zoom</span>
          <input type="range" class="gf-slider" min="0.1" max="1.5" step="0.05" value="${gfLabelThreshold}"
            oninput="gfSet('gfLabelThreshold',+this.value,this)"><span class="gf-val" id="gf-v-lbl">${gfLabelThreshold}</span></div>
      </div>
      <div class="gf-edge-row">
        <span class="gf-label">Edges</span>
        ${ck('cites',gfShowEdges.cites)} ${ck('linked',gfShowEdges.linked)} ${ck('wiki',gfShowEdges.wiki)}
      </div>
      <div class="gf-actions">
        <button class="ghost" type="button" onclick="gfResetDefaults()">Reset defaults</button>
      </div>
    </details>
  </div>`;
}
function gfSet(prop,val,el){
  const m={gfRepulsion:v=>gfRepulsion=v,gfSpring:v=>gfSpring=v,gfGravity:v=>gfGravity=v,
    gfDamping:v=>gfDamping=v,gfIterations:v=>gfIterations=v,gfNodeScale:v=>gfNodeScale=v,
    gfLabelThreshold:v=>gfLabelThreshold=v};
  if(m[prop])m[prop](val);
  const ids={gfRepulsion:'gf-v-rep',gfSpring:'gf-v-spr',gfGravity:'gf-v-grav',
    gfDamping:'gf-v-damp',gfIterations:'gf-v-iter',gfNodeScale:'gf-v-nsz',gfLabelThreshold:'gf-v-lbl'};
  const v=document.getElementById(ids[prop]);if(v)v.textContent=val;
  const renderOnly=prop==='gfNodeScale'||prop==='gfLabelThreshold';
  if(renderOnly||gfFrozen)graphPaint();
  else{graphLayout=null;graphPaint();graphFit()}
}
function gfToggleEdge(kind,on){gfShowEdges[kind]=on;graphPaint()}
function gfToggleFrozen(){
  gfFrozen=!gfFrozen;
  const btn=document.getElementById('gf-freeze-btn');
  if(btn)btn.textContent=gfFrozen?'Unfreeze':'Freeze';
}
function gfResetDefaults(){
  gfRepulsion=2200;gfSpring=0.045;gfGravity=0.002;gfDamping=0.78;gfIterations=260;
  gfNodeScale=1.0;gfLabelThreshold=0.55;gfShowEdges={cites:true,linked:true,wiki:true};
  graphLayout=null;
  const el=document.getElementById('main');
  if(el&&tab==='dashboard')el.innerHTML=rGraph();
  graphPaint();bindGraphEvents();graphFit();renderAgenticLoopMermaid();
}
function rGraphCanvas(){
  return `<div class="graph-wrap" id="graph-wrap"><canvas id="graph-canvas"></canvas></div>
  <div class="graph-legend">
    <span><i class="graph-dot code"></i>code</span>
    <span><i class="graph-dot ticket"></i>ticket</span>
    <span><i class="graph-dot spec"></i>spec</span>
    <span><i class="graph-dot analysis"></i>analysis</span>
    <span><i class="graph-dot source"></i>source</span>
    <span class="dim">—</span>
    <span><i class="graph-edge-loop"></i>closed loop</span>
    <span><i class="graph-edge-cite"></i>cites</span>
    <span><i class="graph-edge-link"></i>linked</span>
    <span><i class="graph-edge-wiki"></i>wikilink</span>
  </div>
  <div class="graph-hint">Drag to pan · pinch / wheel to zoom · tap a node for provenance chain</div>
  ${rGraphGuide()}`;
}
function rGraphContextPanels(){
  return `<div class="graph-context-panels">
    ${rGraphPipeline()}
    ${rDashUntracked()}
    ${rDashProvenanceTools()}
    ${rGraphAdditionalViews()}
  </div>`;
}
function rGraph(){
  let h=`<div class="section">Knowledge dashboard</div>`;
  h+=rGraphDashboard();
  h+=rGraphControlsStack();
  h+=rGraphCanvas();
  h+=`<div class="section" style="margin-top:18px">Context</div>`;
  h+=rGraphContextPanels();
  return h;
}
function setGraphLayer(k){graphLayer=k;graphLayout=null;graphPaint();graphFit()}
function graphRelayout(){graphLayout=null;graphPaint();graphFit()}

function graphFiltered(){
  if(!graphData)return {nodes:[],edges:[],hi:new Set()};
  const hi=new Set(graphData.highlights||[]);
  let nodes=graphData.nodes||[];
  if(graphLayer==='code')nodes=nodes.filter(n=>n.kind==='code');
  else if(graphLayer==='vault')nodes=nodes.filter(n=>n.kind!=='code');
  else if(graphLayer==='coverage'){
    const linked=new Set();
    (graphData.edges||[]).forEach(e=>{
      if(e.kind==='cites'||e.kind==='linked_file'){
        if(e.source.startsWith('code:'))linked.add(e.source);
        if(e.target.startsWith('code:'))linked.add(e.target);
      }
    });
    nodes=nodes.filter(n=>n.kind!=='code'||linked.has(n.id));
  }
  if(graphMissFilter){
    nodes=nodes.filter(n=>{
      if(n.kind==='code')return true;
      return (n.missing||[]).includes(graphMissFilter);
    });
  }
  const ids=new Set(nodes.map(n=>n.id));
  const edges=(graphData.edges||[]).filter(e=>ids.has(e.source)&&ids.has(e.target));
  return {nodes,edges,hi};
}

function graphEdgeStyle(e,allEdges){
  if(e.kind==='cites'){
    const loop=allEdges.some(x=>x.kind==='linked_file'&&x.source===e.target&&x.target===e.source);
    return {color:loop?'#3fb96d':'#4f9cf9',width:loop?2.5:2,dash:[]};
  }
  if(e.kind==='linked_file'){
    const loop=allEdges.some(x=>x.kind==='cites'&&x.source===e.target&&x.target===e.source);
    return {color:loop?'#3fb96d':'#9aa5b8',width:loop?2.5:1.5,dash:loop?[]:[5,4]};
  }
  return {color:'rgba(95,110,135,0.4)',width:1,dash:[3,3]};
}

"""
