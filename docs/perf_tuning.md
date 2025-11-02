# 推理性能调优与测量指南

本篇总结了在移动端运行大模型时常见的性能、能耗优化手段，并给出测量建议，帮助你快速定位瓶颈。

## 1. 关键参数

| 参数 | 说明 | 调优建议 |
| --- | --- | --- |
| `n_threads` / `num_threads` | 推理线程数量 | 一般等于大核数；小核可能拖慢速度。 |
| `n_batch` / `batch_size` | 每次解码的 token 批量 | Android 上 128–256；超出内存会激增。 |
| `context_length` | 上下文窗口长度 | 精简 prompt，减少 KV cache 内存。 |
| `quantization` | 量化格式 | Q4_K_M / q4f16_1 在速度与精度间平衡；需要更快可选 q3_k。 |
| `gpuDelegate` / `device` | 使用 GPU/NNAPI/ANE | GPU 可加速，ANE 更节电；若设备不支持自动退回 CPU。 |
| `prefill` vs `decode` | 预填充与自回归阶段 | Prefill 受上下文长度影响，decode 看 token/s。 |

## 2. 常见优化策略

1. **Prompt 精简**：保留必要上下文，减少初始 token；结合检索或压缩提示。
2. **KV Cache 管理**：旧版本 `llama.cpp` KV cache 始终常驻，可开启 `--cache-reuse`、`--mmapped`，或在 MLC 使用 sliding window。
3. **分块推理**：对长输入分段处理，端侧只处理关键句，其他交给云端。
4. **调度大核**：在 Android 通过 `adb shell cmd uimode night yes` 等方式保持性能模式；或使用 `setThreadPriority` 把推理线程绑定大核。
5. **温控策略**：持续推理会触发降频，可在 1–2 分钟内插入冷却间隔或降低采样温度。
6. **LoRA/Adapter**：对端侧模型做轻量 LoRA 微调，可兼顾准确率与性能。

## 3. 性能指标记录

建议为每个任务记录以下信息，并写入 JSON 方便后续分析：

```json
{
  "id": "sample-0001",
  "strategy": "edge_llm",
  "prompt_tokens": 180,
  "output_tokens": 120,
  "prefill_ms": 320,
  "decode_ms": 1350,
  "tokens_per_second": 55.6,
  "energy_mwh": 12.4,
  "avg_power_mw": 980,
  "temperature_c": 42.1
}
```

- **时间戳**：在调用前后记录 `SystemClock.elapsedRealtime()` / `mach_absolute_time()`。
- **电量**：Android 使用 `BatteryStats`、`BatteryManager.BATTERY_PROPERTY_ENERGY_COUNTER`；iOS 可通过 `IOReport` 或第三方库。
- **温度**：Android `ThermalStatusListener`，iOS 可访问 `ProcessInfo` 的 `thermalState`。

## 4. 质量与性能权衡

- 使用 PC 端基准脚本计算 ROUGE / EM / Accuracy。
- 将质量指标与延迟、能耗绘制到同一张图（Pareto 曲线），寻找最优调度策略。
- 若端侧质量下降明显，可考虑：
  - 采用大模型做知识蒸馏或提示工程强化端侧模型表现。
  - 端云协同：端侧负责快速草稿，云端进行复核或长上下文。
  - 引入 reranker（端侧轻量 + 云端高精），以质量换取性能。

## 5. 故障排查

- **token/s 异常下降**：检查是否触发降频（温度过高），或者内存不足导致 GC/Swap。
- **偶尔卡顿**：UI 与推理共线程；应开新线程处理推理并用 handler 更新 UI。
- **能耗陡升**：大批量长时间运行，可考虑在推理中插入 `sleep`，或者降低 `top_k`、`top_p` 减少采样。

---

如需更详细的端云协同指标设计，请参考 `docs/edge_cloud_workflow.md`（如尚未创建可自行补充）。组合使用本指南与 Android/iOS 部署手册，即可完整覆盖端侧 LLM 部署与调优过程。*** End Patch
