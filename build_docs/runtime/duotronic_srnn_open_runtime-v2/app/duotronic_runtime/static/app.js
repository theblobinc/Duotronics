async function getJson(url, options) {
  const r = await fetch(url, options);
  return await r.json();
}
function pretty(x) { return JSON.stringify(x, null, 2); }
async function refresh() {
  document.getElementById('health').textContent = pretty(await getJson('/health'));
  document.getElementById('witnesses').textContent = pretty(await getJson('/v1/witnesses?limit=5'));
  document.getElementById('memory').textContent = pretty(await getJson('/v1/memory?limit=5'));
}
document.getElementById('refresh').onclick = refresh;
document.getElementById('run').onclick = async () => {
  const body = { prompt: document.getElementById('prompt').value, requested_action: document.getElementById('action').value, steps: 3 };
  const data = await getJson('/v1/run', { method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify(body) });
  document.getElementById('result').textContent = pretty(data);
  await refresh();
};
refresh();
