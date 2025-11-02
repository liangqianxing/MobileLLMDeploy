# 日志格式与采集规范（Android）

统一的日志格式有助于后续的性能分析与端云协同实验。本指南定义了推荐的 JSONL 结构，并提供采集建议。

## 1. 推荐字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | 样本或会话唯一标识，与 PC 端评测脚本中的 `id` 对齐。 |
| `strategy` | string | 运行策略名，如 `edge_llama_cpp`、`mlc_gpu`, `edge_cloud`. |
| `prompt_tokens` | int | 输入 token 数，便于估算上下文开销。 |
| `output_tokens` | int | 输出 token 数，用于计算 tokens/s。 |
| `start_ms` / `end_ms` | int | 任务开始/结束时间（毫秒级 Unix 时间或 `SystemClock.elapsedRealtime()`）。 |
| `prefill_ms` / `decode_ms` | int | 可选：分阶段耗时。 |
| `tokens_per_second` | float | `output_tokens / (decode_ms / 1000)`。 |
| `battery_level_start` / `battery_level_end` | float | 0–1 范围的电量比例（或百分比）。 |
| `energy_mwh` | float | 耗电量（毫瓦时），可通过 `BatteryManager.BATTERY_PROPERTY_ENERGY_COUNTER` 或 batterystats 推算。 |
| `temperature_c` | float | 设备温度（如 SoC 或电池），单位摄氏度。 |
| `bytes_up` / `bytes_down` | int | 网络上下行字节数（端云协同时使用）。 |
| `notes` | string | 其他备注：崩溃重启、降频等。 |

示例见 `android/log_template.jsonl`。

## 2. 写入方式

1. 在应用中创建日志目录：`context.getExternalFilesDir("logs")`，例如 `files/logs/2025-11-01/`。
2. 每次推理完成后将 JSON 写入文件（追加方式）。建议使用 buffered writer，并在异常情况下 flush。
3. 如果需要实时分析，可同时写入 `Logcat` 或通过 WebSocket 上报到 PC。

## 3. 电量与温度采集

- **电量**：
  ```kotlin
  val bm = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
  val energy = bm.getLongProperty(BatteryManager.BATTERY_PROPERTY_ENERGY_COUNTER) // nWh
  ```
  开始与结束读取差值，再转换为 mWh。
- **温度**：使用 `android.os.ThermalListener` 或读取 `/sys/class/thermal` 相关节点。
- **网络流量**：`TrafficStats.getUidTxBytes(uid)` / `TrafficStats.getUidRxBytes(uid)`。

## 4. 导出与对齐

- 导出日志：`adb pull /sdcard/Android/data/<pkg>/files/logs logs/android`。
- 与 PC 端指标对齐：确保 `id` 与基准脚本产生的 `id` 一致，可通过 JSON 合并工具或 Pandas 进行 Join。
- 若端云协同中存在多个子任务，可添加 `node` 字段记录 DAG 节点名称。

## 5. 注意事项

- 使用 JSONL 而非单一 JSON，便于流式写入与追加。
- 控制日志大小，可按日期/会话轮换文件，或设定最大文件大小后滚动。
- 为保护隐私，必要时对 prompt 中的敏感文本做脱敏或只记录哈希。

遵循以上规范，可大幅提升实验数据复用与分析效率。*** End Patch
