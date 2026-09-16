# TraceOne Web

[简体中文](site.md) | [English](site.en.md)

在线地址：<https://traceone-model-check.nutmeg-basil-6747.chatgpt.site>

## 用户流程

网页在同一个工作区提供两个切换模式：

- **模型识别**：复制问题、粘贴回答，直接预测五条目标路由之一或 `unknown`；
- **降智线索**：先选择自己实际使用的模型，再完成同样的一问流程。网页自动把
  所选模型与指纹预测比较，返回“指纹一致”“指纹异常”或“无法判断”。

两个模式都只需复制一个自包含问题，把模型返回的完整 JSON 粘贴回网页。页面同时
显示绝对相似度、支持距离和五候选相对权重，用户不需要手工比较模型名称。

网页不会要求 API Key，也不会把模型回答发送给服务器。HTML、CSS、JavaScript、
三个冻结模型资产均由站点静态提供，识别计算只发生在当前浏览器标签页。页面设置
了仅允许同源脚本、样式、数据连接的 Content Security Policy。

## 与 Python 发布路径的一致性

`dist/traceone.js` 逐步移植以下发布路径：

1. ModelTrace 衍生的 13-model marginal Hellinger 与 ordered-block outer guard；
2. 五类 ridge adapter；
3. shrinkage Mahalanobis target-support rejection 与 high-margin rescue；
4. 显式的 `unknown` 结果。

`scripts/test_web_classifier.mjs` 将浏览器实现与 Python 保存结果逐字段比对，包括
标签、格式、有效数字数、outer candidates、相似度、score margin、adapter margin、
support distance、threshold 与 empirical p-value。75 条冻结 confirmation 加 5 条
网页 pilot 共 80 条全部在 `1e-9` 数值容差内一致。

`scripts/test_site_assets.mjs` 还验证网页中的 bank、adapter、support 与 Python 包
资产逐字节一致，并检查网页显示问题与 `prompts/identity-web-v1.txt` 一致。

## 自包含问题 pilot

冻结发布 prompt 通过 Codex JSON Schema 强制 9×35 输出。普通网页用户无法方便地
附加 Schema，因此 `identity-web-v1` 把 9×35 形状写入同一次提问，仍然只有一次
模型调用。

2026-09-15 的 compatibility pilot 对五条目标 route 各采集一次 Low reasoning：

- `supported` requested-route agreement：5/5；
- 严格格式合规：1/5；
- 其余四条各有 1–2 个越界整数，保留 313–314 个有效数字，均经过 distance path；
- 浏览器与 Python 结果完全一致。

公开响应与评测分别在
[data/public/web-prompt-v1-pilot.jsonl](../data/public/web-prompt-v1-pilot.jsonl) 和
[data/web-prompt-v1-pilot-evaluation.json](../data/web-prompt-v1-pilot-evaluation.json)。
样本量只有 5，不能把 5/5 当作准确率证明；它只验证复制—回答—粘贴链路可工作。

## 解释边界

候选条形图是五类 adapter score 的相对 softmax，仅用于可视化，不是服务端身份
概率。绝对相似度与支持距离也不是可信 attestation。system prompt、reasoning、
runtime、日期和服务更新都可能使行为指纹漂移。

网页的“降智线索”是**路由指纹一致性筛查**：可靠预测与所选模型一致时显示
“指纹一致”，可靠预测不一致时显示“指纹异常”，拒识时显示“无法判断”。不一致
也可能来自分类误差、路由替换、系统提示、推理强度或时间漂移，因此不能单独证明
能力下降。仓库中严格的能力降质结论仍由独立 canary、paired McNemar、功效规划
和多重比较校正产生。

网页明确致谢 [ModelTrace](https://github.com/xqy2006/ModelTrace)。它是本项目最
重要的直接方法与实现基础；TraceOne 的网页只是把这条优秀工作脉络包装成更易用
的一问交互，并增加拒识与可视化。
