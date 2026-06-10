"""Activity tab telemetry, stage burn chart, document viewer, and boot."""

_FRAGMENT = r"""function buildStageChartClient(stages,burnByStage){
  const by={};
  (stages||[]).forEach(s=>{
    const sid=s.stage_id||'unknown';
    if(!by[sid])by[sid]={stage_id:sid,duration_ms:0,tokens:0};
    by[sid].duration_ms+=s.duration_ms||0;
    by[sid].tokens+=(s.tokens_in||0)+(s.tokens_out||0);
  });
  Object.entries(burnByStage||{}).forEach(([sid,agg])=>{
    if(sid==='unknown'||!sid)return;
    if(!by[sid])by[sid]={stage_id:sid,duration_ms:0,tokens:0};
    if(!by[sid].tokens)by[sid].tokens=agg.tokens||0;
    if(!by[sid].duration_ms)by[sid].duration_ms=agg.duration_ms||0;
  });
  const rows=Object.values(by).filter(r=>r.duration_ms||r.tokens);
  if(!rows.length)return [];
  const totalMs=rows.reduce((a,r)=>a+r.duration_ms,0)||1;
  const totalTok=rows.reduce((a,r)=>a+r.tokens,0)||1;
  return rows.map(r=>({
    stage_id:r.stage_id,
    duration_ms:r.duration_ms,
    tokens:r.tokens,
    pct_time:Math.round(100*r.duration_ms/totalMs*10)/10,
    pct_tokens:Math.round(100*r.tokens/totalTok*10)/10,
    duration_s:Math.round(r.duration_ms/1000)
  })).sort((a,b)=>(b.duration_ms+b.tokens)-(a.duration_ms+a.tokens));
}
function fmtBurnDur(ms){
  const s=Math.round((ms||0)/1000);
  if(s<60)return s+'s';
  const m=Math.floor(s/60),r=s%60;
  return r?`${m}m ${r}s`:`${m}m`;
}
function renderBurnBars(chart,metaLabel){
  if(!chart.length)return '';
  let h=`<div class="burn-chart">`;
  if(metaLabel)h+=`<div class="burn-subtitle">${esc(metaLabel)}</div>`;
  h+=`<div class="burn-legend">
      <span><i class="burn-swatch time"></i> time %</span>
      <span><i class="burn-swatch tok"></i> tokens %</span>
    </div>`;
  chart.forEach(row=>{
    const sid=row.stage_id||'?';
    const pctT=Math.min(100,row.pct_time||0);
    const pctK=Math.min(100,row.pct_tokens||0);
    const dur=row.duration_s!=null?row.duration_s:Math.round((row.duration_ms||0)/1000);
    const tok=(row.tokens||0).toLocaleString();
    h+=`<div class="burn-row">
      <span class="burn-label" title="${esc(sid)}">${esc(sid.replace(/_/g,' '))}</span>
      <div class="burn-bars">
        <div class="burn-track"><div class="burn-fill time" style="width:${pctT}%"></div></div>
        <div class="burn-track"><div class="burn-fill tok" style="width:${pctK}%"></div></div>
      </div>
      <span class="burn-meta">${dur}s<br>${tok} tok</span>
    </div>`;
  });
  return h+`</div>`;
}
function setBurnView(v){window._burnView=v;render(true)}
function setBurnRun(id){window._burnRunId=id;render(true)}
function rStageBurnChart(){
  const tel=S.telemetry||{};
  const views=tel.views||{};
  const mode=window._burnView||'average';
  let chart=[],subtitle='';
  if(views.total||views.average||views.runs){
    const n=views.run_count||0;
    const hrs=views.hours||24;
    if(mode==='total'){
      chart=views.total||[];
      subtitle=`Total burn across ${n} run(s) · last ${hrs}h`;
    }else if(mode==='run'){
      const runs=views.runs||[];
      if(!runs.length)return '';
      let pick=runs.find(r=>r.id===(window._burnRunId||''));
      if(!pick)pick=runs[0];
      window._burnRunId=pick.id;
      chart=pick.chart||[];
      subtitle=`${pick.label} · ${fmtBurnDur(pick.total_ms)} · ${(pick.total_tokens||0).toLocaleString()} tok`;
    }else{
      chart=views.average||[];
      subtitle=`Avg per run (${n} run${n===1?'':'s'}) · last ${hrs}h`;
    }
  }else{
    chart=tel.chart||[];
    if(!chart.length)chart=buildStageChartClient(tel.stages,tel.burn?.by_stage);
    subtitle='Stage burn · last 24h';
  }
  if(!chart.length)return '';
  const tabs=[['average','Avg / run'],['total','Total'],['run','By run']];
  let h=`<div class="burn-tabs">`+
    tabs.map(([k,l])=>`<button type="button" class="burn-tab${mode===k?' active':''}" onclick="setBurnView('${k}')">${l}</button>`).join('')+
    `</div>`;
  if(mode==='run'&&(views.runs||[]).length){
    h+=`<select class="burn-run-select" onchange="setBurnRun(this.value)">`+
      views.runs.map(r=>`<option value="${esc(r.id)}"${r.id===window._burnRunId?' selected':''}>${esc(r.label)}</option>`).join('')+
      `</select>`;
  }
  return h+renderBurnBars(chart,subtitle);
}
function rTelemetry(){
  const tel=S.telemetry||{};
  const burn=tel.burn||{};
  const stages=tel.stages||[];
  const chartHtml=rStageBurnChart();
  if(!burn.today&&!stages.length&&!chartHtml)return '';
  let h='';
  const today=burn.today||{};
  if(today.tokens){
    const tpm=today.tokens_per_min||0;
    let line=`Today: ${today.tokens.toLocaleString()} tok`;
    if(tpm)line+=` · ${tpm.toLocaleString()} tok/min`;
    if(burn.budget_daily_tokens){
      const left=burn.budget_headroom;
      line+=` · budget ${burn.budget_daily_tokens.toLocaleString()}`
        +(left!=null?` (${left.toLocaleString()} left)`:'');
    }
    h+=`<div class="section">Pipeline telemetry</div><div class="card"><div class="dim small">${esc(line)}</div></div>`;
  }
  if(chartHtml){
    h+=`<div class="section">Stage burn</div><div class="card">${chartHtml}</div>`;
  }
  if(stages.length){
    h+=`<div class="section">Recent stages</div><div class="card">`;
    h+=stages.slice(-12).reverse().map(s=>{
      const tok=(s.tokens_in||0)+(s.tokens_out||0);
      const dur=Math.round((s.duration_ms||0)/1000);
      const tpm=dur&&tok?Math.round(tok*60/dur):0;
      return `<div class="run"><span style="flex:1">${esc(s.stage_id||'?')}</span>
        <span class="dim small">${dur}s</span>
        <span class="badge">${tok?tok.toLocaleString()+' tok':''}${tpm?' · '+tpm.toLocaleString()+'/min':''}</span></div>`;
    }).join('');
    h+=`</div>`;
  }
  return h;
}
function rActivity(){
  let h=rTelemetry();
  if(!S.activity.length){
    return h||`<div class="empty">No decisions recorded yet.</div>`;
  }
  h+=`<div class="section">Gate decisions</div><div class="card">`+S.activity.map(a=>{
    const cls=/approved|auto/.test(a.decision)?'ok':(/rejected|denied/.test(a.decision)?'bad':'warn');
    return `<div class="run"><span class="dot ${cls==='ok'?'done':(cls==='bad'?'failed':'waiting-on-gate')}"></span>
      <span style="flex:1">${esc(a.summary).slice(0,90)}<br>
      <span class="dim small">${esc(a.when)} · ${esc(a.gate)}</span></span>
      <span class="badge ${cls}">${esc(a.decision)}</span></div>`}).join('')+`</div>`;
  return h;
}

async function openDoc(rel){
  const viewer=document.getElementById('viewer');
  viewer.classList.add('open');
  document.getElementById('docpath').textContent=rel;
  document.getElementById('doctext').innerHTML=
    '<span class="pending-spinner" style="display:inline-block;vertical-align:middle;margin-right:8px"></span>Loading document…';
  try{const d=await api(API_DOC+'?path='+encodeURIComponent(rel));
    document.getElementById('docpath').textContent=d.path;
    document.getElementById('doctext').textContent=d.text}
  catch(e){viewer.classList.remove('open');toast('Cannot load doc: '+e.message)}
}
function closeDoc(){document.getElementById('viewer').classList.remove('open')}

refresh();
connectSSE();
</script>
</body>
</html>
"""
