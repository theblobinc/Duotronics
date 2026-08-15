const $ = (id) => document.getElementById(id);

const state = {
  health: null,
  lastRun: null,
  lastRepoResult: null,
  lastCommitApproval: null,
  lastIntegrationApproval: null,
  chatTurn: 0,
  inferenceHistory: [],
  inferenceMetrics: {
    totalRuns: 0,
    successfulRuns: 0,
    failedRuns: 0,
    totalLatency: 0,
    avgLatency: 0,
  },
  currentAbortController: null,
  inferenceStartTime: null,
};

// Phase 4 & 5: History and Analytics Management
class InferenceHistory {
  static MAX_HISTORY = 50;
  
  static save(run) {
    const history = InferenceHistory.load();
    history.unshift({
      ...run,
      timestamp: new Date().toISOString(),
      id: `run-${Date.now()}`,
    });
    if (history.length > this.MAX_HISTORY) history.pop();
    localStorage.setItem("xavi_inference_history", JSON.stringify(history));
    return history;
  }
  
  static load() {
    try {
      return JSON.parse(localStorage.getItem("xavi_inference_history") || "[]");
    } catch { return []; }
  }
  
  static clear() {
    localStorage.removeItem("xavi_inference_history");
  }
}

class InferenceAnalytics {
  static record(run, latencyMs, success = true) {
    const metrics = InferenceAnalytics.load();
    metrics.totalRuns += 1;
    if (success) metrics.successfulRuns += 1;
    else metrics.failedRuns += 1;
    metrics.totalLatency += latencyMs;
    metrics.avgLatency = metrics.totalLatency / metrics.totalRuns;
    localStorage.setItem("xavi_inference_metrics", JSON.stringify(metrics));
    state.inferenceMetrics = metrics;
    return metrics;
  }
  
  static load() {
    try {
      return JSON.parse(localStorage.getItem("xavi_inference_metrics") || JSON.stringify({
        totalRuns: 0, successfulRuns: 0, failedRuns: 0, totalLatency: 0, avgLatency: 0,
      }));
    } catch { return { totalRuns: 0, successfulRuns: 0, failedRuns: 0, totalLatency: 0, avgLatency: 0 }; }
  }
}

// Phase 3: Settings Presets
const INFERENCE_PRESETS = {
  "default": { model: "", action: "respond", steps: 1, quality: 0.72, auditOnly: true },
  "deep-reasoning": { model: "", action: "observe", steps: 4, quality: 0.85, auditOnly: true },
  "memory-active": { model: "", action: "memory_write", steps: 2, quality: 0.78, auditOnly: false },
  "witness-boost": { model: "", action: "promote_witness", steps: 3, quality: 0.90, auditOnly: false },
  "quick-response": { model: "", action: "respond", steps: 1, quality: 0.60, auditOnly: true },
};

// Phase 1: Error Classification and Categorization
function categorizeError(error) {
  const msg = String(error).toLowerCase();
  if (msg.includes("timeout") || msg.includes("504")) return { kind: "timeout", icon: "⏱", recoverable: true };
  if (msg.includes("502") || msg.includes("provider")) return { kind: "provider", icon: "⚙", recoverable: true };
  if (msg.includes("401") || msg.includes("token")) return { kind: "auth", icon: "🔐", recoverable: false };
  if (msg.includes("404")) return { kind: "notfound", icon: "❓", recoverable: false };
  if (msg.includes("429")) return { kind: "ratelimit", icon: "🚦", recoverable: true };
  return { kind: "unknown", icon: "⚠", recoverable: true };
}

function getKey() {
  return localStorage.getItem("xavi_runtime_api_key") || "";
}

function setStatus(text, kind = "muted") {
  const pill = $("status-pill");
  if (!pill) return;
  pill.textContent = text;
  pill.className = `pill ${kind}`;
}

async function api(path, options = {}, auth = false, retries = 2) {
  const headers = Object.assign({ "content-type": "application/json" }, options.headers || {});
  if (auth) {
    const key = getKey();
    if (key) headers.authorization = `Bearer ${key}`;
  }
  
  let lastError = null;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const fetchOptions = Object.assign({}, options, { headers });
      if (state.currentAbortController) {
        fetchOptions.signal = state.currentAbortController.signal;
      }
      const res = await fetch(path, fetchOptions);
      const text = await res.text();
      let body = null;
      try { body = text ? JSON.parse(text) : null; } catch { body = text; }
      if (!res.ok) {
        const message = typeof body === "object" && body && body.detail ? body.detail : text || res.statusText;
        lastError = new Error(`${res.status} ${message}`);
        if (attempt < retries && res.status >= 500) {
          await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1000));
          continue;
        }
        throw lastError;
      }
      return body;
    } catch (err) {
      if (err.name === "AbortError") throw new Error("Inference cancelled by user");
      lastError = err;
      if (attempt < retries) {
        await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1000));
        continue;
      }
      throw lastError;
    }
  }
  throw lastError || new Error("Request failed");
}

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

function short(value, n = 96) {
  const s = String(value ?? "");
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

function formatResponseOutput(response) {
  if (typeof response !== "string") return pretty(response);
  const lines = response.split("\n").filter(l => l.trim());
  if (lines.length > 50) {
    return lines.slice(0, 40).join("\n") + `\n\n[... ${lines.length - 40} more lines ...]`;
  }
  return response;
}

function formatTime(ms) {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function appendChatMessage(role, text, meta = null, errorKind = null) {
  const log = $("xavi-chat-log");
  if (!log || !text) return;

  const article = document.createElement("article");
  article.className = `chat-message ${role}${errorKind ? " error-message" : ""}`;
  if (errorKind) article.setAttribute("data-error-kind", errorKind);

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  if (errorKind) {
    const errCat = categorizeError(text);
    avatar.textContent = errCat.icon;
    avatar.title = errCat.kind;
  } else {
    avatar.textContent = role === "user" ? "You" : "AI";
  }

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  if (meta) {
    const metaEl = document.createElement("div");
    metaEl.className = "message-meta";
    metaEl.textContent = meta;
    bubble.appendChild(metaEl);
  }

  const body = document.createElement("p");
  body.textContent = text;
  bubble.appendChild(body);
  
  if (errorKind) {
    const errCat = categorizeError(text);
    const hint = document.createElement("small");
    hint.className = "error-hint";
    hint.textContent = `${errCat.kind}${errCat.recoverable ? " (retryable)" : " (requires manual action)"}`;
    bubble.appendChild(hint);
  }
  
  article.append(avatar, bubble);
  log.appendChild(article);
  log.scrollTop = log.scrollHeight;
}

function card(label, value, kind = "") {
  return `<article class="card"><div class="label">${label}</div><div class="value ${kind}">${value}</div></article>`;
}

const XAVI_MODEL_CATEGORIES = [
  { id: "chat", label: "Xavi Models / Chat" },
  { id: "agent", label: "Xavi Models / Agent" },
  { id: "plan", label: "Xavi Models / Plan" },
  { id: "background", label: "Xavi Models / Background" },
  { id: "coding", label: "Xavi Models / Coding" },
  { id: "vision", label: "Xavi Models / Vision" },
  { id: "autocomplete", label: "Xavi Models / Autocomplete" },
  { id: "embedding", label: "Xavi Models / Embeddings" },
  { id: "utility", label: "Xavi Models / Utility & Test" },
];

const XAVI_MODEL_CATEGORY_IDS = new Set(XAVI_MODEL_CATEGORIES.map((category) => category.id));
const XAVI_MODEL_CATEGORY_ALIASES = {
  agent_chat: "agent",
  agentic_editing: "agent",
  tool_augmented_agent: "agent",
  tool_use: "agent",
  planning: "plan",
  repo_reasoning: "plan",
  long_context_planning: "plan",
  architecture: "plan",
  docs: "background",
  readme: "background",
  summaries: "background",
  code: "coding",
  coder: "coding",
  code_review: "coding",
  single_file_edit: "coding",
  small_edit: "coding",
  multi_file_edit: "coding",
  refactor: "coding",
  vision: "vision",
  multimodal: "vision",
  vl: "vision",
  autocomplete: "autocomplete",
  inline_completion: "autocomplete",
  completion: "autocomplete",
  embed: "embedding",
  embedding: "embedding",
  embeddings: "embedding",
  fallback: "utility",
  test: "utility",
  runtime_test: "utility",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function normalizeModelCategory(value) {
  const key = String(value || "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
  return XAVI_MODEL_CATEGORY_ALIASES[key] || (XAVI_MODEL_CATEGORY_IDS.has(key) ? key : "");
}

function modelSearchText(model) {
  const metadata = model.metadata || {};
  return [
    model.name,
    model.model,
    model.provider,
    model.description,
    metadata.xavi_role,
    metadata.hardware_tier,
    ...(metadata.xavi_categories || []),
    ...(metadata.tags || []),
    ...(metadata.recommended_for || []),
  ].filter(Boolean).join(" ").toLowerCase().replace(/[_-]+/g, " ");
}

function getConfiguredModelCategories(model) {
  const metadata = model.metadata || {};
  const values = [
    ...(metadata.xavi_categories || []),
    ...(metadata.tags || []),
    ...(metadata.recommended_for || []),
    metadata.xavi_role,
  ];
  return values.map(normalizeModelCategory).filter(Boolean);
}

function inferModelCategories(model) {
  const text = modelSearchText(model);
  const categories = new Set(getConfiguredModelCategories(model));
  const add = (category) => { if (category) categories.add(category); };

  const isEmbedding = text.includes("embed") || text.includes("nomic embed");
  if (isEmbedding) add("embedding");
  if (/vision|visual|multimodal|qwen2\.5vl|minicpm v|minicpm-v|llava|bakllava|moondream|\bvl\b/.test(text)) add("vision");
  if (/auto ?complete|inline completion/.test(text)) add("autocomplete");
  if (/background|docs|readme|summar/.test(text)) add("background");
  if (/plan|planning|architecture|repo reasoning|long context|deep/.test(text)) add("plan");
  if (/agent|agentic|tool use|tool augmented|copilot|multi file|refactor/.test(text)) add("agent");
  if (/coder|coding|code review|single file|small edit|edit|refactor|vscode|qwen2\.5 coder/.test(text)) add("coding");
  if (/selection explain/.test(text)) { add("chat"); add("coding"); }
  if (!isEmbedding && /chat|small chat|copilot|llama|mistral|gemma|dolphin|phi|qwen2\.5|default/.test(text)) add("chat");
  if (/sandbox|echo|fallback|test/.test(text) || model.provider === "echo") add("utility");
  if (!categories.size) add("chat");

  return XAVI_MODEL_CATEGORIES.map((category) => category.id).filter((id) => categories.has(id));
}

function modelDisplayName(model) {
  const rawCandidate = String(model.model || model.name || "unnamed").replace(/^ollama:/i, "");
  const parts = rawCandidate.split(":");
  const tag = parts.slice(1).join(":");
  let raw = rawCandidate;
  if (tag && /xavi|continue|vscode|agent|plan|background|autocomplete/i.test(tag)) raw = parts[0];
  raw = raw.replace(/^xavi[-_]/i, "").replace(/:latest$/i, "").replace(/[-_]+/g, " ");
  raw = raw.replace(/\bvl\b/gi, "VL").replace(/\bapi\b/gi, "API");
  raw = raw.replace(/\b([a-z])/g, (match) => match.toUpperCase());
  raw = raw.replace(/\b(\d+(?:\.\d+)?)b\b/gi, "$1B");
  return raw.trim() || "Unnamed model";
}

function modelOptionLabel(model) {
  const details = [];
  if (model.provider) details.push(model.provider);
  if (model.metadata?.hardware_tier) details.push(String(model.metadata.hardware_tier).replace(/[_-]+/g, " "));
  if (model.default) details.push("default");
  if (model.discovered) details.push("discovered");
  return [modelDisplayName(model), details.join(", ")].filter(Boolean).join(" - ");
}

function groupedModelEntries(models) {
  const groups = new Map(XAVI_MODEL_CATEGORIES.map((category) => [category.id, []]));
  for (const model of models.filter((item) => item && item.enabled !== false && item.name)) {
    for (const categoryId of inferModelCategories(model)) {
      const bucket = groups.get(categoryId);
      if (bucket && !bucket.some((entry) => entry.name === model.name)) bucket.push(model);
    }
  }
  return XAVI_MODEL_CATEGORIES.map((category) => ({
    ...category,
    models: groups.get(category.id) || [],
  })).filter((category) => category.models.length);
}

function renderModelSelectOptions(models) {
  return `<option value="">default</option>` + groupedModelEntries(models).map((group) => `
    <optgroup label="${escapeHtml(group.label)}">
      ${group.models.map((model) => `<option value="${escapeHtml(model.name)}" title="${escapeHtml(model.name)}">${escapeHtml(modelOptionLabel(model))}</option>`).join("")}
    </optgroup>
  `).join("");
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
  if (modelSelect) {
    const existing = modelSelect.value;
    modelSelect.innerHTML = renderModelSelectOptions(models);
    if (existing) modelSelect.value = existing;
    updateSettingsSummary();
  }
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

function renderRun(result, latencyMs) {
  state.lastRun = result;
  const responseText = formatResponseOutput(result.response_text || pretty(result));
  const modelOutput = $("model-output");
  const policyOutput = $("policy-output");
  
  modelOutput.textContent = responseText;
  modelOutput.classList.add("success-output");
  
  const policyData = {
    requested_action: result.requested_action,
    policy_decision: result.policy_decision,
    non_collapse_gate: result.evidence?.non_collapse_gate,
  };
  policyOutput.textContent = pretty(policyData);
  policyOutput.classList.add("success-output");
  
  if ($("chat-run-output")) $("chat-run-output").textContent = pretty({
    run_id: result.run_id,
    model: result.model,
    requested_action: result.requested_action,
    latency: formatTime(latencyMs),
    witness_contract: result.evidence?.nla_activation_witness_v1 || null,
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

  const turn = state.chatTurn || 1;
  const modelLabel = result.model?.name || result.model?.model || result.model?.provider || "model";
  const latencyLabel = formatTime(latencyMs);
  appendChatMessage("assistant", responseText, `turn ${turn} · ${modelLabel} · ${latencyLabel}`);
}

function updateSettingsSummary(policy = null) {
  const summary = $("settings-summary-text");
  if (!summary) return;

  const model = $("model")?.value || "default";
  const action = $("action")?.value || "respond";
  const steps = $("steps")?.value || "1";
  const quality = $("quality")?.value || "0.72";
  const auditOnly = $("policy-audit-toggle")?.checked ?? Boolean(policy?.audit_only ?? policy?.nla_policy_mode === "audit_only");
  const mode = auditOnly ? "audit-only" : "enforcement";

  summary.textContent = `${mode} · ${action} · ${model} · steps ${steps} · q ${quality}`;
}

function renderPolicyMode(policy) {
  const auditToggle = $("policy-audit-toggle");
  const memoryToggle = $("policy-memory-write-toggle");
  const promoteToggle = $("policy-promote-toggle");
  const label = $("policy-mode-label");
  const detail = $("policy-mode-detail");
  if (!auditToggle || !label || !detail || !policy) return;

  const auditOnly = Boolean(policy.audit_only ?? policy.nla_policy_mode === "audit_only");
  auditToggle.checked = auditOnly;
  if (memoryToggle) {
    memoryToggle.checked = Boolean(policy.allow_memory_write);
    memoryToggle.disabled = auditOnly;
  }
  if (promoteToggle) {
    promoteToggle.checked = Boolean(policy.allow_promote_witness);
    promoteToggle.disabled = auditOnly;
  }

  label.textContent = auditOnly ? "Audit-only" : "Enforcement";
  detail.textContent = auditOnly
    ? "Witnesses are recorded, but they may not influence response, memory, or promotion."
    : "Response influence is enabled. Memory write and witness promotion are separately gated below.";

  updateSettingsSummary(policy);
}

function readPolicySettingsFromModal() {
  const auditOnly = Boolean($("policy-audit-toggle")?.checked);
  return {
    audit_only: auditOnly,
    allow_memory_write: auditOnly ? false : Boolean($("policy-memory-write-toggle")?.checked),
    allow_promote_witness: auditOnly ? false : Boolean($("policy-promote-toggle")?.checked),
  };
}

async function applyInferenceSettingsFromModal() {
  const body = readPolicySettingsFromModal();
  setStatus("applying inference settings", "warn");

  const result = await api("/v1/policy/mode", {
    method: "POST",
    body: JSON.stringify(body),
  }, true);

  renderPolicyMode(result);
  $("policy-output").textContent = pretty(result);
  setStatus(result.audit_only ? "audit-only mode" : "enforcement mode", result.audit_only ? "warn" : "good");
  closeInferenceSettingsModal();
  await refreshAll();
}

function openInferenceSettingsModal() {
  const modal = $("inference-settings-modal");
  if (!modal) return;
  modal.hidden = false;
  document.body.classList.add("modal-open");
  updateSettingsSummary();
  $("close-settings-btn")?.focus();
}

function closeInferenceSettingsModal() {
  const modal = $("inference-settings-modal");
  if (!modal) return;
  modal.hidden = true;
  document.body.classList.remove("modal-open");
  updateSettingsSummary();
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

  if (policy.status === "fulfilled") renderPolicyMode(policy.value);

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
  const promptText = $("prompt").value;
  if (!promptText.trim()) {
    setStatus("please enter a prompt", "warn");
    return;
  }
  
  const body = {
    prompt: promptText,
    requested_action: $("action").value,
    steps: Number($("steps").value || 1),
    evidence_quality: Number($("quality").value || 0.72),
  };
  const modelName = $("model").value;
  if (modelName) body.model_name = modelName;

  state.chatTurn += 1;
  const turn = state.chatTurn;
  state.inferenceStartTime = Date.now();
  state.currentAbortController = new AbortController();

  const runBtn = $("run-btn");
  const modelOutput = $("model-output");
  const policyOutput = $("policy-output");
  
  runBtn.disabled = true;
  appendChatMessage("user", promptText, `turn ${turn} · you`);
  
  // Show progress indicator
  showProgress(true);
  const progressBar = $("inference-progress-bar");
  if (progressBar) progressBar.style.width = "0%";
  
  let originalBtnText = runBtn.textContent;
  runBtn.textContent = "Running…";
  
  try {
    const progressInterval = setInterval(() => {
      if (progressBar && progressBar.style.width !== "100%") {
        const current = parseFloat(progressBar.style.width) || 0;
        progressBar.style.width = Math.min(current + Math.random() * 15, 90) + "%";
      }
    }, 300);
    
    const result = await api("/v1/run", {
      method: "POST",
      body: JSON.stringify(body),
    }, true, 2);
    
    clearInterval(progressInterval);
    if (progressBar) progressBar.style.width = "100%";
    
    const latency = Date.now() - state.inferenceStartTime;
    
    // Save to history and analytics
    InferenceHistory.save({ prompt: promptText, ...body, success: true });
    InferenceAnalytics.record(body, latency, true);
    updateHistoryUI();
    updateAnalyticsUI();
    
    renderRun(result, latency);
    await refreshAll();
    setStatus("inference complete", "good");
  } catch (err) {
    const latency = Date.now() - state.inferenceStartTime;
    const errMsg = String(err);
    const errCat = categorizeError(errMsg);
    
    // Save failed run
    InferenceHistory.save({ prompt: promptText, ...body, success: false, error: errMsg });
    InferenceAnalytics.record(body, latency, false);
    updateHistoryUI();
    updateAnalyticsUI();
    
    modelOutput.textContent = `${errCat.icon} ${errMsg}`;
    modelOutput.classList.add("error-output");
    modelOutput.classList.remove("success-output");
    policyOutput.classList.remove("success-output");
    
    appendChatMessage("assistant", errMsg, `turn ${turn} · error`, errCat.kind);
    setStatus(`inference failed: ${errCat.kind}`, "bad");
    
    if (errCat.recoverable) {
      const retryHint = document.createElement("small");
      retryHint.className = "retry-hint";
      retryHint.innerHTML = ` <a href="#" onclick="runInference(); return false;">Retry</a> or adjust settings and try again.`;
      modelOutput.appendChild(retryHint);
    }
  } finally {
    showProgress(false);
    runBtn.disabled = false;
    runBtn.textContent = originalBtnText;
    state.currentAbortController = null;
  }
}

function cancelInference() {
  if (state.currentAbortController) {
    state.currentAbortController.abort();
    $("run-btn").textContent = "Cancelling…";
    setStatus("cancelling request", "warn");
  }
}

function showProgress(show) {
  const progress = $("inference-progress-container");
  if (progress) progress.style.display = show ? "block" : "none";
}

function updateHistoryUI() {
  const history = InferenceHistory.load();
  const historyList = $("inference-history-list");
  if (!historyList) return;
  
  historyList.innerHTML = history.slice(0, 15).map(run => `
    <div class="history-item" onclick="loadHistoryRun('${run.id}')" title="${run.prompt}">
      <div class="history-prompt">${short(run.prompt, 48)}</div>
      <div class="history-meta">${run.success ? "✓" : "✗"} · ${short(new Date(run.timestamp).toLocaleTimeString(), 12)}</div>
    </div>
  `).join("") || "<div class='history-empty'>No runs yet</div>";
}

function loadHistoryRun(runId) {
  const history = InferenceHistory.load();
  const run = history.find(r => r.id === runId);
  if (!run) return;
  
  $("prompt").value = run.prompt;
  if ($("model") && run.model_name) $("model").value = run.model_name;
  if ($("action")) $("action").value = run.requested_action || "respond";
  if ($("steps")) $("steps").value = run.steps || 1;
  if ($("quality")) $("quality").value = run.evidence_quality || 0.72;
  
  setStatus(`loaded run from ${new Date(run.timestamp).toLocaleTimeString()}`, "warn");
}

function applyPreset(presetName) {
  const preset = INFERENCE_PRESETS[presetName];
  if (!preset) return;
  
  if (preset.model && $("model")) $("model").value = preset.model;
  if ($("action")) $("action").value = preset.action;
  if ($("steps")) $("steps").value = preset.steps;
  if ($("quality")) $("quality").value = preset.quality;
  if ($("policy-audit-toggle")) $("policy-audit-toggle").checked = preset.auditOnly;
  
  updateSettingsSummary();
  setStatus(`loaded preset: ${presetName}`, "good");
}

function updateAnalyticsUI() {
  const metrics = state.inferenceMetrics;
  const analyticsPanel = $("inference-analytics-panel");
  if (!analyticsPanel) return;
  
  const successRate = metrics.totalRuns > 0 ? ((metrics.successfulRuns / metrics.totalRuns) * 100).toFixed(1) : "0";
  analyticsPanel.innerHTML = `
    <div class="analytics-grid">
      <div class="analytics-card">
        <div class="analytics-label">Total runs</div>
        <div class="analytics-value">${metrics.totalRuns}</div>
      </div>
      <div class="analytics-card">
        <div class="analytics-label">Success rate</div>
        <div class="analytics-value">${successRate}%</div>
      </div>
      <div class="analytics-card">
        <div class="analytics-label">Avg latency</div>
        <div class="analytics-value">${formatTime(metrics.avgLatency)}</div>
      </div>
      <div class="analytics-card">
        <div class="analytics-label">Total time</div>
        <div class="analytics-value">${formatTime(metrics.totalLatency)}</div>
      </div>
    </div>
  `;
}


function makePanel(className) {
  const panel = document.createElement("section");
  panel.className = `panel ${className}`;
  return panel;
}

function bindInferenceChatUi() {
  const prompt = $("prompt");
  const runButton = $("run-btn");
  const modelOutput = $("model-output");
  const policyOutput = $("policy-output");

  if (!prompt || !runButton || !modelOutput || !policyOutput || $("xavi-chat-log")) return;

  const inferencePanels = Array.from(document.querySelectorAll('[data-tab-panel="inference"]'));
  if (inferencePanels.length < 2) return;

  const originalControls = inferencePanels[0];
  const originalOutputs = inferencePanels[1];

  const shell = document.createElement("section");
  shell.className = "inference-chat-shell";
  shell.dataset.tabPanel = "inference";

  const sidebar = makePanel("inference-chat-sidebar");
  sidebar.innerHTML = `
    <div>
      <div class="eyebrow">Inference session</div>
      <h2>Local model chat</h2>
      <p>Chat against the active runtime while the witness layer, WG-RNN state, and policy gate stay visible.</p>
    </div>
  `;

  const tokenBox = originalControls.querySelector(".token-box");
  const formStack = originalControls.querySelector(".form-stack");

  if (tokenBox) {
    tokenBox.classList.add("chat-token-box");
    sidebar.appendChild(tokenBox);
  }

  const settingsSummary = document.createElement("div");
  settingsSummary.className = "settings-summary-card";
  settingsSummary.innerHTML = `
    <div class="eyebrow">Inference settings</div>
    <strong id="settings-summary-text">loading settings…</strong>
    <button id="open-settings-btn" type="button">Settings</button>
  `;
  sidebar.appendChild(settingsSummary);

  const settingsModal = document.createElement("section");
  settingsModal.id = "inference-settings-modal";
  settingsModal.className = "settings-modal";
  settingsModal.hidden = true;
  settingsModal.innerHTML = `
    <div class="settings-modal-backdrop" data-close-settings="true"></div>
    <div class="settings-modal-card" role="dialog" aria-modal="true" aria-labelledby="settings-modal-title">
      <div class="settings-modal-head">
        <div>
          <div class="eyebrow">Inference control surface</div>
          <h2 id="settings-modal-title">Runtime settings</h2>
          <p>Test model selection, WG-RNN parameters, and policy behavior without taking space from the chat.</p>
        </div>
        <button id="close-settings-btn" type="button" aria-label="Close settings">Close</button>
      </div>

      <div class="settings-modal-grid">
        <section class="settings-section" id="runtime-model-settings">
          <h3>Model and run</h3>
        </section>

        <section class="settings-section">
          <h3>Policy mode</h3>
          <div class="policy-mode-card">
            <div class="policy-mode-row">
              <div>
                <strong id="policy-mode-label">Audit-only</strong>
                <p id="policy-mode-detail">Witnesses are recorded but may not influence the chat response.</p>
              </div>
              <label class="switch" title="Toggle audit-only mode">
                <input id="policy-audit-toggle" type="checkbox" checked />
                <span></span>
              </label>
            </div>
            <div class="hint">On = observe only. Off = enforce response policy.</div>
          </div>

          <div class="settings-toggle-list">
            <label class="toggle-row">
              <span>
                <strong>Allow memory write</strong>
                <small>Only meaningful when enforcement mode is active.</small>
              </span>
              <label class="switch">
                <input id="policy-memory-write-toggle" type="checkbox" />
                <span></span>
              </label>
            </label>

            <label class="toggle-row">
              <span>
                <strong>Allow witness promotion</strong>
                <small>Only meaningful when enforcement mode is active.</small>
              </span>
              <label class="switch">
                <input id="policy-promote-toggle" type="checkbox" />
                <span></span>
              </label>
            </label>
          </div>
        </section>
      </div>

      <div class="settings-modal-actions">
        <span class="hint">Changes apply to runtime policy immediately. Model/run fields apply on next inference.</span>
        <div>
          <button id="cancel-settings-btn" type="button">Cancel</button>
          <button id="apply-settings-btn" type="button" class="primary">Apply settings</button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(settingsModal);

  if (formStack) {
    $("runtime-model-settings")?.appendChild(formStack);
  }

  $("open-settings-btn")?.addEventListener("click", openInferenceSettingsModal);
  $("close-settings-btn")?.addEventListener("click", closeInferenceSettingsModal);
  $("cancel-settings-btn")?.addEventListener("click", closeInferenceSettingsModal);
  $("apply-settings-btn")?.addEventListener("click", () => {
    applyInferenceSettingsFromModal().catch((err) => {
      setStatus("settings failed", "bad");
      $("policy-output").textContent = String(err);
    });
  });

  settingsModal.addEventListener("click", (event) => {
    if (event.target?.dataset?.closeSettings === "true") closeInferenceSettingsModal();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !settingsModal.hidden) closeInferenceSettingsModal();
  });

  ["model", "action", "steps", "quality", "policy-audit-toggle", "policy-memory-write-toggle", "policy-promote-toggle"]
    .forEach((id) => $(id)?.addEventListener("change", () => {
      const auditOnly = Boolean($("policy-audit-toggle")?.checked);
      if ($("policy-memory-write-toggle")) $("policy-memory-write-toggle").disabled = auditOnly;
      if ($("policy-promote-toggle")) $("policy-promote-toggle").disabled = auditOnly;
      updateSettingsSummary();
    }));

  const quickPrompts = document.createElement("div");
  quickPrompts.className = "quick-prompts";
  quickPrompts.innerHTML = `
    <button type="button" data-prompt="Explain Duotronic non-collapse in one precise paragraph.">Non-collapse</button>
    <button type="button" data-prompt="Summarize the latest runtime witnesses and what they imply.">Witness summary</button>
    <button type="button" data-prompt="Run a careful reasoning pass about whether this runtime should write memory.">Memory policy</button>
  `;
  sidebar.appendChild(quickPrompts);

  const main = makePanel("inference-chat-main");
  main.innerHTML = `
    <div class="inference-chat-head">
      <div>
        <div class="eyebrow">Conversation</div>
        <h2>Xavi Runtime Chat</h2>
      </div>
      <span class="pill muted">evidence-gated</span>
    </div>
    <div id="xavi-chat-log" class="inference-chat-log">
      <article class="chat-message assistant">
        <div class="avatar">X</div>
        <div class="bubble">
          <div class="message-meta">Xavi runtime</div>
          <p>Ask the local runtime anything. The response below is model evidence, while the inspector shows witness contract, policy, and WG-RNN state.</p>
        </div>
      </article>
    </div>
  `;

  modelOutput.classList.add("output", "small", "latest-response-output");
  if (modelOutput.textContent.trim() === "No run yet.") {
    modelOutput.textContent = "No inference run yet. Send a prompt to generate model evidence.";
  }

  const composer = document.createElement("div");
  composer.className = "inference-composer";

  const actions = document.createElement("div");
  actions.className = "composer-actions";

  const hint = document.createElement("span");
  hint.className = "hint";
  hint.textContent = "Runtime output is evidence, not truth. Use Ctrl+Enter to run.";

  actions.append(hint, runButton);
  composer.append(prompt, actions);
  main.appendChild(composer);

  const inspector = makePanel("inference-chat-inspector");
  inspector.innerHTML = `
    <div class="panel-head compact">
      <h2>Inspector</h2>
      <span class="pill muted">live run state</span>
    </div>
    <h3>Policy / non-collapse</h3>
  `;
  inspector.appendChild(policyOutput);

  const latestResponseTitle = document.createElement("h3");
  latestResponseTitle.textContent = "Latest response";
  inspector.append(latestResponseTitle, modelOutput);

  const runFactsTitle = document.createElement("h3");
  runFactsTitle.textContent = "Run facts";

  const runFacts = document.createElement("pre");
  runFacts.id = "chat-run-output";
  runFacts.className = "output small";
  runFacts.textContent = "No run yet.";

  inspector.append(runFactsTitle, runFacts);

  shell.append(sidebar, main, inspector);
  originalControls.replaceWith(shell);
  originalOutputs.remove();

  document.querySelectorAll("[data-prompt]").forEach((btn) => {
    btn.addEventListener("click", () => {
      prompt.value = btn.dataset.prompt || "";
      prompt.focus();
    });
  });

  prompt.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") runInference();
  });
}

function getMcpKey() {
  return localStorage.getItem("xavi_mcp_api_key") || "";
}

async function mcpApi(path, options = {}) {
  const headers = Object.assign({ "content-type": "application/json" }, options.headers || {});
  const key = getMcpKey();
  if (key) headers.authorization = `Bearer ${key}`;

  const res = await fetch(path, Object.assign({}, options, { headers }));
  const text = await res.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = text; }

  if (!res.ok) {
    const detail = typeof body === "object" && body ? body.detail || body.error || body : text || res.statusText;
    throw new Error(`${res.status} ${typeof detail === "string" ? detail : JSON.stringify(detail)}`);
  }

  return body;
}

async function mcpCall(tool, args = {}, requestId = null) {
  return await mcpApi("/xavi-runtime/mcp/call", {
    method: "POST",
    body: JSON.stringify({
      tool,
      args,
      request_id: requestId || `${tool}-${Date.now()}`,
    }),
  });
}

function setRepoOutput(value, diffValue = null) {
  state.lastRepoResult = value;
  const out = $("repo-operator-output");
  if (out) out.textContent = typeof value === "string" ? value : pretty(value);

  if (diffValue !== null) {
    const diffOut = $("repo-diff-output");
    if (diffOut) diffOut.textContent = typeof diffValue === "string" ? diffValue : pretty(diffValue);
  }
}

function repoForm() {
  return {
    worktree_id: $("repo-worktree-id")?.value.trim() || "",
    branch_name: $("repo-branch-name")?.value.trim() || "",
    base_ref: $("repo-base-ref")?.value.trim() || "HEAD",
    target_branch: $("repo-target-branch")?.value.trim() || "main",
    message: $("repo-commit-message")?.value.trim() || "",
    patch: $("repo-patch")?.value || "",
    commit: $("repo-commit-sha")?.value.trim() || "",
    approval_token: $("repo-approval-token")?.value.trim() || "",
    expected_main_head: $("repo-expected-main-head")?.value.trim() || "",
  };
}

function fillRepoField(id, value) {
  const el = $(id);
  if (el && value) el.value = value;
}

async function runRepoAction(label, fn) {
  setStatus(`${label}…`, "warn");
  try {
    const result = await fn();
    setRepoOutput(result);
    setStatus(`${label} ok`, "good");
    return result;
  } catch (err) {
    setRepoOutput(String(err));
    setStatus(`${label} failed`, "bad");
    throw err;
  }
}

async function mcpHealth() {
  return runRepoAction("mcp health", async () => {
    return await mcpApi("/xavi-runtime/mcp/health");
  });
}

async function repoStatus() {
  return runRepoAction("repo status", async () => {
    return await mcpCall("repo.status", {}, "ui-repo-status");
  });
}

async function repoListWorktrees() {
  return runRepoAction("repo worktrees", async () => {
    return await mcpCall("repo.list_worktrees", {}, "ui-repo-worktrees");
  });
}

async function repoCreateWorktree() {
  const f = repoForm();
  return runRepoAction("create worktree", async () => {
    const result = await mcpCall("repo.create_worktree", {
      worktree_id: f.worktree_id || null,
      branch_name: f.branch_name,
      base_ref: f.base_ref,
    }, "ui-create-worktree");

    const payload = result.result || {};
    fillRepoField("repo-worktree-id", payload.worktree_id);
    fillRepoField("repo-branch-name", payload.branch_name);
    return result;
  });
}

async function repoApplyPatch() {
  const f = repoForm();
  return runRepoAction("apply patch", async () => {
    return await mcpCall("repo.apply_patch", {
      worktree_id: f.worktree_id,
      patch: f.patch,
    }, "ui-apply-patch");
  });
}

async function repoDiff() {
  const f = repoForm();
  return runRepoAction("repo diff", async () => {
    const result = await mcpCall("repo.diff", {
      worktree_id: f.worktree_id,
    }, "ui-repo-diff");

    const payload = result.result || {};
    setRepoOutput(result, {
      worktree_id: payload.worktree_id,
      status_short: payload.status_short,
      diff_digest: payload.diff_digest,
      diff: payload.diff,
    });
    return result;
  });
}

async function repoRunTests() {
  const f = repoForm();
  return runRepoAction("run tests", async () => {
    return await mcpCall("repo.run_tests", {
      worktree_id: f.worktree_id,
      test_command: "runtime_pytest",
      timeout_seconds: 300,
    }, "ui-run-tests");
  });
}

async function repoPrepareCommit() {
  const f = repoForm();
  return runRepoAction("prepare commit", async () => {
    const result = await mcpCall("repo.prepare_commit", {
      worktree_id: f.worktree_id,
      message: f.message,
    }, "ui-prepare-commit");

    state.lastCommitApproval = result.result;
    fillRepoField("repo-approval-token", result.result?.approval_token);
    return result;
  });
}

async function repoCommit() {
  const f = repoForm();
  return runRepoAction("commit worktree", async () => {
    const result = await mcpCall("repo.commit", {
      worktree_id: f.worktree_id,
      message: f.message,
      approval_token: f.approval_token,
    }, "ui-commit-worktree");

    fillRepoField("repo-commit-sha", result.result?.commit);
    return result;
  });
}

async function repoPrepareIntegration() {
  const f = repoForm();
  return runRepoAction("prepare integration", async () => {
    const result = await mcpCall("repo.prepare_integration", {
      worktree_id: f.worktree_id,
      message: f.message,
      target_branch: f.target_branch,
    }, "ui-prepare-integration");

    state.lastIntegrationApproval = result.result;
    fillRepoField("repo-approval-token", result.result?.approval_token);
    fillRepoField("repo-commit-sha", result.result?.commit);
    fillRepoField("repo-expected-main-head", result.result?.expected_main_head);
    return result;
  });
}

async function repoIntegrateCommit() {
  const f = repoForm();
  return runRepoAction("integrate commit", async () => {
    return await mcpCall("repo.integrate_commit", {
      worktree_id: f.worktree_id,
      commit: f.commit,
      message: f.message,
      approval_token: f.approval_token,
      target_branch: f.target_branch,
      expected_main_head: f.expected_main_head,
    }, "ui-integrate-commit");
  });
}

async function repoRemoveWorktree() {
  const f = repoForm();
  return runRepoAction("remove worktree", async () => {
    return await mcpCall("repo.remove_worktree", {
      worktree_id: f.worktree_id,
      force: true,
    }, "ui-remove-worktree");
  });
}

function bindRepoOperatorUi() {
  if (!$("mcp-key")) return;

  $("mcp-key").value = getMcpKey();

  $("save-mcp-key-btn").addEventListener("click", () => {
    localStorage.setItem("xavi_mcp_api_key", $("mcp-key").value.trim());
    setStatus("mcp key saved", "good");
  });

  $("mcp-health-btn").addEventListener("click", mcpHealth);
  $("repo-status-btn").addEventListener("click", repoStatus);
  $("repo-worktrees-btn").addEventListener("click", repoListWorktrees);
  $("repo-create-worktree-btn").addEventListener("click", repoCreateWorktree);
  $("repo-apply-patch-btn").addEventListener("click", repoApplyPatch);
  $("repo-diff-btn").addEventListener("click", repoDiff);
  $("repo-run-tests-btn").addEventListener("click", repoRunTests);
  $("repo-prepare-commit-btn").addEventListener("click", repoPrepareCommit);
  $("repo-commit-btn").addEventListener("click", repoCommit);
  $("repo-prepare-integration-btn").addEventListener("click", repoPrepareIntegration);
  $("repo-integrate-btn").addEventListener("click", repoIntegrateCommit);
  $("repo-remove-worktree-btn").addEventListener("click", repoRemoveWorktree);
}



function setOpsOutput(value) {
  const out = $("ops-output");
  if (out) out.textContent = typeof value === "string" ? value : pretty(value);
}

async function runOpsAction(label, tool, args = {}) {
  setStatus(`${label}…`, "warn");
  try {
    const result = await mcpCall(tool, args, `ui-${tool}-${Date.now()}`);
    setOpsOutput(result);
    setStatus(`${label} ok`, "good");
    return result;
  } catch (err) {
    setOpsOutput(String(err));
    setStatus(`${label} failed`, "bad");
    throw err;
  }
}

function bindOpsUi() {
  if (!$("ops-output")) return;

  $("ops-health-btn")?.addEventListener("click", () => runOpsAction("runtime health", "ops.runtime_health"));
  $("ops-ps-btn")?.addEventListener("click", () => runOpsAction("podman ps", "ops.runtime_ps"));
  $("ops-tests-btn")?.addEventListener("click", () => runOpsAction("runtime tests", "ops.runtime_tests"));
  $("ops-git-status-btn")?.addEventListener("click", () => runOpsAction("git status", "ops.git_status"));
  $("ops-git-pull-btn")?.addEventListener("click", () => runOpsAction("git pull", "ops.git_pull"));

  $("ops-logs-btn")?.addEventListener("click", () => {
    const tail = Math.max(20, Math.min(Number($("ops-log-tail")?.value || 160), 1000));
    return runOpsAction("runtime logs", "ops.runtime_logs", { tail });
  });

  $("ops-allowed-command-btn")?.addEventListener("click", () => {
    const name = $("ops-allowed-command")?.value || "runtime_pytest";
    return runOpsAction("allowed command", "ops.allowed_command", { name });
  });
}


function showTab(tabName) {
  document.querySelectorAll("[data-tab-target]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tabTarget === tabName);
  });

  document.querySelectorAll("[data-tab-panel]").forEach((panel) => {
    panel.classList.toggle("active-tab-panel", panel.dataset.tabPanel === tabName);
  });

  localStorage.setItem("xavi_runtime_active_tab", tabName);
}

function bindDashboardTabs() {
  const buttons = Array.from(document.querySelectorAll("[data-tab-target]"));
  if (!buttons.length) return;

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => showTab(btn.dataset.tabTarget));
  });

  const preferred = localStorage.getItem("xavi_runtime_active_tab") || "overview";
  const valid = buttons.some((btn) => btn.dataset.tabTarget === preferred);
  showTab(valid ? preferred : "overview");
}

function safeBind(label, fn) {
  try {
    fn();
  } catch (err) {
    console.error(`failed to bind ${label}`, err);
    setStatus(`${label} failed`, "warn");
  }
}

function boot() {
  safeBind("tabs", bindDashboardTabs);

  safeBind("runtime key", () => {
    const apiKey = $("api-key");
    const saveKey = $("save-key-btn");
    if (!apiKey || !saveKey) return;
    apiKey.value = getKey();
    saveKey.addEventListener("click", () => {
      localStorage.setItem("xavi_runtime_api_key", apiKey.value.trim());
      setStatus("key saved", "good");
    });
  });

  safeBind("refresh button", () => {
    $("refresh-btn")?.addEventListener("click", refreshAll);
  });

  safeBind("inference", () => {
    $("run-btn")?.addEventListener("click", runInference);
    bindInferenceChatUi();
  });

  safeBind("repo operator", bindRepoOperatorUi);
  safeBind("ops", bindOpsUi);

  document.querySelectorAll("[data-reload]").forEach((btn) => btn.addEventListener("click", refreshAll));

  refreshAll().catch((err) => {
    console.error("initial refresh failed", err);
    setStatus("refresh failed", "warn");
  });

  setInterval(() => {
    refreshAll().catch((err) => console.error("scheduled refresh failed", err));
  }, 15000);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}


/* Robust settings-modal fallback binding. Keeps working even if earlier binding order changes. */
function forceOpenInferenceSettingsModal() {
  const modal = document.getElementById("inference-settings-modal");
  if (!modal) {
    console.warn("inference settings modal not found");
    setStatus("settings modal missing", "warn");
    return;
  }

  modal.hidden = false;
  modal.removeAttribute("hidden");
  modal.style.display = "grid";
  modal.style.position = "fixed";
  modal.style.inset = "0";
  modal.style.zIndex = "2147483000";
  modal.style.pointerEvents = "auto";

  const card = modal.querySelector(".settings-modal-card");
  if (card) {
    card.style.zIndex = "2147483001";
    card.style.position = "relative";
  }

  document.body.classList.add("modal-open");
  updateSettingsSummary?.();
}

function forceCloseInferenceSettingsModal() {
  const modal = document.getElementById("inference-settings-modal");
  if (!modal) return;
  modal.hidden = true;
  modal.style.display = "none";
  document.body.classList.remove("modal-open");
  updateSettingsSummary?.();
}

window.openInferenceSettingsModal = forceOpenInferenceSettingsModal;
window.closeInferenceSettingsModal = forceCloseInferenceSettingsModal;

document.addEventListener("click", (event) => {
  const openBtn = event.target.closest?.("#open-settings-btn, [data-open-settings]");
  if (openBtn) {
    event.preventDefault();
    forceOpenInferenceSettingsModal();
    return;
  }

  const closeBtn = event.target.closest?.("#close-settings-btn, #cancel-settings-btn, [data-close-settings]");
  if (closeBtn) {
    event.preventDefault();
    forceCloseInferenceSettingsModal();
  }
}, true);

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") forceCloseInferenceSettingsModal();
}, true);

// Phase 4 & 5: Initialize history and analytics on page load
document.addEventListener("DOMContentLoaded", () => {
  // Load metrics for analytics display
  const metrics = InferenceAnalytics.load();
  state.inferenceMetrics = metrics;
  updateAnalyticsUI();
  
  // Initialize history UI
  updateHistoryUI();
  
  // Restore any saved run button click listeners
  const runBtn = $("run-btn");
  if (runBtn) {
    runBtn.addEventListener("click", runInference);
  }
  
  // Initialize prompt shortcuts (Ctrl+Enter or Cmd+Enter to run)
  const prompt = $("prompt");
  if (prompt) {
    prompt.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        runInference();
      }
    });
  }
});
