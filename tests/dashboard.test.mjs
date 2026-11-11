import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {parseState,stateQuery,selectedDates,selectedGames,comparisonAvailability,segments,safeEvidence,escapeHtml,loadBundle,loadPublished,filterEvents,eventInvestigation} from '../dist/model.mjs';

const root=fileURLToPath(new URL('../dist/',import.meta.url));
async function localFetch(url) {
  const bytes=await readFile(root+url.replace(/^\.\//,''));
  return {ok:true,json:async()=>JSON.parse(bytes.toString()),arrayBuffer:async()=>bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength)};
}
test('invalid query values use safe defaults and unknown game IDs are discarded',()=>{
  const value=parseState('?range=-5&metric=bad&mode=bad&games=unknown,rdr2,rdr2&events=bad');
  assert.equal(value.range,'90');assert.equal(value.mode,'index');assert.equal(value.events,'gta-vi');assert.deepEqual(value.games,['rdr2']);
});
test('empty game selection survives a shared URL round trip',()=>{
  const state={...parseState(''),games:[],originals:true,range:'all',mode:'raw'};
  assert.deepEqual(parseState('?'+stateQuery(state)),state);
});
test('time window uses calendar dates, not a count of rows',()=>{
  const series={summary:{observed_end:'2026-11-10'},daily:[{date:'2026-10-11'},{date:'2026-10-12'},{date:'2026-11-10'}]};
  assert.deepEqual(selectedDates(series,'30'),series.daily.slice(1));
  assert.equal(selectedDates(series,'all').length,3);
});
test('original-launch filter excludes the console re-release without changing saved selection',()=>{
  const state={...parseState(''),originals:true};
  const games=[{id:'gta-v-2022',release_kind:'console_rerelease'},{id:'rdr2',release_kind:'original_launch'}];
  assert.deepEqual(selectedGames(games,state).map(g=>g.id),['rdr2']);assert.ok(state.games.includes('gta-v-2022'));
});
test('incomplete index is unavailable while raw comparison remains available',()=>{
  const games=[{id:'gta-vi',comparison:{baseline:{status:'incomplete'}}}];
  assert.equal(comparisonAvailability(games,'index').available.length,0);
  assert.equal(comparisonAvailability(games,'raw').available.length,1);
});
test('chart paths break at unavailable values rather than connecting future gaps',()=>{
  const path=segments([{x:0,y:0},{x:1,y:10},{x:2,y:null},{x:3,y:20}],p=>p.x,p=>p.y,x=>x,y=>y);
  assert.equal(path,'M0.00,0.00 L1.00,10.00 M3.00,20.00');
});
test('unsafe evidence schemes and credentials are rejected',()=>{
  assert.equal(safeEvidence('javascript:alert(1)'),'#method');assert.equal(safeEvidence('https://user:password@example.org'),'#method');
  assert.equal(safeEvidence('https://example.org/source'),'https://example.org/source');
  assert.equal(escapeHtml('<script>"&'), '&lt;script&gt;&quot;&amp;');
});
test('actual committed snapshots load together with browser SHA-256 verification',async()=>{
  const bundle=await loadBundle(localFetch);
  assert.equal(bundle.data.series.length,20);
  assert.equal(bundle.data.health.observation_count,bundle.data.series.reduce((total,series)=>total+series.observations.length,0));
  assert.ok(bundle.analysis.benchmark.pooled.scored_days>0);
  for(const series of bundle.data.series)assert.ok(series.observations.every(row=>row.date<bundle.data.as_of));
});
test('tampered source payload is withheld before display',async()=>{
  const tampered=async url=>{const response=await localFetch(url);if(url.endsWith('/dataset.json')){response.arrayBuffer=async()=>new TextEncoder().encode('{}').buffer;}return response;};
  await assert.rejects(()=>loadBundle(tampered),/integrity check failed/);
});
test('stale analysis/source association is rejected',async()=>{
  const altered=async url=>{const response=await localFetch(url);if(url==='./analysis/current.json'){const original=response.json;response.json=async()=>({...await original(),source_snapshot_id:'0'.repeat(64)});}return response;};
  await assert.rejects(()=>loadBundle(altered),/do not match/);
});
test('invalid snapshot path is rejected before requesting that path',async()=>{
  const altered=async url=>{const response=await localFetch(url);if(url==='./data/current.json'){const original=response.json;response.json=async()=>({...await original(),dataset:'../../private.json'});}return response;};
  await assert.rejects(()=>loadBundle(altered),/Invalid snapshot reference/);
});
test('HTTP errors are visible, not treated as an empty successful dataset',async()=>{
  await assert.rejects(()=>loadBundle(async()=>({ok:false,status:503})),/HTTP 503/);
});
test('download traversal references are rejected even when display data is valid',async()=>{
  const altered=async url=>{const response=await localFetch(url);if(url==='./data/current.json'){const original=response.json;response.json=async()=>({...await original(),csv:'../../private.csv'});}return response;};
  await assert.rejects(()=>loadBundle(altered),/Invalid snapshot reference/);
});
test('analysis download references must belong to the declared analysis version',async()=>{
  const altered=async url=>{const response=await localFetch(url);if(url==='./analysis/current.json'){const original=response.json;response.json=async()=>{const data=await original();data.files['predictions.csv']=`snapshots/${'0'.repeat(64)}/predictions.csv`;return data;};}return response;};
  await assert.rejects(()=>loadBundle(altered),/Invalid snapshot reference/);
});
test('requests have a bounded timeout signal',async()=>{
  let requests=0;
  await loadBundle(async(url,options)=>{assert.ok(options.signal instanceof AbortSignal);requests++;return localFetch(url);});
  assert.equal(requests,4);
});

test('expanded titles and event filters survive a shared URL',()=>{
  const state=parseState('?games=elden-ring,totk,smash,ghost,rdr2&events=totk&kind=trailer&status=occurred&q=launch');
  assert.equal(state.games.length,4);assert.equal(state.events,'totk');
  assert.deepEqual(parseState('?'+stateQuery(state)),state);
});
test('event search intersects title, kind, status and text without mutating source',()=>{
  const events=[{id:'a',series_id:'gta-vi',kind:'trailer',status:'occurred',label:'Trailer 2',verification:'Publisher verified',date:'2025-05-06'},
    {id:'b',series_id:'gta-vi',kind:'release',status:'scheduled',label:'Launch',verification:'Scheduled',date:'2026-11-19'}];
  assert.equal(filterEvents(events,{series:'all',kind:'trailer',status:'occurred',query:'PUBLISHER'}).length,1);
  assert.equal(filterEvents(events,{query:'no matching words'}).length,0);assert.equal(events[0].id,'a');
});
test('publication checkpoint binds data, analysis and title audit together',async()=>{
  const bundle=await loadPublished(localFetch);
  assert.equal(bundle.fallback,false);assert.equal(bundle.audit.series.length,20);
  assert.equal(bundle.publication.data_pointer.snapshot_id,bundle.analysis.source_snapshot_id);
});
test('remote outage selects an explicitly marked verified bundled fallback',async()=>{
  const bundle=await loadPublished((url,opts)=>url.startsWith('https:')?Promise.reject(new Error('offline')):localFetch(url,opts),'https://example.org');
  assert.equal(bundle.fallback,true);assert.equal(bundle.base,'.');assert.match(bundle.remoteError,/offline/);
});
test('corrupt remote data cannot be displayed and falls back as one complete bundle',async()=>{
  const fetcher=async url=>{
    const local=url.replace('https://example.org','.');const response=await localFetch(local);
    if(url.startsWith('https:')&&url.endsWith('/title-audit.json'))response.arrayBuffer=async()=>new TextEncoder().encode('{}').buffer;
    return response;
  };
  const bundle=await loadPublished(fetcher,'https://example.org');
  assert.equal(bundle.fallback,true);assert.match(bundle.remoteError,/integrity/);
});
test('corrupt bundled audit fails closed when no verified fallback exists',async()=>{
  await assert.rejects(()=>loadPublished(async url=>{
    const response=await localFetch(url);if(url.endsWith('/title-audit.json'))response.arrayBuffer=async()=>new TextEncoder().encode('{}').buffer;return response;
  }),/integrity/);
});

test('event investigation selection round trips without losing timeline filters',()=>{
  const state=parseState('?event=gta-vi-trailer-2&events=all&kind=trailer&q=Trailer');
  assert.equal(state.event,'gta-vi-trailer-2');
  assert.deepEqual(parseState('?'+stateQuery(state)),state);
  assert.equal(parseState('?event=%3Cscript%3E').event,'');
  assert.equal(parseState('?event='+'a'.repeat(65)).event,'');
});
test('unknown investigation cannot silently select a different event',async()=>{
  const {analysis}=await loadBundle(localFetch);
  assert.equal(eventInvestigation(analysis,'unknown-event'),null);
});
test('event context contains exactly 29 consecutive calendar dates around day zero',async()=>{
  const {analysis}=await loadBundle(localFetch);
  const view=eventInvestigation(analysis,'gta-vi-trailer-2');
  assert.equal(view.points.length,29);assert.equal(view.points[14].date,view.event.date);
  assert.equal(view.points[0].date,'2025-04-22');assert.equal(view.points.at(-1).date,'2025-05-20');
  assert.equal(view.points[0].relative_day,-14);assert.equal(view.points.at(-1).relative_day,14);
  assert.equal(view.series.id,'gta-vi');
});
test('incomplete event retains its backend exclusion and future calendar nulls',async()=>{
  const {analysis}=await loadBundle(localFetch);
  const view=eventInvestigation(analysis,'gta-vi-preload');
  assert.equal(view.event.analysis_status,'incomplete');assert.equal(view.event.percent_change,null);
  const today=view.points.find(p=>p.date===analysis.as_of);
  assert.equal(today.state,'future');assert.equal(today.views,null);
});
test('scheduled investigation stays scheduled and reports adjacent catalogued events',async()=>{
  const {analysis}=await loadBundle(localFetch);
  const view=eventInvestigation(analysis,'gta-vi-scheduled-release');
  assert.equal(view.event.analysis_status,'scheduled');assert.equal(view.event.percent_change,null);
  assert.ok(view.nearby.some(item=>item.id==='gta-vi-preload'));
  assert.ok(!view.nearby.some(item=>item.id===view.event.id));
});
test('missing and zero observations remain distinguishable inside an event window',()=>{
  const event={id:'event',date:'2024-01-10',series_id:'game'};
  const analysis={as_of:'2024-02-01',events:[event],series:[{id:'game',summary:{observed_start:'2024-01-01',observed_end:'2024-01-31'},daily:[{date:'2024-01-10',views:0,trailing_7_day_mean:0}]}]};
  const view=eventInvestigation(analysis,'event');
  assert.equal(view.points[14].views,0);assert.equal(view.points[14].state,'observed');
  assert.equal(view.points[13].views,null);assert.equal(view.points[13].state,'missing');
  assert.equal(view.points[0].state,'outside_coverage');
});
test('context does not mutate or recalculate the fixed backend event comparison',async()=>{
  const {analysis}=await loadBundle(localFetch);
  const before=JSON.stringify(analysis);
  const view=eventInvestigation(analysis,'gta-vi-launch-trailer');
  assert.equal(view.event.before.expected_days,7);assert.equal(view.event.after.expected_days,7);
  assert.equal(view.event.analysis_status,'available');assert.equal(JSON.stringify(analysis),before);
});
