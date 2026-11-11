export const IDS = ["gta-vi", "gta-v-2022", "rdr2", "cyberpunk", "elden-ring", "ghost", "odyssey", "botw", "totk", "animal-crossing", "smash", "splatoon-3", "luigi-3", "horizon-zero", "horizon-west", "god-of-war", "ragnarok", "spider-man", "last-of-us-2", "death-stranding"];
export const DEFAULT_IDS = IDS.slice(0,4);
export const COLORS = ['#f6b8ca', '#ead09a', '#99d4c7', '#b7acf2'];
export const DASHES = ['', '9 5', '3 5', '12 4 2 4'];
export const DAY = 86400000;
export const number = (value, digits = 0) => value == null ? 'Unavailable' : new Intl.NumberFormat('en-US', {maximumFractionDigits:digits, minimumFractionDigits:digits}).format(value);
export const percent = value => value == null ? 'Unavailable' : `${value > 0 ? '+' : ''}${number(value, 1)}%`;
export const dateLabel = value => new Date(`${value}T00:00:00Z`).toLocaleDateString('en-GB', {day:'numeric', month:'short', year:'numeric', timeZone:'UTC'});
export const compact = value => Math.abs(value) >= 1e6 ? `${number(value / 1e6, 1)}m` : Math.abs(value) >= 1000 ? `${number(value / 1000, value >= 10000 ? 0 : 1)}k` : number(value);
export const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));

export function parseState(search) {
  const params = new URLSearchParams(search);
  const allowed = (key, values, fallback) => values.includes(params.get(key)) ? params.get(key) : fallback;
  const parsed = (params.get('games') || '').split(',').filter(id => IDS.includes(id));
  return {range:allowed('range', ['30','90','365','all'], '90'), metric:allowed('metric', ['views','mean','both'], 'both'),
    mode:allowed('mode', ['raw','index'], 'index'), originals:params.get('originals') === '1',
    events:allowed('events', [...IDS,'all'], 'gta-vi'),
    event:/^[a-z][a-z0-9-]{0,63}$/.test(params.get('event')||'') ? params.get('event') : '',
    kind:allowed('kind',['all','trailer','announcement','release','rerelease'],'all'), status:allowed('status',['all','occurred','scheduled'],'all'), query:(params.get('q')||'').slice(0,200),
    games:params.get('games') === 'none' ? [] : parsed.length ? [...new Set(parsed)].slice(0,4) : [...DEFAULT_IDS]};
}
export function stateQuery(state) {
  const params = new URLSearchParams();
  for (const key of ['range','metric','mode','events','kind','status']) params.set(key, state[key]);
  if(state.query)params.set('q',state.query);
  if(state.event)params.set('event',state.event);
  params.set('games', state.games.length ? state.games.join(',') : 'none');
  if (state.originals) params.set('originals','1');
  return params.toString();
}
export function selectedDates(series, range) {
  if (range === 'all') return series.daily;
  const last = Date.parse(series.summary.observed_end + 'T00:00:00Z');
  const cutoff = last - (Number(range) - 1) * DAY;
  return series.daily.filter(row => Date.parse(row.date + 'T00:00:00Z') >= cutoff);
}
export function selectedGames(series, state) {
  return series.filter(game => state.games.includes(game.id) && (!state.originals || game.release_kind === 'original_launch'));
}
export function comparisonAvailability(games, mode) {
  const available = games.filter(game => mode === 'raw' || game.comparison.baseline.status === 'available');
  return {available, unavailable:games.filter(game => !available.includes(game))};
}
export function segments(points, xValue, yValue, xScale, yScale) {
  let path = '', drawing = false;
  for (const point of points) {
    const x = xValue(point), y = yValue(point);
    if (y == null || !Number.isFinite(y) || !Number.isFinite(x)) {drawing=false;continue;}
    path += `${drawing ? 'L' : 'M'}${xScale(x).toFixed(2)},${yScale(y).toFixed(2)} `;
    drawing = true;
  }
  return path.trim();
}
export function safeEvidence(url) {
  try {const value=new URL(url);return value.protocol === 'https:' && !value.username && !value.password ? value.href : '#method';}
  catch {return '#method';}
}
export function validateBundle(data, analysis, dataPointer, analysisPointer) {
  const id = dataPointer.snapshot_id;
  if (data.schema_version !== 1 || analysis.schema_version !== 1 || data.manifest_sha256 !== id || analysis.source_snapshot_id !== id || analysisPointer.source_snapshot_id !== id || analysis.analysis_manifest.source_snapshot_id !== id || data.as_of !== analysis.as_of) throw new Error('Source and analysis snapshots do not match. Rebuild the analysis before displaying this data.');
  for (const id of IDS) if (!data.series.some(s=>s.id===id) || !analysis.series.some(s=>s.id===id)) throw new Error('A required series is missing from this snapshot.');
}
export function validatePointers(data, analysis) {
  const hash=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
  if(data?.schema_version!==1||analysis?.schema_version!==1||!hash(data.snapshot_id)||!hash(analysis.analysis_id)||!hash(analysis.source_snapshot_id))throw new Error('Invalid snapshot reference.');
  const check=(path,digest,id,name)=>{
    if(path!==`snapshots/${id}/${name}`||!hash(digest))throw new Error('Invalid snapshot reference.');
  };
  for(const [key,name] of Object.entries({dataset:'dataset.json',csv:'views.csv',health:'health.json',manifest:'manifest.json'}))check(data[key],data.files_sha256?.[name],data.snapshot_id,name);
  for(const name of ['analysis.json','comparisons.csv','predictions.csv','findings.md','manifest.json','protocol.md'])check(analysis.files?.[name],analysis.files_sha256?.[name],analysis.analysis_id,name);
  if(data.snapshot_id!==analysis.source_snapshot_id)throw new Error('Source and analysis snapshots do not match. Rebuild the analysis before displaying this data.');
}
export async function loadBundle(fetcher = fetch) {
  const request=(url,cache)=>fetcher(url,{cache,signal:AbortSignal.timeout(15000)});
  async function json(url) {const response = await request(url,'no-store');if (!response.ok) throw new Error(`Snapshot request failed (HTTP ${response.status}).`);return response.json();}
  const [dataPointer, analysisPointer] = await Promise.all([json('./data/current.json'),json('./analysis/current.json')]);
  validatePointers(dataPointer,analysisPointer);
  async function verified(base, relative, hash) {
    if (!/^snapshots\/[a-f0-9]{64}\/[a-z.-]+$/.test(relative) || !/^[a-f0-9]{64}$/.test(hash)) throw new Error('Invalid snapshot reference.');
    const response = await request(`${base}/${relative}`,'no-cache');
    if (!response.ok) throw new Error(`Snapshot request failed (HTTP ${response.status}).`);
    const bytes = await response.arrayBuffer();
    const actual = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
    if (actual !== hash) throw new Error('Snapshot integrity check failed. The displayed data has been withheld.');
    return JSON.parse(new TextDecoder().decode(bytes));
  }
  const [data, analysis] = await Promise.all([
    verified('./data', dataPointer.dataset, dataPointer.files_sha256['dataset.json']),
    verified('./analysis', analysisPointer.files['analysis.json'], analysisPointer.files_sha256['analysis.json'])]);
  validateBundle(data, analysis, dataPointer, analysisPointer);
  return {data,analysis,dataPointer,analysisPointer};
}

export function filterEvents(events, {series='gta-vi',kind='all',status='all',query=''}) {
  const search=query.trim().toLocaleLowerCase('en-US');
  return events.filter(event=>(series==='all'||event.series_id===series)&&
    (kind==='all'||event.kind===kind)&&(status==='all'||event.status===status)&&
    (!search||`${event.label} ${event.verification} ${event.date}`.toLocaleLowerCase('en-US').includes(search)))
    .sort((a,b)=>b.date.localeCompare(a.date)||a.id.localeCompare(b.id));
}

// The chart adds context without changing the fixed backend effect windows.
// Always use calendar dates: missing/future observations stay null.
export function eventInvestigation(analysis, eventId) {
  const event=analysis.events.find(item=>item.id===eventId);
  if(!event)return null;
  const series=analysis.series.find(item=>item.id===event.series_id);
  if(!series)return null;
  const observations=new Map(series.daily.map(row=>[row.date,row]));
  const stamp=Date.parse(event.date+'T00:00:00Z');
  const points=Array.from({length:29},(_,index)=>{
    const relative_day=index-14,date=new Date(stamp+relative_day*DAY).toISOString().slice(0,10);
    const row=observations.get(date);
    const status=date>=analysis.as_of?'future':row?'observed':date<series.summary.observed_start||date>series.summary.observed_end?'outside_coverage':'missing';
    return {date,relative_day,state:status,views:status==='observed'?row.views:null,
      trailing_7_day_mean:status==='observed'?row.trailing_7_day_mean:null};
  });
  const nearby=analysis.events.filter(item=>item.series_id===series.id&&item.id!==event.id&&item.date>=points[0].date&&item.date<=points.at(-1).date)
    .sort((a,b)=>a.date.localeCompare(b.date)||a.id.localeCompare(b.id));
  return {event,series,points,nearby};
}

export async function loadPublished(fetcher=fetch, remote='') {
  async function load(base) {
    const options={cache:'no-store',signal:AbortSignal.timeout(15000)};
    const response=await fetcher(`${base}/publication.json`,options);
    if(!response.ok)throw new Error('Publication checkpoint unavailable.');
    const publication=await response.json();
    if(publication.schema_version!==1||!Array.isArray(publication.history)||!publication.history.length)throw new Error('Invalid publication checkpoint.');
    validatePointers(publication.data_pointer,publication.analysis_pointer);
    const bundle=await loadBundle((url,opts)=>{
      if(url==='./data/current.json')return Promise.resolve({ok:true,json:async()=>publication.data_pointer});
      if(url==='./analysis/current.json')return Promise.resolve({ok:true,json:async()=>publication.analysis_pointer});
      return fetcher(base+url.slice(1),opts);
    });
    const auditResponse=await fetcher(`${base}/title-audit.json`,options);
    if(!auditResponse.ok)throw new Error('Title audit unavailable.');
    const bytes=await auditResponse.arrayBuffer();
    const hash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
    if(hash!==publication.title_audit_sha256)throw new Error('Title audit integrity check failed.');
    const audit=JSON.parse(new TextDecoder().decode(bytes));
    if(audit.series.length!==bundle.data.series.length||!bundle.data.series.every(s=>audit.series.some(item=>item.series_id===s.id&&item.configured_article===s.article)))throw new Error('Title audit and data cohort differ.');
    return {...bundle,publication,audit,base};
  }
  if(remote){try{return {...await load(remote),fallback:false};}catch(error){return {...await load('.'),fallback:true,remoteError:error.message};}}
  return {...await load('.'),fallback:false};
}
