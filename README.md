# TraceOne

[简体中文](README.md) | [English](README_EN.md)

<p align="center">
  <a href="https://traceone-model-check.nutmeg-basil-6747.chatgpt.site/">
    <img src="docs/assets/quick-online.svg" alt="快速在线使用" width="280" />
  </a>
</p>

TraceOne 用一次 315 数字提问为七条 Codex 模型路由提供实验性指纹识别，并把行为身份
漂移与能力降质拆成两个独立、可复现的统计问题：

- `gpt-5.5`
- `gpt-5.6-luna`
- `gpt-5.6-terra`
- `gpt-5.6-sol`
- `gpt-6-astra`
- `gpt-6-sol`
- `gpt-6-luna`

`gpt-6.1-sol` 已于 2026-09-30 用 Codex 订阅实际采样，并完成八类训练接口与
开发评测；但**尚不能可靠区分 GPT-6 Astra，因此未启用第八个预测选项**。
本轮公开 489 次真实调用，其中 178 次请求 6.1 Sol，全部仍是一问 315 数字。
原问题的八类 `supported` 开发结果为 101/120，6.1 Sol 为 8/15；改进问题的最佳
closed-set 开发候选为 175/192，6.1 Sol 为 19/24，仍未达到逐类门槛。两者不是
同批 paired 比较，也不是独立盲测；不能宣称八款均优于上游。默认七类版本保持不变。
详见 [结果与证据](docs/results.md#gpt-61-sol-扩展开发尚未通过发布门槛) 与
[评测协议](docs/protocol.md#10-gpt-61-sol-扩展开发)。

## 在线使用

[打开 TraceOne Web](https://traceone-model-check.nutmeg-basil-6747.chatgpt.site)

网页把输出形状直接写进同一个问题，用户无需安装软件或附加 JSON Schema：复制
问题、向模型提问、粘贴完整回答即可。16-model outer guard、ridge adapter 与
target-support rejection 全部在浏览器本地运行，回答不会被上传。

网页提供“模型识别”和“降智线索”两个切换模式。后者让用户选择自己实际使用的
模型，由网页自动比较所选模型与指纹预测，并给出“指纹一致”“指纹异常”或
“无法判断”。这只是路由指纹一致性筛查；能力下降仍需独立 canary 评测，不能仅凭
一次指纹不一致下结论。

浏览器 JavaScript 实现与 Python 对最新 315 数字确认集的 105 条响应逐字段一致。
网页展示的是自包含问题；冻结确认使用了同一次调用附加 JSON Schema 的版本，
因此 103/105 不能直接当成网页提示词的准确率。历史五模型网页 pilot 为 5/5
路由匹配、1/5 严格格式合规，只是兼容性 smoke test。详见
[docs/site.md](docs/site.md)。

## 在 ModelTrace 基础上的扩展

TraceOne 首先向 [ModelTrace](https://github.com/xqy2006/ModelTrace) 作者
**xqy2006** 致以诚挚感谢。ModelTrace 把社区中“随机数字选择可能形成模型行为
指纹”的洞见，发展成了包含特征、参考库、采集流程与可复现实验的完整开源项目；
这是一项非常优秀、富有启发性且慷慨的工作，也是 TraceOne 最重要的直接基础。
下面的比较应理解为在这一坚实基础上的扩展与压力测试，而不是对原工作的否定。

- 身份识别从作者推荐的三次 probe 降为一次调用、一次响应。
- 不做裸 closed-set argmax：16-model outer guard、七类 ridge adapter 和
  target-support envelope 可返回 `unknown`。
- 有冻结配置、预注册盲测、完整失败分母、整批留一验证与可公开复现数据。
- “数字指纹变了”不等于“降智”；降质由独立 canary、paired McNemar、功效规划
  和 Holm-Bonferroni 校正判断。

TraceOne 复用并改造了 ModelTrace 的 marginal Hellinger、ordered-block 特征和
参考语料；许可证与改动边界见 [third_party/NOTICE.md](third_party/NOTICE.md)。
ModelTrace 还明确致谢了更早的
[hlwy-ai-checker](https://github.com/hanlinwenyuan/hlwy-ai-checker)，TraceOne 同样
尊重并承认这条社区工作脉络。完整致谢见
[ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md)，研究引用见
[docs/research.md](docs/research.md)。

## 我们的一问

实际冻结问题只有下面这一条；JSON Schema 只是同一次调用的输出约束：

```text
Using only the current language model, produce 315 separate first-instinct
choices of an integer from 1 through 355 inclusive in the exact JSON structure
required by the supplied output schema. Do not use tools, Python, code execution,
calculators, search, APIs, or external random generators. Do not count upward or
downward and do not use an arithmetic progression, repeating cycle, repeated block,
or another designed pattern. Accidental repetitions are valid. Output only the
schema-conforming JSON value with no explanation.
```

模型在一次 response 中返回 9×35 个整数。一次调用包含多个微选择，但不是三次
独立提问；prompt 与 Schema 分别在
[prompts/identity-v3-schema.txt](prompts/identity-v3-schema.txt) 和
[schemas/identity-v3.json](schemas/identity-v3.json)。

## 七模型三轮确认均未过预设门槛

新款 GPT-6 Sol/Luna 已进入 16-model 参考库和七类适配器。按冻结的
`confirmation-v8` 计划，105 次新调用全部严格符合 Schema；TraceOne 一问是
101/105，但 GPT-6 Astra 与 GPT-6 Luna 各只有 13/15，未过每类至少 14/15 的
预登记门槛。ModelTrace 同响应一问也是 101/105，三问是 35/35。
本批结果保留为失败证据，不能据此宣称七款均优于上游；详见
[docs/results.md](docs/results.md)。

随后冻结的 `release-candidate-v10` 在独立 `confirmation-v9` 上是 98/105；
GPT-5.6 Sol 为 13/15，GPT-6 Sol 为 12/15，仍未过同一门槛。
ModelTrace 同响应一问为 96/105，非重叠三问 35/35。

当前 315 数字 v11 加入原始数字频率特征，在新采集的 `confirmation-v10` 上为
103/105（98.1%）；GPT-6 Sol 为 13/15，仍未达到每类 ≥14/15 的预设门槛。
同响应 ModelTrace 一问为 104/105，互不重叠三问为 35/35。因此七模型支持
可以试用，但不能宣称全面超过上游。完整失败样本见
[docs/results.md](docs/results.md)。

## 0.1.0 的五模型冻结盲测结果

发布配置 v8 在 `confirmation-v7` 采集前冻结。75 次新调用全部成功且严格符合
Schema：

- TraceOne `supported`：75/75；五个模型分别 15/15。
- 同响应 ModelTrace 一问：74/75；Sol 为 14/15，其余为 15/15。
- 同响应、互不重叠的 ModelTrace 三问：25/25；每类 5/5。

因此，每次判定所需模型调用由三次降为一次。在固定为 75 次模型调用的本批对照中，
TraceOne 一问形成 75 个独立决定，三问 arm 形成 25 个 triplet 决定；两者点估计均为
100%。TraceOne 比同响应 ModelTrace 一问整体多对 1 条，但不足以证明统计显著优势
或正式 non-inferiority。准确表述是：本批五类的点估计均未低于一问对照，其中 Sol
多对一条；TraceOne 一问与三问 arm 的 accuracy 点估计相同。
95% Wilson 区间及逐样本决策见
[data/confirmation-v7-evaluation.json](data/confirmation-v7-evaluation.json) 和
[data/confirmation-v7-head-to-head.json](data/confirmation-v7-head-to-head.json)。

标签是 Codex `requested_model`，不是服务端实际权重的独立证明。

## 0.1.0 的 Open-world 结果与边界

真正的 held-label 评测会把一个完整 excluded label 同时移出 bank、adapter feature
space 和 support 拟合，再把它当作未见模型：

- `supported`：24/288 误接收，8.33%（95% Wilson 5.66%–12.10%）。
- `enrolled`：59/288 误接收，20.49%。
- ModelTrace closed-set：288/288 被迫归到某个已知标签。

这是调过超参数的 development 结果，未见样本来自上游语料，不是独立 provider
盲测。最大短板是 held-out GPT-5.4：`supported` 仍误接收 20/36。固定完整 bank
上的 excluded-route rejection 只能叫 registered-distractor 检查，不能冒充真正
OOD。完整结果在 [data/open-world-development-v2.json](data/open-world-development-v2.json)。

## 安装与身份识别

需要 Python 3.11 或更新版本。

```text
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

打印冻结 prompt：

```text
traceone prompt
```

采集一次 Codex 响应：

```text
python3 scripts/collect_codex.py \
  --output data/live/one.jsonl \
  --prompt prompts/identity-v3-schema.txt \
  --schema schemas/identity-v3.json \
  --split holdout --repeat 1 --model gpt-5.6-terra --run-id my-run
```

离线识别保存的 JSON 响应：

```text
traceone identify answer.json --format grid --method supported
```

`supported` 是较低 OOD 误接收的默认模式；`enrolled` 更偏重已登记模型的敏感度。
两者都先经过 16-model outer guard。`unknown` 是有效结果，不应强制改成某个模型。

复现最终评测与冻结检查：

```text
PYTHONPATH=src python3 scripts/evaluate_live.py \
  data/public/confirmation-v7.jsonl --output /tmp/traceone-eval.json
PYTHONPATH=src python3 scripts/evaluate_head_to_head.py \
  data/public/confirmation-v7.jsonl --output /tmp/traceone-h2h.json
python3 scripts/verify_frozen.py config/release-candidate-v8.json --revision 7b52cb1
python3 scripts/verify_release.py config/release-v0.1.0.json
python3 scripts/verify_frozen.py config/release-candidate-v11.json --revision 8d70a3b
PYTHONPATH=src python3 scripts/evaluate_live.py \
  data/public/confirmation-v10.jsonl --output /tmp/traceone-v11-eval.json
```

## 降质检测

身份 probe 只检测行为路由，不能证明“降智”。TraceOne v2 canary 有 192 道
版本化 exact-answer 题，baseline/current 对同一题逐项配对。默认把无效输出计错，
要求题目集合完全一致，并可按题族做 Holm 校正：

```text
traceone degradation baseline-outcomes.json current-outcomes.json \
  --minimum-effect 0.05 --by-family --invalid-policy fail
```

先做 exact power planning：

```text
traceone plan-degradation \
  --regression-probability 0.10 --improvement-probability 0.02 \
  --minimum-effect 0.05 --target-power 0.80
```

在该预声明情景下，旧 48 题设计的检测功效只有 29.1%，192 题为 89.8%，所以
发布 canary 扩到 192 题。该数字依赖假设，不是已观察到的降质率。采集与评分见
`scripts/collect_canary.py`、`traceone score-canary`；每题单独调用以保留合理的
item-level 配对，它不属于一次身份识别的调用预算。

## 证据与限制

- 最终 manifest：[config/release-v0.1.0.json](config/release-v0.1.0.json)
- 评测协议：[docs/protocol.md](docs/protocol.md)
- 完整结果与失败史：[docs/results.md](docs/results.md)
- 研究来源与负结果：[docs/research.md](docs/research.md)
- 去本地 task ID/stderr 的公开数据：[data/public](data/public)
- 公开数据、隐私边界与完整性检查：[docs/protocol.md](docs/protocol.md)
- 上游工作与完整致谢：[ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md)
- 项目贡献者与 AI 辅助边界：[CONTRIBUTORS.md](CONTRIBUTORS.md)
- 在线版实现与验证：[docs/site.md](docs/site.md)

行为指纹会随 system prompt、runtime、reasoning effort、wrapper 和服务端更新漂移。
没有 routing log 或可信 attestation 时，单次 mismatch 可能是分类错误、自然波动或
真实 route substitution；TraceOne 报告证据，不声称观察到了服务端权重本身。

MIT License。
