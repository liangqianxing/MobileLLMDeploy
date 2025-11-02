# Mobile LLM Deploy Toolkit

帮助你在移动端（Android / iOS）快速部署量化大模型，并与端云协同实验配套的资料与脚本。目录中的说明文档与示例脚本可直接复用到自己的项目中。

## 目录结构

- `docs/`：部署指南、性能调优、常见问题。
- `android/`：Android 端示例工程说明、NDK/MLC-LLM 使用指引。
- `ios/`：iOS 端 CoreML / MLC-LLM 集成说明。
- `models/`：放置量化后的模型、tokenizer 及配置文件（初始为空）。
- `scripts/`：数据/模型下载、格式转换脚本模版。
- `README.md`：项目总览（当前文件）。

## 环境要求

| 场景 | 必备组件 | 说明 |
| --- | --- | --- |
| 通用 | Python ≥ 3.9、Git、Hugging Face CLI | 用于模型下载、格式转换。 |
| Android | Android Studio、NDK r26+、CMake、JDK 17 | 配合 `llama.cpp` / `MLC-LLM` 打包 APK。 |
| iOS | Xcode 15+、CMake（如需）、coremltools | CoreML / MLC-LLM 构建 .mlpackage 与 Swift 调用。 |
| 量化工具 | `llama.cpp`, `mlc-llm`, `bitsandbytes`, `ggml` | 可按所选模型按需安装。 |

建议提前安装：

```powershell
python -m pip install --upgrade pip
python -m pip install datasets huggingface_hub transformers accelerate
python -m pip install mlc-llm-core coremltools==7.2.1 bitsandbytes
```

> 按需安装即可，例如只使用 `llama.cpp` 则以官方 README 为准安装其依赖。

## 快速开始

1. **下载模型**（示例：Qwen2.5-1.5B-Instruct）：
   ```powershell
   python scripts\\download_model.py --repo qwen/Qwen2.5-1.5B-Instruct --output models\\qwen2.5-1.5b
   ```
2. **量化格式转换**：
   - llama.cpp：执行 `scripts\\convert_to_gguf.bat` 生成 GGUF 文件。
   - MLC-LLM：执行 `scripts\\package_with_mlc.py` 打包 Android/iOS runtime。
3. **移动端集成**：
   - Android：参考 `android/README.md`，选择 `llama.cpp` Demo 或 `MLC-LLM` APK 模板。
   - iOS：参考 `ios/README.md`，使用 CoreML 或 MLC-LLM Swift 接口。
4. **测试与调优**：使用 `docs/perf_tuning.md` 的建议调整线程数、批量大小，记录耗时、能耗、内存、温度。

## 推荐模型与格式

| 模型 | 规模 | 推荐格式 | 适用场景 |
| --- | --- | --- | --- |
| Phi-3-mini 4K | 3.8B | GGUF Q4_K_M (llama.cpp) | Android CPU 兼容广（低内存设备）。 |
| Qwen2.5-1.5B-Instruct | 1.5B | GGUF Q4_1 / MLC int4 | 中等手机，中文任务好。 |
| LLaMA-3.2-3B-Instruct | 3B | MLC int4 / CoreML int4 | iOS + CoreML、Android GPU 。 |
| Mistral-7B-Instruct v0.3 | 7B | GGUF Q4_K_M (高配机) | 高端手机/平板 + NPU/GPU。 |

## 端云协同建议

1. 本地模型完成意图识别、初步摘要等轻量任务。
2. 复杂问题转云端大模型，云端回传结果供端侧继续执行后续步骤。
3. 结合 `experiments/mobile_benchmark`（在原仓库中）生成质量指标，手机端记录延迟/能耗后合并分析。

## 下一步资源

- `docs/android_setup.md`：llama.cpp、MLC-LLM、NNAPI 与能耗监控。
- `docs/ios_setup.md`：CoreML 转换、MLC iOS 打包、Metal/ANE 调试。
- `docs/perf_tuning.md`：线程配置、KV cache、分批策略、温控技巧。
- `scripts/download_model.py`：使用 `huggingface_hub` 下载模型权重（待完善）。
- `scripts/convert_to_gguf.bat`：llama.cpp 格式转换脚本（待完善）。
- `scripts/package_with_mlc.py`：调用 MLC-LLM 一键打包（待完善）。

根据上述指南填充脚本或替换为自己的模型即可，后续可加入端侧数据采集、调度策略评估等模块。欢迎继续完善。*** End Patch
