import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {parseState,stateQuery,selectedDates,selectedGames,comparisonAvailability,segments,safeEvidence,escapeHtml,loadBundle} from '../dist/model.mjs';

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
  assert.equal(bundle.data.series.length,4);
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
