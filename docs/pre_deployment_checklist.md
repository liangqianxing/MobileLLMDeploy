# 手机端部署前置检查清单

在开始 Android 或 iOS 上部署 LLM 前，建议逐条确认以下事项：

## 1. 环境与依赖
- [ ] 已安装 Python ≥ 3.9，确认 `python --version` 输出正确。
- [ ] 在当前目录执行 `scripts/setup_env.ps1`（Windows）或 `scripts/setup_env.sh`（macOS/Linux）创建虚拟环境并安装 `requirements.txt` 中依赖。
- [ ] 已安装 Git、Hugging Face CLI，并完成 `huggingface-cli login`。
- [ ] Android 部署：安装 Android Studio、NDK r26+、CMake、JDK 17。
- [ ] iOS 部署：安装 Xcode 15+，并具备有效的 Apple 开发者账号。

## 2. 模型与存储准备
- [ ] 选择目标模型（如 Qwen2.5 1.5B、Phi-3-mini 等），评估端侧内存峰值是否可接受。
- [ ] 运行 `python scripts/download_model.py --repo <model_repo> --output models/<model_name>` 下载权重与 tokenizer。
- [ ] 确认模型体积与设备存储空间匹配；必要时规划首次启动下载或差分更新。
- [ ] Android：准备 GGUF（llama.cpp）或 MLC artifact；iOS：准备 CoreML `.mlpackage` 或 MLC artifact。

## 3. 量化与转换
- [ ] 通过 `scripts/convert_to_gguf.py` 或官方工具完成 GGUF 量化（若使用 llama.cpp）。
- [ ] 通过 `scripts/package_with_mlc.py` 生成 MLC 模型包（若使用 MLC-LLM）。
- [ ] iOS + CoreML：确认转换/量化脚本可在 macOS 正常运行，输出 `.mlpackage`。
- [ ] 记录量化配置、上下文长度、词表信息，并存档在 `models/<model_name>/README.md`（建议）。

## 4. 工程与代码库
- [ ] Android：在 `android/` 目录创建或引用 Demo 工程，将模型置于 `app/src/main/assets/models/`。
- [ ] iOS：在 `ios/` 目录创建 Swift 项目，设置模型资源路径或下载逻辑。
- [ ] 把推理接口统一为 `init → generate(prompt, options)`，方便与实验脚本对接。
- [ ] 实现日志记录（延迟、能耗、上下行流量）并输出 JSONL，字段包含 `id`、`timestamp`、`token_count` 等。

## 5. 实验联动（可选）
- [ ] 与 PC 端的基准脚本 (`experiments/mobile_benchmark/benchmark_runner.py`) 对齐输出格式，用 `id` 链接质量指标。
- [ ] 规划端云协同策略：端侧任务列表、云端 API/模型、回传接口。
- [ ] 准备性能调优计划，参考 `docs/perf_tuning.md` 选择合适的线程数、批量大小、设备委托。

---

完成以上准备后，即可开始在移动设备上部署并验证大模型推理流程。*** End Patch
