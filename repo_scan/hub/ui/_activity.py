"""Activity tab, document viewer helpers, and boot ``refresh``/``connectSSE``."""

_FRAGMENT = r"""function rActivity(){
  if(!S.activity.length)return `<div class="empty">No decisions recorded yet.</div>`;
  return `<div class="card">`+S.activity.map(a=>{
    const cls=/approved|auto/.test(a.decision)?'ok':(/rejected|denied/.test(a.decision)?'bad':'warn');
    return `<div class="run"><span class="dot ${cls==='ok'?'done':(cls==='bad'?'failed':'waiting-on-gate')}"></span>
      <span style="flex:1">${esc(a.summary).slice(0,90)}<br>
      <span class="dim small">${esc(a.when)} · ${esc(a.gate)}</span></span>
      <span class="badge ${cls}">${esc(a.decision)}</span></div>`}).join('')+`</div>`;
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
