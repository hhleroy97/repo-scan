"""Canvas pan/zoom/pinch and node tap handlers for the knowledge dashboard."""

_FRAGMENT = r"""function graphZoom(f,cx,cy){
  const wrap=document.getElementById('graph-wrap');
  if(!wrap)return;
  const r=wrap.getBoundingClientRect();
  cx=cx==null?r.width/2:cx;cy=cy==null?r.height/2:cy;
  const newScale=Math.min(5,Math.max(0.2,graphView.scale*f));
  const k=newScale/graphView.scale;
  graphView.x=cx-(cx-graphView.x)*k;
  graphView.y=cy-(cy-graphView.y)*k;
  graphView.scale=newScale;
  graphPaint();
}
function graphHitScreen(sx,sy){
  const nodes=window._graphScreenNodes||[];
  for(let i=nodes.length-1;i>=0;i--){
    const n=nodes[i],dx=n.sx-sx,dy=n.sy-sy;
    if(dx*dx+dy*dy<=14*14)return n;
  }
  return null;
}
function bindGraphEvents(){
  const wrap=document.getElementById('graph-wrap');
  const canvas=document.getElementById('graph-canvas');
  if(!wrap||!canvas||canvas.dataset.bound)return;
  canvas.dataset.bound='1';
  const pointers=new Map();
  function localXY(e){
    const r=canvas.getBoundingClientRect();
    return {x:e.clientX-r.left,y:e.clientY-r.top};
  }
  canvas.addEventListener('pointerdown',e=>{
    canvas.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId,localXY(e));
    if(pointers.size===1){
      graphDrag={...localXY(e),ox:graphView.x,oy:graphView.y,moved:false,id:e.pointerId};
    }else if(pointers.size===2){
      const [a,b]=[...pointers.values()];
      graphPinch={d:Math.hypot(a.x-b.x,a.y-b.y),scale:graphView.scale,
        cx:(a.x+b.x)/2,cy:(a.y+b.y)/2,tx:graphView.x,ty:graphView.y};
      graphDrag=null;
    }
  });
  canvas.addEventListener('pointermove',e=>{
    if(!pointers.has(e.pointerId))return;
    pointers.set(e.pointerId,localXY(e));
    if(graphPinch&&pointers.size===2){
      const [a,b]=[...pointers.values()];
      const d=Math.hypot(a.x-b.x,a.y-b.y);
      const ns=Math.min(5,Math.max(0.2,graphPinch.scale*(d/graphPinch.d)));
      const k=ns/graphPinch.scale;
      graphView.scale=ns;
      graphView.x=graphPinch.cx-(graphPinch.cx-graphPinch.tx)*k;
      graphView.y=graphPinch.cy-(graphPinch.cy-graphPinch.ty)*k;
      graphPaint();
    }else if(graphDrag&&e.pointerId===graphDrag.id){
      const p=localXY(e);
      const dx=p.x-graphDrag.x,dy=p.y-graphDrag.y;
      if(Math.hypot(dx,dy)>4)graphDrag.moved=true;
      graphView.x=graphDrag.ox+dx;graphView.y=graphDrag.oy+dy;
      graphPaint();
    }
  });
  function endPointer(e){
    if(graphDrag&&e.pointerId===graphDrag.id&&!graphDrag.moved){
      const p=localXY(e),hit=graphHitScreen(p.x,p.y);
      if(hit)openGraphChain(hit);
    }
    pointers.delete(e.pointerId);
    if(pointers.size<2)graphPinch=null;
    if(pointers.size===0)graphDrag=null;
  }
  canvas.addEventListener('pointerup',endPointer);
  canvas.addEventListener('pointercancel',endPointer);
  canvas.addEventListener('wheel',e=>{
    e.preventDefault();
    const r=canvas.getBoundingClientRect();
    graphZoom(e.deltaY<0?1.12:0.9,e.clientX-r.left,e.clientY-r.top);
  },{passive:false});
}

"""
