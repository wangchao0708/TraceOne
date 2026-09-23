# 结果与证据账本

[简体中文](results.md) | [English](results.en.md)

## 七模型首轮冻结确认：未过门槛

`release-candidate-v9` 于 2026-09-23 16:29:50 UTC 冻结，首条
`confirmation-v8` 于 16:32:05 UTC 采集。七类各 15 条，共 105 次调用全部成功、
严格符合 Schema，并使用相同的 Codex runtime、Low reasoning、prompt 与 wrapper。

TraceOne `supported` 是 101/105（96.19%）：5.5、5.6 Luna/Terra/Sol 和 6 Sol
各 15/15，6 Astra 与 6 Luna 各 13/15。因此没有达到预登记的“每类至少 14/15”
门槛。四条失败包括两条 outer guard 拒识和两条适配器误判；完整失败分母与逐条结果
见 [confirmation-v8-evaluation.json](../data/confirmation-v8-evaluation.json)。

同响应的新版 ModelTrace closed-set 一问也是 101/105，但逐类不同：5.6 Sol
14/15、6 Astra 13/15、6 Luna 14/15；非重叠三问为 35/35。它们不是模型服务
真实权重的证明，也不能凭这些点估计声称 TraceOne 已全面超过 ModelTrace。
对照见 [confirmation-v8-head-to-head.json](../data/confirmation-v8-head-to-head.json)。
这批失败确认只在冻结规则判定未通过后，才允许进入下一轮开发；不能把它重新称为
v9 的盲测成功。

## 0.2.0 七模型开发证据

ModelTrace 作者及时公开的新版 16-model bank（上游 commit
`55a2e4a55170423b484d701e9a82ab62b268c811`）包含 GPT-6 Sol 与 Luna 的
各 36 条 Low-reasoning 参考响应。TraceOne 在此优秀开放工作的基础上，用同一个
9×35 问题另外采集两款各 83 条独立 enrollment，与旧五款各 83 条组成平衡的
581 条训练集。两批 enrollment 的 Codex runtime 不同，已逐类记录。

冻结前的 68/15 开发划分共有 105 条测试响应：`supported` 为 100/105，
`enrolled` 为 102/105。新款 6 Sol 是 15/15；6 Luna 的 `supported` 是 13/15，
其中一条分类错、一条被支持域拒识。旧版 Astra 也为 13/15；这是需要保留的
失败证据，不能写成“七款开发集全对”。完整逐样本结果见
[seven-model-development-v1.json](../data/seven-model-development-v1.json)。

16-model held-label open-world 开发评测包含九个未登记标签各 36 条：
`supported` 误接收 34/324（10.49%），`enrolled` 51/324（15.74%）；
ModelTrace closed-set 按定义会给 324/324 个有效 unknown 输入命名。主要短板为
GPT-5.4 的 19/36 与 Claude Opus 5.5 的 10/36。数据仍来自上游参考语料，
并非独立 provider 盲测；它与旧版 24/288 使用的标签集合不同，不能直接比较
百分比。见 [open-world-development-v3.json](../data/open-world-development-v3.json)。

最终 581 条训练配置先固定在
[release-candidate-v9.json](../config/release-candidate-v9.json)，随后按
[confirmation-v8.json](../config/confirmation-v8.json) 的七款各 15 条规则采集新
确认集。开发数据只用于选择配置，不能替代新确认结果。

## 0.1.0 五模型发布结论（历史）

0.1.0 发布使用 `release-candidate-v8` + `confirmation-v7`：先冻结、后采集、再揭盲。

- 75 次调用全部 `return_code=0`，75 个 sample ID 唯一。
- 75/75 严格 9×35 Schema 合规；prompt/schema hash、runtime、reasoning、wrapper
  在批内均一致。
- TraceOne `supported`：75/75，coverage 75/75，Wilson 95% CI
  95.13%–100%。
- 五类：5.5、Luna、Terra、Sol、Astra 均为 15/15。

这些是 requested-label agreement，不是独立的 served-weight 真值。

## 同响应 ModelTrace 对照

- TraceOne 一问：75/75。
- ModelTrace closed-set 一问：74/75；唯一错误在 Sol，因此 Sol 14/15，另四类
  15/15。
- ModelTrace 三问：25 个非重叠 triplet 全对，每类 5/5。

TraceOne 对 ModelTrace 一问的 paired discordance 只有 1 比 0；单侧 exact sign/
McNemar p=0.5，不足以证明准确率显著更高，也不是正式 non-inferiority 检验。
可以支持的结论是：本批五类逐类点估计未低于一问对照，Sol 多对一条；每次决定
从三次调用降到一次，且一问与三问 arm 的 accuracy 点估计均为 100%。三问只有
25 个决定，不能把 25/25 和 75/75 当作等样本量比较。

证据：

- [confirmation-v7 evaluation](../data/confirmation-v7-evaluation.json)
- [confirmation-v7 head-to-head](../data/confirmation-v7-head-to-head.json)
- [public confirmation responses](../data/public/confirmation-v7.jsonl)
- [release manifest](../config/release-v0.1.0.json)

## Open-world development

每个 fold 删除一个完整 excluded label 后再拟合，合计 8×36=288 个真正未见
label 样本：

- TraceOne `supported`：24/288 false accepts，8.33%，Wilson 95% CI
  5.66%–12.10%。
- TraceOne `enrolled`：59/288，20.49%，Wilson 95% CI 16.23%–25.52%。
- ModelTrace closed-set：288/288 false identifications；它在有效输入上没有
  `unknown` 分支。
- 同一 75 条 target holdout 在八个 gallery fold 中重复使用：`supported` 平均
  98.33%，最低 97.33%；不能把它当成 600 个独立样本。
- 主要失败集中于 GPT-5.4：`supported` 20/36 false accepts。

这是超参数已被查看的 development 结果，而且 unknown 来自上游语料，不是新
provider 盲测。它证明方法显著减少 closed-set 强制命名，但没有证明普适 OOD。
完整 decisions 在 [open-world-development-v2.json](../data/open-world-development-v2.json)。

旧 v6 的“完整 bank 内 excluded labels 2/288”只说明已登记 distractor rejection；
因为那些 labels 参与了 bank 构建，不再称为真正 open world。

## 开发过程中的失败

- 无 Schema 的 v2 曾出现 Luna 越界并截断，促成 strict 9×35 Schema。
- confirmation-v2 为 73/75，Sol 13/15；未过门槛。
- 190-row adapter 的真正盲测 confirmation-v3 为 71/75；未过门槛。
- confirmation-v4 为 73/75，Sol 13/15；未过门槛。
- v6 adapter 的 confirmation-v5 为 74/75；唯一失败是 Astra 240 秒 timeout，
  其余 74 个有效响应全部正确。
- v7 target-support 的 confirmation-v6 为 71/75：adapter 两错，support 又拒绝
  两个正确 Astra；未过每类 ≥14/15 门槛。这批随后才成为 v8 development。
- v8 选择 alpha=1：415-row whole-collection CV 为 412/415，优于 alpha=30 的
  411/415。KNN、LDA、RBF prototype 均未超过；见
  [adapter-model-exploration.json](../data/adapter-model-exploration.json)。

历史失败不与最终 confirmation 合并。为缩小公开发布面，原始失败批次不进入精简
主分支；其分母、关键结果和淘汰原因完整保留在本账本。

## Active probe 负结果

我们尝试把自由数字序列改成一次响应内 128 个成对二选一 bit：随机 pair v1 在
同数据选超参数的小样本 leave-one-out 为 24/25；按 340 条 enrollment 优化 pair
后的 v2 反而为 22/25，均低于主方法，因此没有进入发布 classifier。这项开发负
结果保留在账本中；其探索性 prompt、脚本和原始评测不进入精简发布主分支，也不
构成盲测结论。

## 降质检测状态

仓库提供完整方法，但没有捏造“已检测到服务端降质”的实测结论。

- 48-item canary 在假设 regression=0.10、improvement=0.02、minimum effect=0.05
  时 exact power 只有 29.06%。
- 192-item canary v2 的相应 power 为 89.76%。
- 实现报告 paired regressions/improvements、无效与缺失、exact one-sided McNemar，
  并对题族做 Holm-Bonferroni。

功效依赖预声明概率；实际监测必须重新记录 baseline/current 的 model、provider、
runtime、reasoning、wrapper、日期与重试策略。
