(function () {
  const $ = (id) => document.getElementById(id);
  const state = { lastAssistantText: "", turn: 0 };

  function makePanel(className) {
    const panel = document.createElement("section");
    panel.className = `panel ${className}`;
    return panel;
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

  function setupAssistantObserver(modelOutput) {
    state.lastAssistantText = modelOutput.textContent.trim();
    const observer = new MutationObserver(() => {
      const text = modelOutput.textContent.trim();
      if (!text || text === "No run yet." || text === state.lastAssistantText) return;
      state.lastAssistantText = text;
      state.turn += 1;
      appendChatMessage("assistant", text, `runtime response ${state.turn}`);
    });
    observer.observe(modelOutput, { childList: true, characterData: true, subtree: true });
  }

  function moveRuntimeControls(sidebar, originalControls) {
    const tokenBox = originalControls.querySelector(".token-box");
    const formStack = originalControls.querySelector(".form-stack");

    if (tokenBox) {
      tokenBox.classList.add("chat-token-box");
      sidebar.appendChild(tokenBox);
    }

    if (formStack) sidebar.appendChild(formStack);
  }

  function buildQuickPrompts(prompt) {
    const quickPrompts = document.createElement("div");
    quickPrompts.className = "quick-prompts";
    quickPrompts.innerHTML = `
      <button type="button" data-prompt="Explain Duotronic non-collapse in one precise paragraph.">Non-collapse</button>
      <button type="button" data-prompt="Summarize the latest runtime witnesses and what they imply.">Witness summary</button>
      <button type="button" data-prompt="Run a careful reasoning pass about whether this runtime should write memory.">Memory policy</button>
    `;
    quickPrompts.querySelectorAll("[data-prompt]").forEach((btn) => {
      btn.addEventListener("click", () => {
        prompt.value = btn.dataset.prompt || "";
        prompt.focus();
      });
    });
    return quickPrompts;
  }

  function buildMain(prompt, runButton, modelOutput) {
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
    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = "AI";
    modelOutput.classList.add("bubble", "chat-output");
    latest.append(avatar, modelOutput);
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

    return main;
  }

  function buildInspector(policyOutput) {
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
    runFacts.textContent = "Run facts are shown in the policy and witness panels after each inference.";
    inspector.append(runFactsTitle, runFacts);
    return inspector;
  }

  function bindPromptShortcuts(prompt, runButton) {
    prompt.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        runButton.click();
      }
    });

    runButton.addEventListener("click", () => {
      const promptText = prompt.value.trim();
      if (promptText) appendChatMessage("user", promptText, "you");
    }, { capture: true });
  }

  function setupInferenceChat() {
    if ($("xavi-chat-log")) return;
    const prompt = $("prompt");
    const runButton = $("run-btn");
    const modelOutput = $("model-output");
    const policyOutput = $("policy-output");
    if (!prompt || !runButton || !modelOutput || !policyOutput) return;

    const inferencePanels = Array.from(document.querySelectorAll('[data-tab-panel="inference"]'));
    if (inferencePanels.length < 2) return;

    const originalControls = inferencePanels[0];
    const originalOutputs = inferencePanels[1];
    const wasActive = originalControls.classList.contains("active-tab-panel") || originalOutputs.classList.contains("active-tab-panel");

    const shell = document.createElement("section");
    shell.className = "inference-chat-shell";
    shell.dataset.tabPanel = "inference";
    if (wasActive) shell.classList.add("active-tab-panel");

    const sidebar = makePanel("inference-chat-sidebar");
    sidebar.innerHTML = `
      <div>
        <div class="eyebrow">Inference session</div>
        <h2>Local model chat</h2>
        <p>Chat against the active runtime while the witness layer, WG-RNN state, and policy gate stay visible.</p>
      </div>
    `;

    moveRuntimeControls(sidebar, originalControls);
    sidebar.appendChild(buildQuickPrompts(prompt));

    shell.append(sidebar, buildMain(prompt, runButton, modelOutput), buildInspector(policyOutput));
    originalControls.replaceWith(shell);
    originalOutputs.remove();

    bindPromptShortcuts(prompt, runButton);
    setupAssistantObserver(modelOutput);
  }

  document.addEventListener("DOMContentLoaded", setupInferenceChat);
})();
