const $ = (id) => document.getElementById(id);

const state = {
  health: null,
  lastRun: null,
};

function getKey() {
  return localStorage.getItem("xavi_runtime_api_key") || "";
}

function setStatus(text, kind = "muted") {
  const pill = $("status-pill");
  pill.textContent = text;
  pill.className = `pill ${kind}`;
}

async function api(path, options = {}, auth = false) {
  const headers = Object.assign({ "content-type": "application/json" }, options.headers || {});
  if (auth) {
    const key = getKey();
    if (key) headers.authorization = `Bearer ${key}`;
  }
  const res = await fetch(path, Object.assign({}, options, { headers }));
  const text = await res.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = text; }
  if (!res.ok) {
    const message = typeof body === "object" && body && body.detail ? body.detail : text || res.statusText;
    throw new Error(`${res.status} ${message}`);
  }
  return body;
}

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function short(value, n = 96) {
  const s = String(value ?? "");
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

function card(label, value, kind = "") {
  return `<article class="card"><div class="label">${label}</div><div class="value ${kind}">${value}</div></article>`;
}

function renderHealth(health) {
  state.health = health;
  const models = health.models || [];
  const defaultModel = models.find((m) => m.default) || models.find((m) => m.enabled) || {};
  $("health-cards").innerHTML = [
    card("Runtime", `${health.status || "unknown"} / ${health.runtime_mode || "unknown"}`),
    card("Node", health.node_id || "unknown"),
    card("Default model", `${defaultModel.name || "none"} ${defaultModel.provider ? `(${defaultModel.provider})` : ""}`),
    card("Corpus", short(`${health.corpus?.version || "unknown"} ${health.corpus?.digest || ""}`, 72)),
  ].join("");

  setStatus(health.status === "ok" ? "online" : "degraded", health.status === "ok" ? "good" : "warn");

  const modelSelect = $("model");
  const existing = modelSelect.value;
  modelSelect.innerHTML = `<option value="">default</option>` + models
    .filter((m) => m.enabled)
    .map((m) => `<option value="${m.name}">${m.name} · ${m.provider}${m.default ? " · default" : ""}</option>`)
    .join("");
  if (existing) modelSelect.value = existing;
}

function renderModels(data) {
  const items = data.items || state.health?.models || [];
  $("models-list").innerHTML = items.map((m) => `
    <div class="item">
      <strong>${m.name || "unnamed"} ${m.default ? "· default" : ""}</strong>
      <span>${m.provider || "unknown"} · enabled=${m.enabled !== false} · ${m.model || m.description || ""}</span>
    </div>
  `).join("") || `<div class="item"><span>No models.</span></div>`;
}

function renderModules(data) {
  const items = data.modules || [];
  $("modules-list").innerHTML = items.map((m) => `
    <div class="item">
      <strong>${m.id} ${m.enabled ? "· enabled" : "· disabled"}</strong>
      <span>${m.kind} · ${m.profile} · ${(m.capabilities || []).join(", ")}</span>
    </div>
  `).join("") || `<div class="item"><span>No modules.</span></div>`;
}

function drawVector(canvas, vectors) {
  const ctx = canvas.getContext("2d");
  const w = canvas.width = canvas.clientWidth * devicePixelRatio;
  const h = canvas.height = 260 * devicePixelRatio;
  ctx.clearRect(0, 0, w, h);

  ctx.fillStyle = "#050912";
  ctx.fillRect(0, 0, w, h);

  const rows = vectors.filter((r) => Array.isArray(r.values) && r.values.length);
  if (!rows.length) {
    ctx.fillStyle = "#8fa0b7";
    ctx.font = `${14 * devicePixelRatio}px sans-serif`;
    ctx.fillText("No runtime vector available yet.", 20 * devicePixelRatio, 45 * devicePixelRatio);
    return;
  }

  const pad = 18 * devicePixelRatio;
  const rowHeight = (h - pad * 2) / rows.length;
  const maxAbs = Math.max(...rows.flatMap((r) => r.values.map((v) => Math.abs(Number(v) || 0))), 0.0001);

  rows.forEach((row, rowIndex) => {
    const values = row.values;
    const cellW = (w - pad * 2) / values.length;
    const y = pad + rowIndex * rowHeight;

    ctx.fillStyle = "#8fa0b7";
    ctx.font = `${12 * devicePixelRatio}px sans-serif`;
    ctx.fillText(row.label, pad, y + 15 * devicePixelRatio);

    values.forEach((value, i) => {
      const magnitude = Math.min(1, Math.abs(Number(value) || 0) / maxAbs);
      const hue = value >= 0 ? 216 : 344;
      ctx.fillStyle = `hsl(${hue} 90% ${22 + magnitude * 55}%)`;
      ctx.fillRect(
        pad + i * cellW,
        y + 24 * devicePixelRatio,
        Math.max(1, cellW - 1 * devicePixelRatio),
        Math.max(3, (rowHeight - 42 * devicePixelRatio) * magnitude)
      );
    });
  });
}

function renderRun(result) {
  state.lastRun = result;
  $("model-output").textContent = result.response_text || pretty(result);
  $("policy-output").textContent = pretty({
    requested_action: result.requested_action,
    policy_decision: result.policy_decision,
    non_collapse_gate: result.evidence?.non_collapse_gate,
  });
  $("witness-output").textContent = pretty({
    run_id: result.run_id,
    model: result.model,
    nla_witness: result.nla_witness,
    model_output_witness: result.evidence?.model_output_witness,
  });

  const snapshot = result.wg_rnn?.snapshot || result.memory?.runtime_snapshot || {};
  drawVector($("memory-canvas"), [
    { label: "h", values: snapshot.h || result.wg_rnn?.activation_vector || [] },
    { label: "c", values: snapshot.c || [] },
  ]);
}

async function refreshAll() {
  setStatus("refreshing", "warn");
  const [health, models, modules, memory, witnesses, evidenceWitnesses, claims, audit, corpus, policy, formal] =
    await Promise.allSettled([
      api("/health"),
      api("/v1/models"),
      api("/v1/modules"),
      api("/v1/memory?limit=8"),
      api("/v1/witnesses?limit=8"),
      api("/v1/evidence/witnesses?limit=8"),
      api("/v1/evidence/claims?limit=8"),
      api("/v1/audit?limit=8"),
      api("/v1/corpus/inspect"),
      api("/v1/policy/explain"),
      api("/v1/formal/status"),
    ]);

  if (health.status === "fulfilled") renderHealth(health.value);
  else setStatus("offline", "bad");

  if (models.status === "fulfilled") renderModels(models.value);
  if (modules.status === "fulfilled") renderModules(modules.value);

  $("memory-output").textContent = memory.status === "fulfilled" ? pretty(memory.value) : String(memory.reason);
  $("witnesses-output").textContent = pretty({
    witnesses: witnesses.status === "fulfilled" ? witnesses.value : String(witnesses.reason),
    evidence_witnesses: evidenceWitnesses.status === "fulfilled" ? evidenceWitnesses.value : String(evidenceWitnesses.reason),
  });
  $("audit-output").textContent = pretty({
    claims: claims.status === "fulfilled" ? claims.value : String(claims.reason),
    audit: audit.status === "fulfilled" ? audit.value : String(audit.reason),
  });
  $("corpus-output").textContent = corpus.status === "fulfilled" ? pretty(corpus.value) : String(corpus.reason);
  $("system-output").textContent = pretty({
    policy: policy.status === "fulfilled" ? policy.value : String(policy.reason),
    formal: formal.status === "fulfilled" ? formal.value : String(formal.reason),
  });

  if (!state.lastRun && memory.status === "fulfilled") {
    const latest = (memory.value.items || [])[0];
    const snapshot = latest?.runtime_snapshot || latest?.payload?.runtime_snapshot;
    if (snapshot) drawVector($("memory-canvas"), [
      { label: "h", values: snapshot.h || [] },
      { label: "c", values: snapshot.c || [] },
    ]);
  }
}

async function runInference() {
  const body = {
    prompt: $("prompt").value,
    requested_action: $("action").value,
    steps: Number($("steps").value || 1),
    evidence_quality: Number($("quality").value || 0.72),
  };
  const modelName = $("model").value;
  if (modelName) body.model_name = modelName;

  $("run-btn").disabled = true;
  $("run-btn").textContent = "Running…";
  try {
    const result = await api("/v1/run", {
      method: "POST",
      body: JSON.stringify(body),
    }, true);
    renderRun(result);
    await refreshAll();
  } catch (err) {
    $("model-output").textContent = String(err);
    setStatus("run failed", "bad");
  } finally {
    $("run-btn").disabled = false;
    $("run-btn").textContent = "Run inference";
  }
}

function boot() {
  $("api-key").value = getKey();
  $("save-key-btn").addEventListener("click", () => {
    localStorage.setItem("xavi_runtime_api_key", $("api-key").value.trim());
    setStatus("key saved", "good");
  });
  $("refresh-btn").addEventListener("click", refreshAll);
  $("run-btn").addEventListener("click", runInference);
  document.querySelectorAll("[data-reload]").forEach((btn) => btn.addEventListener("click", refreshAll));
  refreshAll();
  setInterval(refreshAll, 15000);
}

boot();
