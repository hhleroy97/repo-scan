"""Force-directed layout simulation, paint loop, and graph mount."""

_FRAGMENT = r"""function computeGraphLayout(){
  const {nodes,edges}=graphFiltered();
  const n=nodes.length;
  if(!n){graphLayout={nodes:[],edges:[],bounds:{minX:0,minY:0,maxX:1,maxY:1}};return}
  const deg={};
  edges.forEach(e=>{deg[e.source]=(deg[e.source]||0)+1;deg[e.target]=(deg[e.target]||0)+1});
  const sorted=[...nodes].sort((a,b)=>(deg[b.id]||0)-(deg[a.id]||0));
  const radius=Math.max(220,Math.sqrt(n)*70);
  const sim={};
  sorted.forEach((node,i)=>{
    if(i===0){sim[node.id]={x:0,y:0,vx:0,vy:0,n:node};return}
    const ring=Math.ceil(Math.sqrt(i));
    const ringStart=(ring-1)*(ring-1), ringSize=ring*ring-ringStart;
    const idx=i-ringStart, ang=(idx/ringSize)*Math.PI*2+ring*0.7;
    const r=ring*radius/Math.sqrt(n);
    sim[node.id]={x:Math.cos(ang)*r,y:Math.sin(ang)*r,vx:0,vy:0,n:node};
  });
  const arr=Object.values(sim);
  const idealEdge=Math.max(60,radius*0.18);
  const allEdges=graphData?.edges||[];
  const iters=gfIterations;
  for(let t=0;t<iters;t++){
    const k=1-t/iters;
    for(let i=0;i<arr.length;i++){
      for(let j=i+1;j<arr.length;j++){
        const a=arr[i],b=arr[j];
        let dx=b.x-a.x,dy=b.y-a.y,d2=dx*dx+dy*dy+0.01;
        const f=gfRepulsion/d2;
        const nx=dx/Math.sqrt(d2),ny=dy/Math.sqrt(d2);
        a.vx-=f*nx;a.vy-=f*ny;b.vx+=f*nx;b.vy+=f*ny;
      }
    }
    edges.forEach(e=>{
      const a=sim[e.source],b=sim[e.target];if(!a||!b)return;
      let dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy)||1;
      const f=(d-idealEdge)*gfSpring;
      a.vx+=f*dx/d;a.vy+=f*dy/d;b.vx-=f*dx/d;b.vy-=f*dy/d;
    });
    arr.forEach(p=>{
      p.vx-=p.x*gfGravity;p.vy-=p.y*gfGravity;
      p.x+=p.vx*0.18*k;p.y+=p.vy*0.18*k;
      p.vx*=gfDamping;p.vy*=gfDamping;
    });
  }
  const positioned=arr.map(p=>({...p.n,x:p.x,y:p.y,deg:deg[p.n.id]||0}));
  const xs=positioned.map(p=>p.x),ys=positioned.map(p=>p.y);
  const bounds={minX:Math.min(...xs),maxX:Math.max(...xs),
                minY:Math.min(...ys),maxY:Math.max(...ys)};
  graphLayout={nodes:positioned,edges,bounds};
  graphLayerCache=graphLayer+(graphMissFilter||'');
}

function graphFit(){
  if(!graphLayout)return;
  const wrap=document.getElementById('graph-wrap');if(!wrap)return;
  const rect=wrap.getBoundingClientRect();
  const b=graphLayout.bounds;
  const pad=60;
  const gw=Math.max(1,b.maxX-b.minX),gh=Math.max(1,b.maxY-b.minY);
  const s=Math.min(3,Math.max(0.25,Math.min((rect.width-pad*2)/gw,(rect.height-pad*2)/gh)));
  graphView.scale=s;
  graphView.x=rect.width/2-((b.minX+b.maxX)/2)*s;
  graphView.y=rect.height/2-((b.minY+b.maxY)/2)*s;
  graphPaint();
}

function graphPaint(){
  const wrap=document.getElementById('graph-wrap');
  const canvas=document.getElementById('graph-canvas');
  if(!wrap||!canvas||!graphData)return;
  const layerKey=graphLayer+(graphMissFilter||'');
  if(!graphLayout||graphLayerCache!==layerKey)computeGraphLayout();
  const rect=wrap.getBoundingClientRect();
  const dpr=window.devicePixelRatio||1;
  canvas.width=Math.max(1,Math.floor(rect.width*dpr));
  canvas.height=Math.max(1,Math.floor(rect.height*dpr));
  const ctx=canvas.getContext('2d');
  ctx.setTransform(dpr,0,0,dpr,0,0);
  ctx.clearRect(0,0,rect.width,rect.height);
  const {nodes,edges}=graphLayout;
  const allEdges=graphData.edges||[];
  const hi=new Set((graphData.highlights||[]));
  const s=graphView.scale,tx=graphView.x,ty=graphView.y;
  const toScreen=p=>({x:p.x*s+tx,y:p.y*s+ty});
  ctx.lineCap='round';
  const edgeKindMap={cites:'cites',linked_file:'linked',wikilink:'wiki'};
  edges.forEach(e=>{
    const ek=edgeKindMap[e.kind]||'wiki';
    if(!gfShowEdges[ek])return;
    const a=nodes.find(n=>n.id===e.source),b=nodes.find(n=>n.id===e.target);
    if(!a||!b)return;
    const st=graphEdgeStyle(e,allEdges);
    const A=toScreen(a),B=toScreen(b);
    ctx.strokeStyle=st.color;ctx.lineWidth=Math.max(0.6,st.width*Math.min(1,s));
    ctx.setLineDash(st.dash);
    ctx.beginPath();ctx.moveTo(A.x,A.y);ctx.lineTo(B.x,B.y);ctx.stroke();
    ctx.setLineDash([]);
  });
  const labelPx=Math.min(GRAPH_LABEL_MAX,Math.max(GRAPH_LABEL_MIN,GRAPH_LABEL_BASE*s));
  const showLabels=s>gfLabelThreshold;
  ctx.font=`600 ${labelPx}px -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif`;
  ctx.textAlign='center';ctx.textBaseline='alphabetic';
  const coverageMode=graphLayer==='coverage'||graphLayer==='vault';
  nodes.forEach(n=>{
    const P=toScreen(n);
    const baseR=(4+Math.min(6,Math.sqrt(n.deg||1)*1.2))*gfNodeScale;
    const r=(hi.has(n.id)?baseR+3:baseR)*Math.max(0.8,Math.min(1.4,s));
    if(coverageMode&&n.score!=null&&n.kind!=='code'){
      ctx.strokeStyle=scoreRingColor(n.score);
      ctx.lineWidth=3;ctx.beginPath();ctx.arc(P.x,P.y,r+3,0,Math.PI*2);ctx.stroke();
    }
    ctx.fillStyle=GRAPH_COLORS[n.kind]||'#8b95a5';
    if(coverageMode&&n.kind==='code')ctx.globalAlpha=0.45;
    ctx.beginPath();ctx.arc(P.x,P.y,r,0,Math.PI*2);ctx.fill();
    ctx.globalAlpha=1;
    if(hi.has(n.id)){
      ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.stroke();
    }
    if(showLabels){
      let label=(n.label||n.id).slice(0,24);
      const ty=P.y-r-4;
      ctx.lineWidth=3;ctx.strokeStyle='rgba(14,17,22,0.85)';
      ctx.strokeText(label,P.x,ty);
      ctx.fillStyle=hi.has(n.id)?'#fff':'#cdd4e0';
      ctx.fillText(label,P.x,ty);
    }
  });
  window._graphScreenNodes=nodes.map(n=>{const P=toScreen(n);return {...n,sx:P.x,sy:P.y,sr:6}});
}

async function mountGraph(){
  const el=document.getElementById('main');
  if(el&&tab==='dashboard'&&!graphData){
    el.innerHTML=`<div class="section">Knowledge dashboard</div>
      <div class="empty"><span class="pending-spinner" style="display:inline-block;vertical-align:middle;margin-right:8px"></span>Loading vault audit…</div>`;
  }
  try{
    graphData=await api(API_GRAPH);
    graphLayout=null;
    if(el&&tab==='dashboard')el.innerHTML=rGraph();
    graphPaint();bindGraphEvents();graphFit();
    renderAgenticLoopMermaid();
    if(!window._graphResizeBound){
      window._graphResizeBound=1;
      window.addEventListener('resize',()=>{if(tab==='dashboard')graphPaint()});
    }
  }catch(e){
    const w=document.getElementById('graph-wrap');
    if(w)w.innerHTML=`<div class="empty">Dashboard unavailable (${esc(e.message)})</div>`;
  }
}

"""
