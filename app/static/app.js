const $ = (id) => document.getElementById(id);
let fleetData=[], metricData=[], latencyChart, cpuChart;
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
async function api(path, options={}) {
  const response = await fetch(path, {headers:{"Content-Type":"application/json"}, ...options});
  const data = await response.json().catch(()=>({detail:"Unexpected server response"}));
  if(!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}
function toast(msg){const t=$("toast");t.textContent=msg;t.classList.add("show");setTimeout(()=>t.classList.remove("show"),3600)}
function statusClass(status){return status==="HEALTHY"?"healthy":status==="CRITICAL"?"critical":status==="WARNING"?"warning":"info"}
function renderFleet(data){
 fleetData=data.items; $("healthyCount").textContent=`${data.summary.healthy} Healthy`; $("warningCount").textContent=`${data.summary.warning} Warning`; $("criticalCount").textContent=`${data.summary.critical} Critical`;
 $("fleetGrid").innerHTML=fleetData.map((d,i)=>`<article class="db-card ${d.status==="WARNING"?"warning-card":d.status==="CRITICAL"?"critical-card":""}"><div class="db-head"><h3>${esc(d.name)}<br><span class="db-engine">${esc(d.engine)} · ${esc(d.database)}</span></h3><span class="pill ${statusClass(d.status)}">${esc(d.status)}</span></div><div class="host">Host: ${esc(d.host)} · Port: ${d.port}</div><div class="mini-stats"><div class="mini-stat"><span>CPU</span><b>${d.cpu_pct==null?"--%":d.cpu_pct+"%"}</b></div><div class="mini-stat"><span>Latency</span><b>${d.latency_ms==null?"-- ms":d.latency_ms+" ms"}</b></div></div><button class="button outline" data-view="${esc(d.id)}">View database</button></article>`).join("");
 $("targetSelect").innerHTML=fleetData.map(d=>`<option value="${esc(d.id)}">${esc(d.name)} (${esc(d.engine)}) — ${esc(d.status)}</option>`).join("");
 const warning=fleetData.some(d=>d.status==="WARNING"); $("globalStatus").className=`pill ${warning?"warning":"healthy"}`;$("globalStatus").innerHTML=`<i></i> ${warning?"WARNING":"HEALTHY"}`;
 document.querySelectorAll("[data-view]").forEach(b=>b.addEventListener("click",()=>{const d=fleetData.find(x=>x.id===b.dataset.view);$("targetSelect").value=d.id;toast(`${d.name}: ${d.source==="demo"?"illustrative demo target":"not yet verified against a live database"}.`)}));
}
function renderCharts(items){
 metricData=items;
 const labels=items.map(m=>m.time);
 const common={responsive:true,maintainAspectRatio:false,animation:{duration:250},plugins:{legend:{labels:{color:"#aab6c8",boxWidth:24,font:{family:"Inter",size:10}}}},scales:{x:{ticks:{color:"#8492a7",maxRotation:0,autoSkip:true,font:{size:9}},grid:{color:"#202a3a"}},y:{ticks:{color:"#8492a7",font:{size:9}},grid:{color:"#202a3a"}}}};
 if(latencyChart){latencyChart.data.labels=labels;latencyChart.data.datasets[0].data=items.map(m=>m.latency_ms);latencyChart.update();cpuChart.data.labels=labels;cpuChart.data.datasets[0].data=items.map(m=>m.cpu_pct);cpuChart.data.datasets[1].data=items.map(m=>m.connections);cpuChart.update();return}
 latencyChart=new Chart($("latencyChart"),{type:"line",data:{labels,datasets:[{label:"Query Latency (ms)",data:items.map(m=>m.latency_ms),borderColor:"#08bad2",backgroundColor:"#08bad21b",fill:true,tension:.25,pointRadius:2,borderWidth:2}]},options:common});
 cpuChart=new Chart($("cpuChart"),{type:"line",data:{labels,datasets:[{label:"CPU Usage (%)",data:items.map(m=>m.cpu_pct),borderColor:"#f34b5c",tension:.25,pointRadius:2,borderWidth:2},{label:"Connections",data:items.map(m=>m.connections),borderColor:"#9270f5",tension:.1,pointRadius:2,borderWidth:2}]},options:common});
}
async function loadAnomalies(){
 const data=await api("/api/anomalies");$("kpiAnomalies").textContent=data.open_count;$("anomalyBadge").textContent=`${data.open_count} Open`;
 $("anomalyList").innerHTML=data.items.slice(0,6).map(a=>`<article class="list-card"><div class="list-meta"><span class="pill ${a.severity==="critical"?"critical":"warning"}">${esc(a.type)}</span><span class="pill info">${esc(a.status)}</span><small class="muted">${new Date(a.created_at).toLocaleTimeString()}</small></div><h3>${esc(a.title)}</h3><p>${esc(a.details)}</p><div class="list-meta"><span class="muted">Isolation Forest score (demo):</span><b style="color:var(--cyan)">${esc(a.score)}</b></div></article>`).join("")||'<div class="empty">No open anomalies.</div>';
}
async function loadRecommendations(){
 const data=await api("/api/recommendations");$("kpiRecommendations").textContent=data.items.filter(r=>r.status==="RECOMMENDED").length;
 $("recommendationList").innerHTML=data.items.map(r=>`<article class="list-card"><div class="list-meta"><span class="pill ${r.severity==="high"?"critical":"warning"}">${esc(r.severity.toUpperCase())}</span><span class="pill info">${esc(r.status)}</span></div><h3>${esc(r.title)}</h3><p>${esc(r.reason)}</p><div class="mono">${esc(r.sql)}</div><div class="action-row"><button class="button primary" data-action="approve" data-id="${r.id}">Approve for review</button><button class="button outline" data-action="dismiss" data-id="${r.id}">Dismiss</button><button class="button outline" data-action="rollback_preview" data-id="${r.id}">Rollback preview</button></div></article>`).join("");
 document.querySelectorAll("[data-action]").forEach(b=>b.addEventListener("click",async()=>{try{const r=await api("/api/actions",{method:"POST",body:JSON.stringify({recommendation_id:b.dataset.id,action:b.dataset.action})});toast(r.message);await loadRecommendations();await loadAudit()}catch(e){toast(e.message)}}));
}
async function loadAudit(){
 const data=await api("/api/audit");$("auditRows").innerHTML=data.items.length?data.items.map(a=>`<tr><td>${esc(new Date(a.timestamp).toLocaleString())}</td><td>${esc(a.action)}</td><td>${esc(a.executed_by)}</td><td>${esc(a.details)}</td><td><span class="pill info">${esc(a.status)}</span></td></tr>`).join(""):'<tr><td colspan="5" class="empty">No audit logs yet.</td></tr>';
}
async function refresh(){
 try{
 const [f,m]=await Promise.all([api("/api/fleet"),api("/api/metrics")]);renderFleet(f);renderCharts(m.items);
 const last=m.items[m.items.length-1];$("kpiLatency").innerHTML=`${last.latency_ms} <small>ms</small>`;$("kpiCpu").innerHTML=`${last.cpu_pct}<small>%</small>`;$("kpiConnections").textContent=last.connections;
 await Promise.all([loadAnomalies(),loadRecommendations(),loadAudit()]);
 }catch(e){toast(`API unavailable: ${e.message}`)}
}
document.querySelectorAll("[data-scenario]").forEach(b=>b.addEventListener("click",async()=>{b.disabled=true;try{const result=await api("/api/workload",{method:"POST",body:JSON.stringify({scenario:b.dataset.scenario})});$("simMessage").hidden=false;$("simMessage").textContent=result.message;toast(`Scenario complete: ${result.scenario.replaceAll("_"," ")}`);await refresh()}catch(e){toast(e.message)}finally{b.disabled=false}}));
$("connectOpen").addEventListener("click",()=>{$("connectModal").classList.add("open");$("connectModal").setAttribute("aria-hidden","false")});
document.querySelectorAll("[data-close]").forEach(b=>b.addEventListener("click",()=>{$("connectModal").classList.remove("open");$("connectModal").setAttribute("aria-hidden","true")}));
$("connectForm").addEventListener("submit",async e=>{e.preventDefault();const form=new FormData(e.target);const body=Object.fromEntries(form.entries());body.port=Number(body.port);try{const result=await api("/api/connect",{method:"POST",body:JSON.stringify(body)});$("connectResult").hidden=false;$("connectResult").textContent=result.message;e.target.password.value="";await refresh();toast("Target added as unverified.")}catch(err){toast(err.message)}});
$("refreshAudit").addEventListener("click",loadAudit);$("signOut").addEventListener("click",()=>toast("Demo mode: no authentication session is configured."));
refresh();setInterval(refresh,5000);
