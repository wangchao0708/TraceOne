# 评测协议

[简体中文](protocol.md) | [English](protocol.en.md)

## 1. 目标与真值边界

目标是在固定 `reasoning_effort=low`、Codex runtime、wrapper 和 prompt 下，
从一次响应判断五个 `requested_model` route label，或返回 `unknown`。事件流没有
独立 `response_model` 或权重证明，因此结果叫 requested-label agreement，不能
解释为服务端实际权重的 ground truth accuracy。

身份识别必须只有一个模型调用和一个响应。9×35 个数字是同一响应内的 315 个
微选择；JSON Schema 是输出约束，不是额外问题。能力降质是另一个多题流程，
不计入身份识别的一问预算。

## 2. 冻结发布管线

最终发布使用 [release-candidate-v8.json](../config/release-candidate-v8.json)：

1. strict parser 要求对象只含 `numbers`，形状 9×35，值为 1–355 的 integer。
2. 复用 ModelTrace 的 13-model marginal Hellinger 与 ordered-block bank，并计算
   absolute JS similarity；不足 280 个可用值、top 不属于目标或 similarity <0.52
   时立即返回 `unknown`。
3. 通过 outer guard 后，39 维 feature（13 fused、13 marginal、13 absolute
   similarity）进入 alpha=1 的五类 ridge adapter；margin <0.01 时拒识。
4. 默认 `supported` 再检查 shrinkage Mahalanobis target-support envelope。
   每类 99% empirical distance 阈值；高于每类第 90 百分位的 adapter margin
   可 rescue。它是经验 support，不具 distribution-free OOD 保证。

训练集共 415 条、每类 83 条，来自公开的 340 条 enrollment 与失败盲测
confirmation-v6。所有 prompt、Schema、bank、实现和 artifact hash 在
confirmation-v7 采集前冻结，采集后复核一致。

## 3. Operating profiles

- `supported`：默认；outer guard + ridge + target support，优先降低未见类误接收。
- `enrolled`：outer guard + ridge，优先已登记路由 sensitivity。
- `bank`：仅上游特征与 guard，用于消融，不是推荐发布模式。

必须同时报告 match rate、coverage 和 abstention；禁止只在已识别子集上报 accuracy。

## 4. 数据划分与调参纪律

- Development：选择 prompt、feature、guard、adapter 与 support；不能作最终结论。
- Group CV：完整 collection 留一，测试批次不参与 normalization、fit 或阈值。
- Confirmation：先固定配置、样本数、成功规则与 hash，再采集全新响应。
- Open world：完整 label 同时从 gallery、feature space 和 support fit 中移除。

v7 配置的 confirmation-v6 为 71/75，未过预注册门槛；随后才允许作为 v8
development 数据。v8 的 confirmation-v7 是最终未见盲测，不能再用于修改 v8。
失败调用、格式错误、误判与 `unknown` 全部留在主分母。

## 5. 对照设计

最终 head-to-head 对同一批 75 条响应运行：

- TraceOne：每条响应作一次决定；
- ModelTrace-one：同一条响应的 closed-set mean fused argmax；
- ModelTrace-three：按模型和顺序划分 25 个互不重叠 triplet，每三条作一次决定。

比较复用同一 bank 与响应以减少数据差异，但 prompt/Schema 是 TraceOne 的，不是
ModelTrace 随机 challenge 原文；三问只有 25 个独立决定，置信区间更宽。不同论文
或社区数据集的点估计只作背景。

## 6. Open-world 定义

完整 bank 中“excluded route 被拒绝”只是 registered-distractor 结果，因为该标签
参与了 bank 构建。真正 held-label 流程对每个 excluded label 重新构建 bank、
adapter feature space 和 support，再测试被删标签。ModelTrace closed-set 在这些
有效输入上没有 `unknown`，所以 288/288 必然被命名；这不是称其 0% accuracy，
而是 100% false identification under unknown truth。

open-world v2 用过这些数据调参，只能称 development estimate。独立 provider、
新日期和未见 wrapper 的盲测仍是缺口。

## 7. 降质协议

数字指纹漂移不能证明能力下降。Canary baseline/current 必须使用同一版本题目、
scorer、reasoning、wrapper、重试策略和时间预算，并逐题配对：

- 主检验：exact one-sided McNemar；baseline 对/current 错为 regression，反向为
  improvement。
- 结论：observed accuracy loss 达到预声明 minimum effect，且 p≤alpha，才报告
  `degraded`。
- 无效回答默认计错；题目集合不一致默认 `invalid_comparison`，不能静默取交集。
- overall 是预声明 primary test；题族是 secondary tests，用 Holm-Bonferroni。
- benchmark 题量先用预期 regression/improvement 概率做 exact power planning。

Canary v2 有四个题族、每族 48 题，共 192 题。题目或独立 session 是统计单元，
不能把同一长响应中的 token 当成独立样本。

## 8. 公开数据与隐私

`data/live/` 永不提交。`scripts/export_public_data.py` 删除本地 `thread_id` 和
`stderr_tail`，保留数字响应、route、runtime、reasoning、usage、时间与 hash；
manifest 记录源文件和公开文件 digest。发布前仍需人工检查未来 runtime 新字段。

## 9. 已知限制

- 行为指纹会随 system prompt、wrapper、reasoning 和时间漂移。
- 上游参考语料缺少完整 reasoning provenance。
- 五类各 15 条只能证明本批结果；75/75 的 Wilson 95% 区间仍为约 95.13%–100%。
- GPT-5.4 是当前最难未见类，development 中仍有 20/36 false accepts。
- 没有 routing log/attestation，不能区分 detector error、自然波动和真实换模。
