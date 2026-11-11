import {COLORS,DAY,dateLabel,number,percent,escapeHtml as e,safeEvidence,stateQuery,eventInvestigation} from './model.mjs?v=7';

export function createEventInvestigator({bundle,state,table,scaffold,drawLine,node,syncURL,toast}) {
  const $=id=>document.getElementById(id);
  let current,returnEvent='';
  const href=id=>`?${stateQuery({...state,event:id})}#investigation`;

  function draw() {
    if(!current||$('investigation').hidden)return;
    const {event,points}=current;
    const values=points.flatMap(point=>[point.views,point.trailing_7_day_mean]).filter(value=>value!=null);
    const svg=$('event-chart');
    const scales=scaffold(svg,`${event.label}: attention around the event`,
      '29 UTC dates, 14 days before through 14 days after. Daily pageviews and trailing seven-day mean. Event day and fixed comparison windows are marked. All dates and coverage states are in the table below.',
      -14,14,Math.max(1,...values)*1.12,value=>Math.round(value)===0?'Event day':`${Math.round(value)>0?'+':''}${Math.round(value)}d`,'ARTICLE PAGEVIEWS');
    for(const [start,end,color] of [[-7.5,-.5,COLORS[3]],[-.5,6.5,COLORS[2]]]){
      const background=node('rect',{x:scales.x(start),y:scales.top,width:scales.x(end)-scales.x(start),height:scales.bottom-scales.top,fill:color,opacity:'.08'});
      svg.insertBefore(background,svg.children[2]||null);
    }
    const x=scales.x(0);
    svg.append(node('line',{x1:x,x2:x,y1:scales.top,y2:scales.bottom,stroke:COLORS[1],'stroke-dasharray':'4 5'}));
    drawLine(svg,points,point=>point.relative_day,point=>point.views,scales,COLORS[0]);
    drawLine(svg,points,point=>point.relative_day,point=>point.trailing_7_day_mean,scales,COLORS[2],'6 5');
    if(!values.length)svg.append(node('text',{x:(scales.left+scales.right)/2,y:150,'text-anchor':'middle'},'No observations in this context window.'));
  }

  function render() {
    const panel=$('investigation');
    panel.hidden=!state.event;
    current=state.event?eventInvestigation(bundle.analysis,state.event):null;
    if(!state.event)return;
    $('investigation-content').hidden=!current;
    if(!current){
      $('investigation-title').textContent='Event unavailable';
      $('investigation-subtitle').textContent='This event is not in the verified snapshot.';
      $('investigation-status').textContent='Choose another event from the timeline, or close this investigation.';
      return;
    }
    const {event,series,points,nearby}=current;
    $('investigation-title').textContent=event.label;
    $('investigation-subtitle').textContent=`${series.label} · ${dateLabel(event.date)} · ${event.status==='scheduled'?'Scheduled; occurrence unverified':event.kind}`;
    const messages={
      available:'Both seven-day windows are complete. The change is a descriptive association, not a measured causal effect.',
      scheduled:'Scheduled event: no measured effect is assigned, even if the calendar date passes.',
      incomplete:'A comparison window is incomplete. The change is withheld; partial observations remain visible in the chart and table.',
      zero_baseline:'The complete before window has zero mean views. A percentage change cannot be calculated.'
    };
    $('investigation-status').textContent=messages[event.analysis_status]||'A measured comparison is unavailable.';
    $('investigation-metrics').innerHTML=[
      ['BEFORE · 7-DAY MEAN',number(event.before.mean_views,1),`${event.before.observed_days}/7 observed days · ${event.before.start} to ${event.before.end}`],
      ['AFTER · 7-DAY MEAN',number(event.after.mean_views,1),`${event.after.observed_days}/7 observed days · ${event.after.start} to ${event.after.end}`],
      ['CHANGE IN MEAN',event.analysis_status==='available'?percent(event.percent_change):'Unavailable','Event day is included in the after window']
    ].map(([label,value,note])=>`<div class="metric"><span class="metric-label">${e(label)}</span><span class="metric-value">${e(value)}</span><span class="metric-note">${e(note)}</span></div>`).join('');
    $('investigation-verification').textContent=event.verification;
    $('investigation-source').href=safeEvidence(event.source_url);
    $('investigation-nearby').innerHTML=nearby.length?`<ul>${nearby.map(item=>`<li><a data-event="${e(item.id)}" href="${e(href(item.id))}">${e(item.date)} · ${e(item.label)}</a> <span class="caption">(${e(item.status)})</span></li>`).join('')}</ul>`:'<p>No other catalogued events for this title in the 29-day window. This catalogue is not exhaustive.</p>';
    $('investigation-title-note').textContent=`Exact article: ${series.article}. ${series.notes} Pageviews are not unique readers, sales or sentiment.`;
    $('investigation-table').innerHTML=table(['Relative day','UTC date','Daily views','Trailing 7-day mean','Coverage state'],points.map(point=>[point.relative_day,point.date,number(point.views),number(point.trailing_7_day_mean,1),point.state]),'All 29 calendar dates. Nulls stay unavailable; zero views are observed values.');
    $('investigation-identity').textContent=`Data as of ${bundle.data.as_of} UTC. Source: ${bundle.dataPointer.snapshot_id}. Analysis: ${bundle.analysisPointer.analysis_id}. Source checks: ${bundle.data.events_checked_on}.`;
    draw();
  }

  function choose(id) {
    returnEvent=id;state.event=id;syncURL('#investigation',true);render();
    requestAnimationFrame(()=>{
      $('investigation-title').focus({preventScroll:true});
      $('investigation').scrollIntoView({behavior:'instant',block:'start'});
    });
  }
  $('timeline').addEventListener('click',event=>{
    const link=event.target.closest('a[data-event]');
    if(!link||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey||event.button!==0)return;
    event.preventDefault();choose(link.dataset.event);
  });
  $('close-investigation').addEventListener('click',()=>{
    state.event='';syncURL('#timeline',true);render();
    const link=[...$('events').querySelectorAll('a[data-event]')].find(item=>item.dataset.event===returnEvent);
    (link||$('event-filter')).focus();
  });
  $('share-event').addEventListener('click',async()=>{
    syncURL('#investigation');
    try{await navigator.clipboard.writeText(location.href);toast('Event link copied.');}
    catch{toast('Copy the current address to share this event investigation.');}
  });
  return {render,draw,href};
}
