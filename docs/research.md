# 研究依据与方法选择

[简体中文](research.md) | [English](research.en.md)

## 上游基础与特别致谢

[ModelTrace](https://github.com/xqy2006/ModelTrace) 是 TraceOne 最重要的直接基础。
它把 1–355 数字偏好发展成可运行的黑盒指纹系统，清晰地融合 marginal Hellinger
与 ordered-block 特征，并公开了参考库、采集代码和验证过程。尤其值得赞赏的是，
作者不仅提供了很有创造力的方法，也坦诚记录了一问/三问、same-provider 与
cross-provider 的边界，为后续工作留下了高质量、可审计的起点。作者的
[Linux Do 复盘](https://linux.do/t/topic/2827119?tl=en) 报告了这些结果，也明确
说明最佳结果依赖三问。更早的社区实现
[hlwy-ai-checker](https://github.com/hanlinwenyuan/hlwy-ai-checker) 和
[随机数分布讨论](https://linux.do/t/topic/2472419/1) 同样应得到明确承认。

TraceOne 的贡献建立在这条优秀工作脉络上：保留并明确归因其可复现 feature、
bank 与语料，再补充 single-call 协议、当前 Codex enrollment、open-set rejection、
冻结盲测和独立降质检验。任何对照数字都只描述本文协议下的差异，不削弱原工作
的首创性与价值。完整致谢和复用边界见
[ACKNOWLEDGEMENTS.md](../ACKNOWLEDGEMENTS.md) 与
[third_party/NOTICE.md](../third_party/NOTICE.md)。

## 近期工作如何影响设计

- [LLMmap, USENIX Security 2025](https://www.usenix.org/conference/usenixsecurity25/presentation/pasquini)
  展示黑盒输出行为可识别模型版本，同时说明 open world、适配攻击与多轮查询是
  核心难点。它支持“行为 fingerprint 可用”，但不支持把 closed-set confidence
  当作 unknown 证明。
- [LLMPrint, ACL 2026](https://aclanthology.org/2026.acl-long.541/) 使用优化 prompt
  与统计 verification 提高 query efficiency。TraceOne 因此探索一次响应内大量
  constrained micro-decisions，但 proprietary Codex routes 没有论文所需的完整
  source optimization access。
- [Targeted Counterfactual Fingerprinting](https://arxiv.org/abs/2608.08195) 强调
  受限答案空间和针对性 probe。我们的 128-bit pairwise active probe 正是沿这条
  路线测试；实测未超过主方法，所以作为负结果保留。
- [Conformal Inference for Open-Set and Imbalanced Classification](https://arxiv.org/abs/2510.13037)
  研究开放集与类别不平衡分类中的 conformal inference，提醒拒识必须写清 calibration
  与适用条件。它不是 LLM 归因论文；TraceOne 仅借鉴其开放集问题意识。我们的
  support 使用 empirical rank 与距离阈值，但数据并不满足可宣称 distribution-free
  coverage 的独立同分布条件，因此不把它包装成 conformal guarantee。
- [Do System Prompts Leave Behavioral Fingerprints? A Large-Scale Empirical Study of Clone Detection via Output Similarity](https://arxiv.org/abs/2608.24461)
  表明 system prompt/prefix 可显著改变 detector。TraceOne 因而把 prompt、Schema、
  runtime、wrapper、reasoning 和时间作为 label provenance，而不把模型名当成永恒类别。

## 为什么一问仍能包含 315 个选择

这里的 query budget 按模型调用/turn 计，不按输出 token 中的 decision 数计。
一次长 response 可以提供比单个数字更低方差的分布估计，同时省去三次独立网络
调用。9×35 Schema 解决了无 Schema 版本真实出现的越界、解释文字和截断问题。

这是一种 query packing，而不是把 315 个选择当作 315 个独立统计样本。最终
accuracy 的独立单位仍是 75 次模型调用；Wilson interval 也以 75 为分母。

## 为什么使用分层拒识

单一 closed-set softmax/argmax 对任意有效输入总能给出高置信标签。TraceOne 分层：

1. 13-model bank 检查绝对分布相似度和 top label 是否为目标；
2. ridge adapter 解决当前 Codex wrapper 下五个相近 route 的边界；
3. target-support envelope 检查预测点是否位于对应 enrollment 支持区域。

这种结构把“最像谁”和“是否像任何已登记目标”分开。它把 held-label false
identification 从 ModelTrace 的 288/288 降到 24/288，但 GPT-5.4 仍与目标 support
高度重叠，说明一次数字响应的可辨识信息存在上限。

## Active probe 与 nonlinear adapter 的负结果

- Pairwise v1：128 个随机整数对，模型每对选左/右；小样本且同数据选超参数的
  development LOO 为 24/25。
- Pairwise v2：依据 340 条 enrollment log-odds 选 pair，结果降到 22/25。
- 同一 39 维 feature 上，KNN、shrinkage LDA 与 RBF prototype 的 whole-collection
  CV 均未超过 alpha=1 ridge 的 412/415。

负结果说明“更主动”或“更非线性”不自动等于更可靠；我们没有因为方法更新颖就
把它放进发布路径。

## 降质检测依据

[When LLMs get significantly worse: A statistical approach to detect model degradations](https://proceedings.iclr.cc/paper_files/paper/2026/hash/70de9e3948645a1be2de657f14d85c6d-Abstract-Conference.html)
强调 paired item-level outcomes 与控制 false positive；
[LLM Accuracy Stats](https://github.com/amazon-science/LLM-Accuracy-Stats) 也建议先对
同一 example 的 rerun 做合理聚合，再做 permutation/paired inference。这些工作
支持把能力 canary 与身份 fingerprint 完全拆开。

TraceOne 选择 exact one-sided McNemar，是因为 canary outcome 为逐题 binary，且
关心 regression 是否多于 improvement。Minimum effect 防止“统计显著但无实际
意义”；Holm 防止查看多个题族后挑最小 p-value；exact power planning 防止 48 题
这样的低功效设计把 `not significant` 错读为 `no degradation`。

## 下一步最有价值的实验

- 从从未参与 bank 或阈值选择的独立 provider 采集 unknown blind set。
- 跨日期、system prompt、reasoning level 和 Codex runtime 做预注册 drift matrix。
- 若能获得可信 routing attestation，把 requested-label agreement 升级为真实
  substitution evaluation。
- 预先定义可行动的 degradation effect、功效与重试策略，再运行 baseline/current
  canary；不要看到结果后改题或改阈值。
