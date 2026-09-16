import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath));
const text = (relativePath) => read(relativePath).toString("utf8");
const hash = (relativePath) => crypto.createHash("sha256").update(read(relativePath)).digest("hex");

const mirroredAssets = [
  "unified_bank.json",
  "codex_low_v4_adapter_415.json",
  "codex_low_v4_support_415.json",
];
for (const asset of mirroredAssets) {
  const sourceHash = hash(`src/traceone/data/${asset}`);
  const siteHash = hash(`dist/data/${asset}`);
  if (sourceHash !== siteHash) throw new Error(`${asset} is not synchronized`);
}

const html = text("dist/index.html");
const css = text("dist/styles.css");
const app = text("dist/app.js");
const promptMatch = html.match(/<div class="prompt-box" id="promptText"[^>]*>([\s\S]*?)<\/div>/);
if (!promptMatch) throw new Error("prompt box not found");
const normalize = (value) => value.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
const visiblePrompt = normalize(promptMatch[1]);
const promptFile = normalize(text("prompts/identity-web-v1.txt"));
if (visiblePrompt !== promptFile) throw new Error("visible prompt differs from identity-web-v1.txt");

for (const marker of ["identifyMode", "degradationMode", "expectedModel"]) {
  if (!html.includes(`id="${marker}"`)) throw new Error(`${marker} control is missing`);
}
if (!html.includes('wrap="off"')) throw new Error("response textarea must disable visual wrapping");
const promptRule = css.match(/\.prompt-box\s*\{([^}]*)\}/)?.[1] ?? "";
if (!promptRule.includes("white-space: normal")) throw new Error("prompt must wrap to show its full content");
if (promptRule.includes("overflow-x: auto")) throw new Error("prompt must not require horizontal dragging");
if (!css.includes("white-space: pre")) throw new Error("response textarea must preserve unwrapped input");
const modelNameRule = css.match(/\.model-name\s*\{([^}]*)\}/)?.[1] ?? "";
if (!modelNameRule.includes("white-space: nowrap")) throw new Error("result title must stay on one line");
if (!modelNameRule.includes("text-align: center")) throw new Error("result title must be centered");
if (app.includes("presentation.verdict")) throw new Error("result subtitle must not be rendered");
const aboutMatch = html.match(/<section class="about-section"[^>]*>([\s\S]*?)<\/section>/);
if (!aboutMatch || normalize(aboutMatch[1]) !== "TraceOne 建立在 ModelTrace 的优秀开源工作之上。") {
  throw new Error("ModelTrace acknowledgement must contain exactly one compact sentence");
}
for (const conclusion of ["指纹一致", "指纹异常", "无法判断"]) {
  if (!app.includes(conclusion)) throw new Error(`${conclusion} conclusion is missing`);
}
for (const overclaim of ["未发现降智", "疑似降智", "No degradation detected", "Suspected degradation"]) {
  if (app.includes(overclaim)) throw new Error(`${overclaim} must not be presented as a web verdict`);
}

const manifest = JSON.parse(text(".openai/hosting.json"));
if (manifest.static?.directory !== "dist") throw new Error("hosting static directory is not dist");
if (!manifest.project_id) throw new Error("hosting project_id is missing");
if (!fs.existsSync(path.join(root, "dist/index.html"))) throw new Error("dist/index.html is missing");

console.log(JSON.stringify({
  mirroredAssets: mirroredAssets.length,
  promptSynchronized: true,
  dualModeWorkflow: true,
  fullPromptVisible: true,
  oneLineResultTitle: true,
  hostingManifest: true,
}));
