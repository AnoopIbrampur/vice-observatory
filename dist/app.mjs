import {IDS,COLORS,DASHES,DAY,number,percent,dateLabel,compact,escapeHtml as e,parseState,stateQuery,selectedDates,selectedGames,comparisonAvailability,segments,safeEvidence,loadBundle,loadPublished,filterEvents} from './model.mjs';

const $ = id => document.getElementById(id);
const NS = 'http://www.w3.org/2000/svg';
const state = parseState(location.search);
let bundle, vi, visibleDates = [], cursorIndex = 0, toastTimer;
const shortDate = value => new Date(`${value}T00:00:00Z`).toLocaleDateString('en-GB',{day:'numeric',month:'short',timeZone:'UTC'});
function node(tag,attrs={},text) {const el=document.createElementNS(NS,tag);for(const [key,value] of Object.entries(attrs)) el.setAttribute(key,String(value));if(text!=null)el.textContent=text;return el;}
function table(headers,rows,caption) {return `<table><caption>${e(caption)}</caption><thead><tr>${headers.map(label=>`<th scope="col">${e(label)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(value=>`<td>${e(value)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;}
function syncURL() {history.replaceState(null,'',`${location.pathname}?${stateQuery(state)}${location.hash}`);}
function toast(text) {clearTimeout(toastTimer);$('toast').textContent=text;$('toast').hidden=false;toastTimer=setTimeout(()=>$('toast').hidden=true,3500);}

function scaffold(svg,title,description,minX,maxX,maxY,xLabel,yLabel) {
  svg.replaceChildren(node('title',{id:svg.id==='attention-chart'?'attention-title':'comparison-title'},title),node('desc',{id:svg.id==='attention-chart'?'attention-description':'comparison-description'},description));
  const width=Math.max(280,Math.round(svg.parentElement.clientWidth)),height=width<600?280:340;
  svg.setAttribute('viewBox',`0 0 ${width} ${height}`);
  const left=width<600?46:65,right=width-18,top=30,bottom=height-45;
  const x=value=>left+(value-minX)/(maxX-minX||1)*(right-left), y=value=>bottom-value/(maxY||1)*(bottom-top);
  for(let i=0;i<=4;i++){const value=maxY*i/4,position=y(value);svg.append(node('line',{x1:left,x2:right,y1:position,y2:position,class:'grid-line'}),node('text',{x:left-12,y:position+4,'text-anchor':'end'},compact(value)));}
  const ticks=width<600?2:4;
  for(let i=0;i<=ticks;i++){const value=minX+(maxX-minX)*i/ticks;svg.append(node('text',{x:x(value),y:bottom+25,'text-anchor':i===0?'start':i===ticks?'end':'middle'},xLabel(value)));}
  svg.append(node('text',{x:left,y:14,class:'axis-label'},yLabel));
  return {x,y,left,right,top,bottom,width};
}
function drawLine(svg,points,getX,getY,scales,color,dash='') {const d=segments(points,getX,getY,scales.x,scales.y);if(d)svg.append(node('path',{d,stroke:color,'stroke-dasharray':dash,class:'series-line'}));}

function renderOverview() {
  const summary=vi.summary, change=summary.week_change.percent;
  const scheduledDays=Math.round((Date.parse(vi.release_date)-Date.parse(bundle.data.as_of))/DAY);
  const fourth=vi.release_status==='scheduled' && scheduledDays>0 ? [number(scheduledDays)+' days','TO SCHEDULED LAUNCH',dateLabel(vi.release_date)+' · at snapshot date'] : [dateLabel(vi.release_date),'RELEASE DATE',vi.release_status==='scheduled'?'Scheduled · occurrence unverified':'Verified historical release'];
  $('metrics').innerHTML=[['LATEST DAILY VIEWS',number(summary.latest_views),dateLabel(summary.observed_end)+' · UTC'],['7-DAY AVERAGE',number(summary.trailing_7_day_mean),'Mean daily article pageviews'],['7-DAY CHANGE',percent(change),'vs immediately preceding 7 days'],[fourth[1],fourth[0],fourth[2]]].map(([label,value,note],i)=>`<div class="metric"><span class="metric-label">${e(label)}</span><span class="metric-value ${i===2&&change>0?'positive':''}">${e(value)}</span><span class="metric-note">${e(note)}</span></div>`).join('');
  $('snapshot-badge').textContent=`SNAPSHOT · ${dateLabel(summary.observed_end).toUpperCase()}`;
  const age=Math.floor((Date.now()-Date.parse(bundle.data.collected_at))/DAY);
  $('freshness').textContent=`Observations through ${dateLabel(summary.observed_end)} UTC. Retrieved ${dateLabel(bundle.data.collected_at.slice(0,10))}. ${age>2?`Saved snapshot is ${age} days old. `:''}Snapshot date: ${dateLabel(bundle.data.as_of)}. ${bundle.publication ? bundle.publication.schedule : "Bundled snapshot."} ${bundle.fallback ? "Daily publication unavailable; showing the bundled verified snapshot." : ""} ${bundle.publication?.history[0]?.status==='failed_retained_last_good'?'Latest refresh failed; retaining the last verified observations.':''}`;
  $('range').value=state.range;$('metric').value=state.metric;
  drawAttention();
}

function drawAttention(preserveDate=false) {
  const previousDate=preserveDate?visibleDates[cursorIndex]?.date:null;
  visibleDates=selectedDates(vi,state.range);cursorIndex=previousDate?visibleDates.findIndex(row=>row.date===previousDate):visibleDates.length-1;
  if(cursorIndex<0)cursorIndex=visibleDates.length-1;
  $('daily-legend').hidden=state.metric==='mean';$('mean-legend').hidden=state.metric==='views';
  const svg=$('attention-chart');
  const min=Date.parse(visibleDates[0].date),max=Date.parse(visibleDates.at(-1).date);
  const shownValues=visibleDates.flatMap(row=>state.metric==='views'?[row.views]:state.metric==='mean'?[row.trailing_7_day_mean]:[row.views,row.trailing_7_day_mean]).filter(v=>v!=null);
  const scales=scaffold(svg,'GTA VI attention over time',`${visibleDates.length} observed dates. Showing ${state.metric==='mean'?'the trailing seven-day mean':state.metric==='views'?'daily pageviews':'daily pageviews and the trailing seven-day mean'}. Full values are in the table below.`,min,max,Math.max(1,...shownValues)*1.12,value=>new Date(value).toLocaleDateString('en-GB',state.range==='all'||state.range==='365'?{month:'short',year:'numeric',timeZone:'UTC'}:{day:'numeric',month:'short',timeZone:'UTC'}),'ARTICLE PAGEVIEWS');
  const markers=bundle.analysis.events.filter(event=>event.series_id==='gta-vi'&&event.status==='occurred'&&Date.parse(event.date)>=min&&Date.parse(event.date)<=max);
  for(const event of markers) {
    const stamp=Date.parse(event.date);if(stamp<min||stamp>max)continue;
    const x=scales.x(stamp),line=node('line',{x1:x,x2:x,y1:scales.top,y2:scales.bottom,stroke:'#ead09a','stroke-dasharray':'3 5',opacity:'.7'});
    line.append(node('title',{},event.label));svg.append(line);
    if(markers.length<=2)svg.append(node('text',{x:Math.max(scales.left,Math.min(x+6,scales.right-210)),y:scales.top+14,class:'chart-label'},`${dateLabel(event.date)} · ${event.kind}`));
  }
  if(state.metric!=='mean')drawLine(svg,visibleDates,row=>Date.parse(row.date),row=>row.views,scales,COLORS[0]);
  if(state.metric!=='views')drawLine(svg,visibleDates,row=>Date.parse(row.date),row=>row.trailing_7_day_mean,scales,COLORS[2],'6 5');
  const guide=node('line',{id:'inspection-guide',y1:scales.top,y2:scales.bottom,stroke:'#f4f1e9',opacity:'.35','stroke-dasharray':'3 4'});svg.append(guide);
  const dot=node('circle',{id:'inspection-dot',r:4,fill:COLORS[0],stroke:'#101519','stroke-width':2});svg.append(dot);
  svg.onclick=event=>{const rect=svg.getBoundingClientRect(),relative=(event.clientX-rect.left)/rect.width*scales.width;cursorIndex=Math.max(0,Math.min(visibleDates.length-1,Math.round((relative-scales.left)/(scales.right-scales.left)*(visibleDates.length-1))));$('cursor').value=String(cursorIndex);inspect(scales);};
  $('cursor').max=String(visibleDates.length-1);$('cursor').value=String(cursorIndex);
  $('cursor').oninput=event=>{cursorIndex=Number(event.target.value);inspect(scales);};
  inspect(scales);
  $('attention-table').innerHTML=table(['UTC date','Daily views','Trailing 7-day mean'],visibleDates.map(row=>[row.date,number(row.views),number(row.trailing_7_day_mean,1)]),`${dateLabel(visibleDates[0].date)} to ${dateLabel(visibleDates.at(-1).date)} · exact selected observations`);
}
function inspect(scales) {
  const row=visibleDates[cursorIndex],x=scales.x(Date.parse(row.date)),value=state.metric==='mean'?row.trailing_7_day_mean:row.views;
  const text=`${shortDate(row.date)} ${row.date.slice(0,4)} · ${number(row.views)} views · mean ${number(row.trailing_7_day_mean)}`;
  $('inspection').textContent=text;$('cursor').setAttribute('aria-valuetext',text);
  $('inspection-guide').setAttribute('x1',x);$('inspection-guide').setAttribute('x2',x);
  $('inspection-dot').setAttribute('cx',x);$('inspection-dot').setAttribute('cy',scales.y(value??0));$('inspection-dot').setAttribute('fill',state.metric==='mean'?COLORS[2]:COLORS[0]);$('inspection-dot').style.display=value==null?'none':'';
}

function renderComparison() {
  $('mode').value=state.mode;$('originals').checked=state.originals;
  const fieldset=$('game-select');fieldset.innerHTML='<legend>Select releases</legend>';
  for(const game of bundle.analysis.series){const index=Math.max(0,state.games.indexOf(game.id))%COLORS.length;const label=document.createElement('label');
    const input=document.createElement('input');input.type='checkbox';input.checked=state.games.includes(game.id);input.dataset.game=game.id;
    input.disabled=state.originals&&game.release_kind!=='original_launch';label.style.color=input.disabled?'var(--dim)':COLORS[index];
    const key=node('svg',{width:19,height:8,'aria-hidden':'true',viewBox:'0 0 19 8'});key.append(node('path',{d:'M0 4 H19',stroke:COLORS[index],'stroke-width':2,'stroke-dasharray':DASHES[index]}));
    label.append(input,key,document.createTextNode(game.id==='gta-v-2022'?'GTA V · 2022 re-release':game.label));
    input.addEventListener('change',()=>{if(input.checked&&state.games.length>=4){input.checked=false;toast('Choose up to four releases. Deselect one to add another.');return;}state.games=input.checked?[...new Set([...state.games,game.id])]:state.games.filter(id=>id!==game.id);syncURL();renderComparison();});fieldset.append(label);
  }
  drawComparison();
}
function drawComparison() {
  const games=selectedGames(bundle.analysis.series,state),{available,unavailable}=comparisonAvailability(games,state.mode),svg=$('comparison-chart');
  $('comparison-note').textContent=unavailable.length?unavailable.map(game=>`${game.label}: index unavailable (${game.comparison.baseline.observed_days}/${game.comparison.baseline.expected_days} baseline days).`).join(' '):state.mode==='raw'?'Raw article traffic · empty future regions stay unobserved.':'Baseline = 100 · retrospective normalization, not a forecast.';
  const values=available.flatMap(game=>game.comparison.points.map(point=>state.mode==='raw'?point.views:point.index_100)).filter(value=>value!=null);
  const max=Math.max(1,...values)*1.12;
  const scales=scaffold(svg,'Release-aligned attention comparison',`Days minus 90 through plus 90. ${available.length} available series on the ${state.mode==='raw'?'raw pageview':'indexed'} scale. Missing and future values are not drawn. Data table below.`, -90,90,max,value=>Math.round(value)===0?'Release':`${value>0?'+':''}${Math.round(value)} days`,state.mode==='raw'?'ARTICLE PAGEVIEWS':'INDEX · BASELINE = 100');
  const zero=scales.x(0);svg.append(node('line',{x1:zero,x2:zero,y1:scales.top,y2:scales.bottom,stroke:'#b2bdc3','stroke-dasharray':'4 5',opacity:'.6'}));
  if(state.mode==='index'&&values.length)svg.append(node('line',{x1:scales.left,x2:scales.right,y1:scales.y(100),y2:scales.y(100),stroke:'#99d4c7',opacity:'.4','stroke-dasharray':'2 6'}));
  for(const game of available){const index=Math.max(0,state.games.indexOf(game.id))%COLORS.length;drawLine(svg,game.comparison.points,p=>p.relative_day,p=>state.mode==='raw'?p.views:p.index_100,scales,COLORS[index],DASHES[index]);}
  if(!available.length)svg.append(node('text',{x:(scales.left+scales.right)/2,y:160,'text-anchor':'middle',class:'empty-chart'},games.length?'Index unavailable; try raw views.':'Select a release to compare.'));
  $('comparison-summary').textContent=available.length?`Showing ${available.map(game=>game.label).join('; ')}. Series use distinct solid/dashed line patterns. ${state.mode==='index'?'An index of 200 means twice that title’s own baseline, not twice another title’s audience.':'Each line uses its own release date; future GTA VI observations remain empty.'}`:'Use the release selectors or switch to raw daily views.';
  $('comparison-table').innerHTML=table(['Release','Relative day','UTC date','Daily views','Index (100 baseline)','Observation status'],games.flatMap(game=>game.comparison.points.map(point=>[game.label,point.relative_day,point.date,number(point.views),number(point.index_100,1),point.state])),`Selected releases · all ${games.length*181} aligned dates, including unavailable observations`);
}

function renderEvents() {
  $('event-filter').value=state.events;$('event-kind').value=state.kind;$('event-status').value=state.status;$('event-search').value=state.query;
  const events=filterEvents(bundle.analysis.events,{series:state.events,kind:$('event-kind').value,status:$('event-status').value,query:$('event-search').value});
  $('event-count').textContent=`${events.length} matching events. Seven complete days on each side are required for a measured change.`;
  $('events').innerHTML=events.length?events.map(event=>`<li><time class="event-date" datetime="${e(event.date)}">${e(dateLabel(event.date))}</time><div><span class="event-tag ${event.status==='scheduled'?'scheduled':''}">${event.status==='scheduled'?'Scheduled · not observed':event.kind==='rerelease'?'Console re-release':event.kind==='announcement'?'Announcement':event.kind==='trailer'?'Trailer':'Original launch'}</span><h3>${e(event.label)}</h3><p class="caption">${e(event.verification)}</p><p class="caption">Before: ${event.before.observed_days}/7 days · After: ${event.after.observed_days}/7 days. ${e(event.interpretation)}</p><a href="${e(safeEvidence(event.source_url))}" target="_blank" rel="noopener">Publisher source ↗</a></div><div class="event-effect">${event.analysis_status==='available'?e(percent(event.percent_change)):'—'}<small>${event.analysis_status==='available'?'7-day mean change<br>before vs after':event.status==='scheduled'?'Awaiting observed data':'Incomplete comparison window'}</small></div></li>`).join(''):'<li>No matching events. Try a different title, clear the search, or choose all event types.</li>';
}
function renderEvidence() {
  const {data,analysis,dataPointer,analysisPointer}=bundle,bench=analysis.benchmark;
  const yesterdayWins=bench.series.filter(game=>game.lowest_mae_method==='yesterday').length;
  const weeklyLaunchWins=bench.series.filter(game=>game.regimes.launch_days.methods.trailing_week.mae<game.regimes.launch_days.methods.yesterday.mae).map(game=>game.label);
  $('benchmark-copy').textContent=`Across ${bench.pooled.scored_days} fixed historical targets, yesterday’s count has lower full-window MAE in ${yesterdayWins} of ${bench.series.length} releases. ${weeklyLaunchWins.length?`The weekly mean does better in the three-day release window for ${weeklyLaunchWins.join('; ')}. `:''}Full regime results are in the findings download.`;
  $('benchmark-table').innerHTML=table(['Historical release','Yesterday MAE','Weekly mean MAE'],bench.series.map(game=>[game.label,number(game.overall.methods.yesterday.mae,1),number(game.overall.methods.trailing_week.mae,1)]),'Mean absolute error · pageviews per day · lower is better');
  $('health').innerHTML=table(['Source series','First day','Last day','Days','Missing','Coverage'],data.health.series.map(health=>[data.series.find(game=>game.id===health.series_id).label,health.first_observed,health.last_observed,number(health.observations),number(health.missing_days),`${health.coverage_fraction*100}%`]),'Complete requested coverage does not establish complete article-title history.');
  if(bundle.audit){$('title-audit').innerHTML=table(['Title','Canonical article','Page created','Incoming redirects','Audit flags'],bundle.audit.series.map(item=>[data.series.find(game=>game.id===item.series_id)?.label||item.series_id,item.canonical_article,item.created_at.slice(0,10),item.incoming_redirects.length,item.flags.join('; ')||'No flags in this bounded check']),bundle.audit.limitation);}
  if(bundle.publication){$('refresh-history').innerHTML=table(['Attempt (UTC)','Result','Data as of','Details'],bundle.publication.history.map(item=>[item.at,item.status,item.as_of,item.message||'Validated source + analysis + title audit']), 'Last 30 publication attempts. Validated means ready for publication; deployment status is recorded by GitHub Actions.');}
  const groups=bench.release_groups;
  if(groups){$('benchmark-groups').innerHTML=table(['Cohort','Targets','Yesterday WAPE','Weekly WAPE'],Object.entries(groups).map(([kind,score])=>[kind,score.scored_days,number(score.methods.yesterday.wape*100,1)+'%',number(score.methods.trailing_week.wape*100,1)+'%']),'Original launches and console re-releases scored separately; error ratio, lower is better.');}
  $('identity').textContent=`SHA-256 verified in this browser. Source snapshot: ${dataPointer.snapshot_id}. Analysis snapshot: ${analysisPointer.analysis_id}. Event sources last checked ${data.events_checked_on}.`;
  const base=bundle.base||'.';
  const downloads=[['Observations CSV',`${base}/data/${dataPointer.csv}`],['Comparisons CSV',`${base}/analysis/${analysisPointer.files['comparisons.csv']}`],['Predictions CSV',`${base}/analysis/${analysisPointer.files['predictions.csv']}`],['Findings',`${base}/analysis/${analysisPointer.files['findings.md']}`],['Analysis JSON',`${base}/analysis/${analysisPointer.files['analysis.json']}`]];
  $('downloads').replaceChildren(...downloads.map(([label,url])=>{const link=document.createElement('a');link.href=url;link.download=url.split('/').at(-1);link.textContent=label+' ↓';return link;}));
}

async function start() {
  try {
    bundle=await loadPublished(fetch,location.hostname==='localhost'||location.hostname==='127.0.0.1'?'':'https://anoopibrampur.github.io/vice-observatory');vi=bundle.analysis.series.find(game=>game.id==='gta-vi');$('application').hidden=false;
    const eventFilter=$('event-filter');
    for(const game of bundle.analysis.series.filter(game=>game.id!=='gta-vi')){const option=document.createElement('option');option.value=game.id;option.textContent=game.label;eventFilter.append(option);}
    if(!['all',...bundle.analysis.series.map(game=>game.id)].includes(state.events))state.events='gta-vi';
    renderOverview();renderComparison();renderEvents();renderEvidence();
    for(const [id,key] of [['event-kind','kind'],['event-status','status'],['event-search','query']])$(id).addEventListener(id==='event-search'?'input':'change',event=>{state[key]=event.target.value.slice(0,200);syncURL();renderEvents();});
    $('range').addEventListener('change',event=>{state.range=event.target.value;syncURL();drawAttention();});
    $('metric').addEventListener('change',event=>{state.metric=event.target.value;syncURL();drawAttention();});
    $('mode').addEventListener('change',event=>{state.mode=event.target.value;syncURL();drawComparison();});
    $('originals').addEventListener('change',event=>{state.originals=event.target.checked;if(state.originals)state.games=state.games.filter(id=>bundle.analysis.series.find(game=>game.id===id)?.release_kind==='original_launch');syncURL();renderComparison();});
    $('event-filter').addEventListener('change',event=>{state.events=event.target.value;syncURL();renderEvents();});
    $('share').addEventListener('click',async()=>{syncURL();try{await navigator.clipboard.writeText(location.href);toast('View link copied.');}catch{toast('Copy the current address from your browser to share this view.');}});
    let resizeTimer;window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{drawAttention(true);drawComparison();},120);});
    $('loading').hidden=true;$('application').hidden=false;
  } catch(error) {
    console.error('Snapshot load failed:',error.message);$('application').hidden=true;$('loading').hidden=true;$('error-message').textContent=error.message+' You can inspect the public source data or retry.';$('error').hidden=false;
  }
}
$('retry').addEventListener('click',()=>location.reload());
start();
