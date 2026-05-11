const $ = (id) => document.getElementById(id);

const state = {
  health: null,
  lastRun: null,
  lastRepoResult: null,
  lastCommitApproval: null,
  lastIntegrationApproval: null,
  chatTurn: 0,
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

function appendChatMessage(role, text, meta = null) {
  const log = $("xavi-chat-log");
  if (!log || !text) return;

  const article = document.createElement("article");
  article.className = `chat-message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "You" : "AI";

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
  article.append(avatar, bubble);
  log.appendChild(article);
  log.scrollTop = log.scrollHeight;
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
  if ($("chat-run-output")) $("chat-run-output").textContent = pretty({
    run_id: result.run_id,
    model: result.model,
    requested_action: result.requested_action,
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

  state.chatTurn += 1;
  appendChatMessage("assistant", result.response_text || "No response text returned.", `runtime response ${state.chatTurn}`);
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
  const promptText = $("prompt").value;
  const body = {
    prompt: promptText,
    requested_action: $("action").value,
    steps: Number($("steps").value || 1),
    evidence_quality: Number($("quality").value || 0.72),
  };
  const modelName = $("model").value;
  if (modelName) body.model_name = modelName;

  $("run-btn").disabled = true;
  appendChatMessage("user", promptText, "you");
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

  if (formStack) sidebar.appendChild(formStack);

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
          <p>Ask the local runtime anything. Responses flow through the active model provider, WG-RNN state, witness generation, and policy gate.</p>
        </div>
      </article>
    </div>
  `;

  const latest = document.createElement("article");
  latest.className = "chat-message assistant latest-output";

  const aiAvatar = document.createElement("div");
  aiAvatar.className = "avatar";
  aiAvatar.textContent = "AI";

  modelOutput.classList.add("bubble", "chat-output");
  latest.append(aiAvatar, modelOutput);
  main.querySelector("#xavi-chat-log").appendChild(latest);

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

function boot() {
  $("api-key").value = getKey();
  $("save-key-btn").addEventListener("click", () => {
    localStorage.setItem("xavi_runtime_api_key", $("api-key").value.trim());
    setStatus("key saved", "good");
  });
  $("refresh-btn").addEventListener("click", refreshAll);
  $("run-btn").addEventListener("click", runInference);
  bindRepoOperatorUi();
  bindInferenceChatUi();
  bindOpsUi();
  bindDashboardTabs();
  document.querySelectorAll("[data-reload]").forEach((btn) => btn.addEventListener("click", refreshAll));
  refreshAll();
  setInterval(refreshAll, 15000);
}

boot();
