import {
  TARGET_MODELS,
  identifyWithArtifacts,
  loadArtifacts,
  targetRelativeWeights,
} from "./traceone.js";

const copyButton = document.querySelector("#copyPrompt");
const promptText = document.querySelector("#promptText");
const responseInput = document.querySelector("#modelResponse");
const analyzeButton = document.querySelector("#analyzeButton");
const inputStatus = document.querySelector("#inputStatus");
const resultPanel = document.querySelector("#resultPanel");
const languageButton = document.querySelector(".language-button");
const identifyModeButton = document.querySelector("#identifyMode");
const degradationModeButton = document.querySelector("#degradationMode");
const modeSwitch = document.querySelector("#modeSwitch");
const expectedModelField = document.querySelector("#expectedModelField");
const expectedModelSelect = document.querySelector("#expectedModel");
const identityPrompt = promptText.textContent.replace(/\s+/g, " ").trim();
const MODEL_DISPLAY_NAMES = {
  "gpt-5.5": "GPT-5.5",
  "gpt-5.6-luna": "GPT-5.6 Luna",
  "gpt-5.6-terra": "GPT-5.6 Terra",
  "gpt-5.6-sol": "GPT-5.6 Sol",
  "gpt-6-astra": "GPT-6 Astra",
};

const copy = {
  zh: {
    htmlLang: "zh-CN",
    documentTitle: "TraceOne — 一次响应，识别模型行为指纹",
    languageButton: "EN",
    languageLabel: "切换到英文",
    methodNav: "方法",
    aboutNav: "关于",
    pageTitle: "一次提问<br />看见模型的行为指纹",
    introCopy: "分析在你的浏览器中完成，不会上传回答。",
    modeLabel: "检测模式",
    identifyMode: "模型识别",
    degradationMode: "降智线索",
    expectedModelLabel: "你正在使用的模型",
    expectedModelHint: "网站会自动将指纹预测与它比较。",
    expectedModelPlaceholder: "请选择模型",
    chooseModel: "请选择你正在使用的模型",
    copyKicker: "复制问题",
    copyTitle: "发送给需要检测的模型",
    degradationCopyTitle: "发送给你正在使用的模型",
    copyButton: "复制问题",
    copied: "已复制",
    manualCopy: "请按 Ctrl/⌘ + C",
    pasteKicker: "粘贴回答",
    pasteTitle: "保留模型返回的完整 JSON",
    placeholder: "在这里粘贴 9 × 35 的 JSON 数组…",
    waiting: "等待回答",
    input: (count) => `已输入 ${count.toLocaleString()} 个字符`,
    analyze: "分析响应",
    analyzeDegradation: "检查一致性",
    analyzing: "正在分析",
    loadingTitle: "正在比对行为指纹",
    loadingCopy: "数据只在当前浏览器标签页中处理。",
    emptyKicker: "分析结果",
    emptyTitle: "等待一次响应",
    emptyCopy: "完成两步后，这里会显示最接近的模型、支持距离与候选分布。",
    degradationEmptyTitle: "等待一次检查",
    degradationEmptyCopy: "选择当前模型并粘贴回答后，这里会给出指纹一致性结论与预测。",
    principle1Title: "一次响应",
    principle1Copy: "315 个微选择被装入一个严格的 JSON 响应。",
    principle2Title: "分层判断",
    principle2Copy: "先检查参考库相似度，再区分五条目标路由。",
    principle3Title: "允许未知",
    principle3Copy: "证据不足时返回 unknown，而不是强行指定模型。",
    aboutPrefix: "TraceOne 建立在",
    aboutSuffix: " 的优秀开源工作之上。",
    footerCopy: "本地优先的行为证据",
    identified: "支持域内",
    unknown: "证据不足",
    unknownTitle: "未知",
    local: "仅本地处理",
    resultKicker: "判断结果",
    noDegradation: "指纹一致",
    suspectedDegradation: "指纹异常",
    degradationUnknown: "无法判断",
    selectedModel: "所选模型",
    predictedModel: "指纹预测",
    similarity: "绝对相似度",
    format: "有效数字",
    margin: "适配间隔",
    support: "支持距离",
    candidates: "五个候选",
    relativeOnly: "相对权重，仅用于可视化",
    warning: "行为指纹会随系统提示、推理强度、运行时和服务端更新漂移。结论表示统计相似性，不证明实际服务权重。",
    degradationWarning: "这里检测的是行为指纹是否与所选模型一致。不一致可提示路由变化或指纹漂移，但不能单独证明能力下降。",
    reset: "重新检测",
    formatWarning: "格式存在偏差，但有效数字达到分析门槛；请谨慎解释结果。",
    unknownReasons: {
      invalid: "无法读取完整 JSON。请只粘贴数组或 {\"numbers\": [...]}，并移除 ``` 代码围栏。",
      short: (count) => `只读取到 ${count}/315 个有效整数；至少需要 280 个。`,
      guard: "外层参考库认为其他已登记标签更相似，因此没有进入五模型判断。",
      similarity: "响应与参考分布的绝对相似度低于发布阈值。",
      adapter: "五个目标候选的分数过于接近，无法稳定区分。",
      support: "最接近候选仍超出该模型的经验支持区域。",
      generic: "一个或多个可靠性检查没有通过。",
    },
    errorTitle: "暂时无法完成分析",
    errorCopy: "本地模型资产没有成功载入。请刷新页面后重试。",
  },
  en: {
    htmlLang: "en",
    documentTitle: "TraceOne — One-response behavioral model trace",
    languageButton: "中文",
    languageLabel: "Switch to Chinese",
    methodNav: "Method",
    aboutNav: "About",
    pageTitle: "One question<br />See the model's behavioral trace",
    introCopy: "Analysis stays in your browser; the response is never uploaded.",
    modeLabel: "Check mode",
    identifyMode: "Identify model",
    degradationMode: "Degradation signal",
    expectedModelLabel: "Model you are using",
    expectedModelHint: "The site compares its fingerprint prediction automatically.",
    expectedModelPlaceholder: "Choose a model",
    chooseModel: "Choose the model you are using",
    copyKicker: "Copy the question",
    copyTitle: "Send it to the model you want to check",
    degradationCopyTitle: "Send it to the model you are using",
    copyButton: "Copy question",
    copied: "Copied",
    manualCopy: "Press Ctrl/⌘ + C",
    pasteKicker: "Paste the answer",
    pasteTitle: "Keep the model's complete JSON",
    placeholder: "Paste the 9 × 35 JSON array here…",
    waiting: "Waiting for an answer",
    input: (count) => `${count.toLocaleString()} characters entered`,
    analyze: "Analyze response",
    analyzeDegradation: "Check consistency",
    analyzing: "Analyzing",
    loadingTitle: "Comparing behavioral traces",
    loadingCopy: "The data is processed only in this browser tab.",
    emptyKicker: "Analysis result",
    emptyTitle: "Waiting for one response",
    emptyCopy: "After two steps, the nearest model, support distance, and candidate distribution appear here.",
    degradationEmptyTitle: "Waiting for one check",
    degradationEmptyCopy: "Choose the current model and paste its answer to see a fingerprint-consistency result and prediction.",
    principle1Title: "One response",
    principle1Copy: "315 micro-choices are packed into one strict JSON response.",
    principle2Title: "Layered decision",
    principle2Copy: "Check reference-bank similarity before separating five target routes.",
    principle3Title: "Unknown is valid",
    principle3Copy: "Return unknown when evidence is weak instead of forcing a label.",
    aboutPrefix: "TraceOne builds on the excellent open-source work of",
    aboutSuffix: ".",
    footerCopy: "Local-first behavioral evidence",
    identified: "In support",
    unknown: "Insufficient evidence",
    unknownTitle: "Unknown",
    local: "Processed locally",
    resultKicker: "Result",
    noDegradation: "Fingerprint consistent",
    suspectedDegradation: "Fingerprint anomaly",
    degradationUnknown: "Unable to determine",
    selectedModel: "Selected model",
    predictedModel: "Fingerprint prediction",
    similarity: "Absolute similarity",
    format: "Usable numbers",
    margin: "Adapter margin",
    support: "Support distance",
    candidates: "Five candidates",
    relativeOnly: "Relative weight, visualization only",
    warning: "Behavioral fingerprints can drift with system prompts, reasoning effort, runtime, and server updates. This is statistical similarity, not proof of served weights.",
    degradationWarning: "This checks whether the behavioral fingerprint matches the selected model. A mismatch can flag rerouting or drift, but cannot by itself prove a capability loss.",
    reset: "Check another",
    formatWarning: "The format is imperfect, but enough usable numbers remain; interpret the result cautiously.",
    unknownReasons: {
      invalid: "The JSON could not be read. Paste only the array or {\"numbers\": [...]}, without ``` code fences.",
      short: (count) => `Only ${count}/315 usable integers were found; at least 280 are required.`,
      guard: "The outer reference bank found another registered label more similar, so the five-model decision was not entered.",
      similarity: "Absolute similarity to the reference distributions is below the release threshold.",
      adapter: "The five target candidates are too close to separate reliably.",
      support: "The nearest candidate still falls outside that model's empirical support region.",
      generic: "One or more reliability checks did not pass.",
    },
    errorTitle: "Analysis is temporarily unavailable",
    errorCopy: "The local model assets did not load. Refresh the page and try again.",
  },
};

let language = "zh";
let lastResult = null;
let mode = "identity";

function setText(id, value) {
  const element = document.querySelector(`#${id}`);
  if (element) element.textContent = value;
}

function renderEmptyState() {
  const t = copy[language];
  const degradation = mode === "degradation";
  resultPanel.removeAttribute("data-state");
  resultPanel.innerHTML = `<div class="result-empty">
    <div class="signal-orbit" aria-hidden="true"><span></span><span></span><span></span></div>
    <p class="step-kicker" id="emptyKicker">${t.emptyKicker}</p>
    <h2 id="emptyTitle">${degradation ? t.degradationEmptyTitle : t.emptyTitle}</h2>
    <p id="emptyCopy">${degradation ? t.degradationEmptyCopy : t.emptyCopy}</p>
  </div>`;
}

function setMode(nextMode) {
  mode = nextMode;
  const degradation = mode === "degradation";
  const t = copy[language];
  identifyModeButton.classList.toggle("is-active", !degradation);
  degradationModeButton.classList.toggle("is-active", degradation);
  identifyModeButton.setAttribute("aria-pressed", String(!degradation));
  degradationModeButton.setAttribute("aria-pressed", String(degradation));
  expectedModelField.hidden = !degradation;
  setText("copyTitle", degradation ? t.degradationCopyTitle : t.copyTitle);
  analyzeButton.textContent = degradation ? t.analyzeDegradation : t.analyze;
  updateInputStatus();
  if (lastResult && (!degradation || expectedModelSelect.value)) renderResult(lastResult);
  else renderEmptyState();
}

function setLanguage(nextLanguage) {
  language = nextLanguage;
  const t = copy[language];
  document.documentElement.lang = t.htmlLang;
  document.title = t.documentTitle;
  languageButton.textContent = t.languageButton;
  languageButton.setAttribute("aria-label", t.languageLabel);
  setText("methodNav", t.methodNav);
  setText("aboutNav", t.aboutNav);
  modeSwitch.setAttribute("aria-label", t.modeLabel);
  identifyModeButton.textContent = t.identifyMode;
  degradationModeButton.textContent = t.degradationMode;
  setText("expectedModelLabel", t.expectedModelLabel);
  setText("expectedModelHint", t.expectedModelHint);
  expectedModelSelect.options[0].textContent = t.expectedModelPlaceholder;
  document.querySelector("#page-title").innerHTML = t.pageTitle;
  setText("introCopy", t.introCopy);
  setText("copyKicker", t.copyKicker);
  copyButton.textContent = t.copyButton;
  setText("pasteKicker", t.pasteKicker);
  setText("pasteTitle", t.pasteTitle);
  responseInput.placeholder = t.placeholder;
  setText("principle1Title", t.principle1Title);
  setText("principle1Copy", t.principle1Copy);
  setText("principle2Title", t.principle2Title);
  setText("principle2Copy", t.principle2Copy);
  setText("principle3Title", t.principle3Title);
  setText("principle3Copy", t.principle3Copy);
  setText("aboutPrefix", t.aboutPrefix);
  setText("aboutSuffix", t.aboutSuffix);
  setText("footerCopy", t.footerCopy);
  setMode(mode);
}

function updateInputStatus() {
  const length = responseInput.value.trim().length;
  const t = copy[language];
  const missingModel = mode === "degradation" && !expectedModelSelect.value;
  analyzeButton.disabled = length === 0 || missingModel;
  inputStatus.textContent = missingModel ? t.chooseModel : length ? t.input(length) : t.waiting;
}

function candidateWeights(result) {
  const scores = result.adapter.adapterScores;
  if (scores && Object.keys(scores).length) return targetRelativeWeights(scores);
  const candidateMap = new Map(
    result.adapter.outerGuard.candidates.map((candidate) => [candidate.model, candidate.closedSetProbability]),
  );
  const values = TARGET_MODELS.map((model) => candidateMap.get(model) ?? 0);
  const total = values.reduce((sum, value) => sum + value, 0) || 1;
  return values.map((value) => value / total);
}

function unknownReason(result) {
  const t = copy[language].unknownReasons;
  const errors = result.parsed.errors;
  if (errors.some((error) => error.startsWith("invalid_json") || error === "missing_grid_array")) return t.invalid;
  if (result.parsed.numbers.length < 280) return t.short(result.parsed.numbers.length);
  const reasons = result.adapter.outerGuard.guardReasons;
  if (reasons.includes("guard_model_won")) return t.guard;
  if (reasons.includes("low_absolute_similarity")) return t.similarity;
  if (result.adapter.outerGuard.status === "identified" && result.adapter.status === "unknown") return t.adapter;
  if (result.supportPath === "rejected") return t.support;
  return t.generic;
}

function formatNumber(value, digits = 2) {
  return Number.isFinite(value) ? value.toFixed(digits) : "—";
}

function candidateMarkup(result) {
  const t = copy[language];
  const weights = candidateWeights(result);
  const maximum = Math.max(...weights, 1e-12);
  return `
    <div class="distribution">
      <div class="distribution-title">
        <h3>${t.candidates}</h3>
        <span>${t.relativeOnly}</span>
      </div>
      <div class="candidate-list">
        ${TARGET_MODELS.map((model, index) => {
          const primary = model === (result.label ?? result.adapter.label) ? " primary" : "";
          const width = Math.max(3, (weights[index] / maximum) * 100);
          return `<div class="candidate-row${primary}">
            <span title="${MODEL_DISPLAY_NAMES[model]}">${MODEL_DISPLAY_NAMES[model]}</span>
            <div class="bar-track"><div class="bar-fill" style="--width:${width.toFixed(2)}%"></div></div>
            <span class="candidate-value">${Math.round(weights[index] * 100)}%</span>
          </div>`;
        }).join("")}
      </div>
    </div>`;
}

function resultPresentation(result) {
  const t = copy[language];
  const identified = result.status === "identified";
  if (mode === "identity") {
    return {
      pillClass: identified ? "" : " unknown",
      pillText: identified ? t.identified : t.unknown,
      title: identified ? MODEL_DISPLAY_NAMES[result.label] : t.unknownTitle,
      comparison: "",
      warning: t.warning,
    };
  }

  const expected = expectedModelSelect.value;
  const expectedName = MODEL_DISPLAY_NAMES[expected] ?? expected;
  const predictedName = identified ? MODEL_DISPLAY_NAMES[result.label] : t.unknownTitle;
  const comparison = `<div class="comparison-card">
    <div><span>${t.selectedModel}</span><strong>${expectedName}</strong></div>
    <span class="comparison-arrow" aria-hidden="true">→</span>
    <div><span>${t.predictedModel}</span><strong>${predictedName}</strong></div>
  </div>`;
  if (!identified) {
    return {
      pillClass: " unknown",
      pillText: t.degradationUnknown,
      title: t.degradationUnknown,
      comparison,
      warning: t.degradationWarning,
    };
  }
  const matches = result.label === expected;
  return {
    pillClass: matches ? "" : " alert",
    pillText: matches ? t.noDegradation : t.suspectedDegradation,
    title: matches ? t.noDegradation : t.suspectedDegradation,
    comparison,
    warning: t.degradationWarning,
  };
}

function renderResult(result) {
  const t = copy[language];
  const identified = result.status === "identified";
  const presentation = resultPresentation(result);
  const similarity = result.adapter.outerGuard.similarity ?? 0;
  const orbit = Math.max(0, Math.min(1, similarity));
  const formatNote = result.parsed.valid ? "" : `<div class="error-detail">${t.formatWarning}</div>`;
  const reason = identified ? "" : `<div class="error-detail">${unknownReason(result)}</div>`;
  const supportValue = Number.isFinite(result.supportDistance)
    ? `${formatNumber(result.supportDistance, 1)} / ${formatNumber(result.supportThreshold, 1)}`
    : "—";

  resultPanel.dataset.state = "result";
  resultPanel.innerHTML = `
    <div class="result-content">
      <div class="verdict-topline">
        <span class="status-pill${presentation.pillClass}">${presentation.pillText}</span>
        <span class="privacy-label">${t.local}</span>
      </div>
      <p class="step-kicker result-kicker">${t.resultKicker}</p>
      <h2 class="model-name">${presentation.title}</h2>
      ${presentation.comparison}
      <div class="confidence-orbit" style="--orbit:${(orbit * 100).toFixed(1)}%">
        <div class="orbit-value"><strong>${Math.round(orbit * 100)}%</strong><span>${t.similarity}</span></div>
      </div>
      <div class="metrics-grid">
        <div class="metric"><span>${t.format}</span><strong>${result.parsed.numbers.length} / 315</strong></div>
        <div class="metric"><span>${t.margin}</span><strong>${formatNumber(result.adapter.adapterMargin, 3)}</strong></div>
        <div class="metric"><span>${t.support}</span><strong>${supportValue}</strong></div>
      </div>
      ${candidateMarkup(result)}
      ${reason}${formatNote}
      <p class="result-warning">${presentation.warning}</p>
      <div class="result-actions"><button class="reset-button" id="resetButton" type="button">${t.reset}</button></div>
    </div>`;
  document.querySelector("#resetButton").addEventListener("click", resetExperience);
}

function renderError() {
  const t = copy[language];
  resultPanel.dataset.state = "result";
  resultPanel.innerHTML = `<div class="result-content">
    <span class="status-pill unknown">${t.unknown}</span>
    <h2 class="model-name">${t.errorTitle}</h2>
    <p class="verdict-copy">${t.errorCopy}</p>
  </div>`;
}

async function runAnalysis(responseText) {
  const t = copy[language];
  analyzeButton.disabled = true;
  analyzeButton.textContent = t.analyzing;
  resultPanel.dataset.state = "result";
  resultPanel.innerHTML = `<div class="result-loading"><div><div class="loading-ring"></div><h2>${t.loadingTitle}</h2><p>${t.loadingCopy}</p></div></div>`;
  try {
    const artifacts = await loadArtifacts();
    const result = identifyWithArtifacts(responseText, artifacts);
    lastResult = result;
    if (mode === "identity" || expectedModelSelect.value) renderResult(result);
    else renderEmptyState();
    inputStatus.textContent = result.parsed.valid
      ? `${result.parsed.numbers.length} / 315 JSON`
      : `${result.parsed.numbers.length} / 315`;
    if (window.innerWidth <= 820) resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    return result;
  } catch (error) {
    console.error(error);
    renderError();
    throw error;
  } finally {
    analyzeButton.disabled = responseInput.value.trim().length === 0
      || (mode === "degradation" && !expectedModelSelect.value);
    analyzeButton.textContent = mode === "degradation"
      ? copy[language].analyzeDegradation
      : copy[language].analyze;
  }
}

function resetExperience() {
  lastResult = null;
  responseInput.value = "";
  renderEmptyState();
  updateInputStatus();
  responseInput.focus();
}

copyButton.addEventListener("click", async () => {
  const t = copy[language];
  try {
    await navigator.clipboard.writeText(identityPrompt);
    copyButton.textContent = t.copied;
    setTimeout(() => { copyButton.textContent = copy[language].copyButton; }, 1600);
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(promptText);
    selection.removeAllRanges();
    selection.addRange(range);
    copyButton.textContent = t.manualCopy;
  }
});

responseInput.addEventListener("input", updateInputStatus);
responseInput.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter" && !analyzeButton.disabled) {
    event.preventDefault();
    void runAnalysis(responseInput.value).catch(() => {});
  }
});
analyzeButton.addEventListener("click", () => { void runAnalysis(responseInput.value).catch(() => {}); });
identifyModeButton.addEventListener("click", () => setMode("identity"));
degradationModeButton.addEventListener("click", () => setMode("degradation"));
expectedModelSelect.addEventListener("change", () => {
  updateInputStatus();
  if (lastResult && expectedModelSelect.value) renderResult(lastResult);
  else if (!expectedModelSelect.value) renderEmptyState();
});
languageButton.addEventListener("click", () => setLanguage(language === "zh" ? "en" : "zh"));

function registerWebMCP() {
  const context = document.modelContext;
  if (!context?.registerTool) return;
  const lifecycle = new AbortController();
  const register = (tool) => Promise.resolve(context.registerTool(tool, { signal: lifecycle.signal })).catch(console.error);
  void register({
    name: "get_traceone_identity_prompt",
    title: "Get TraceOne identity prompt",
    description: "Return the exact one-response question used by the visible TraceOne workflow.",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    annotations: { readOnlyHint: true, untrustedContentHint: false },
    execute() { return { prompt: identityPrompt, expectedShape: "9 arrays × 35 integers" }; },
  });
  void register({
    name: "analyze_traceone_model_response",
    title: "Analyze model response",
    description: "Paste and analyze one model-generated TraceOne JSON response, updating the visible result panel.",
    inputSchema: {
      type: "object",
      properties: { response: { type: "string", minLength: 2, description: "The complete JSON response from the tested model." } },
      required: ["response"],
      additionalProperties: false,
    },
    annotations: { readOnlyHint: false, untrustedContentHint: true },
    async execute(input) {
      if (!input || typeof input.response !== "string" || input.response.trim().length < 2) {
        throw new Error("response must be a non-empty JSON string");
      }
      responseInput.value = input.response;
      updateInputStatus();
      const result = await runAnalysis(input.response);
      return {
        status: result.status,
        label: result.label,
        usableNumbers: result.parsed.numbers.length,
        formatCompliant: result.parsed.valid,
        supportPath: result.supportPath,
      };
    },
  });
}

setLanguage("zh");
registerWebMCP();
