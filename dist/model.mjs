export const IDS = ['gta-vi', 'gta-v-2022', 'rdr2', 'cyberpunk'];
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
    events:allowed('events', ['gta-vi','all'], 'gta-vi'),
    games:params.get('games') === 'none' ? [] : parsed.length ? [...new Set(parsed)] : [...IDS]};
}
export function stateQuery(state) {
  const params = new URLSearchParams();
  for (const key of ['range','metric','mode','events']) params.set(key, state[key]);
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
export async function loadBundle(fetcher = fetch) {
  async function json(url) {const response = await fetcher(url, {cache:'no-store'});if (!response.ok) throw new Error(`Snapshot request failed (HTTP ${response.status}).`);return response.json();}
  const [dataPointer, analysisPointer] = await Promise.all([json('./data/current.json'),json('./analysis/current.json')]);
  async function verified(base, relative, hash) {
    if (!/^snapshots\/[a-f0-9]{64}\/[a-z.-]+$/.test(relative) || !/^[a-f0-9]{64}$/.test(hash)) throw new Error('Invalid snapshot reference.');
    const response = await fetcher(`${base}/${relative}`, {cache:'no-cache'});
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
