# Android 示例工程说明

本目录用于存放 Android 端测试或 Demo 项目，可根据以下建议组织：

- `llama_cpp_demo/`：基于官方 `llama.cpp/android` 的 Kotlin 示例。
- `mlc_chat_app/`：使用 `MLC-LLM` 的 Chat 应用模板。
- `profiling/`：性能与能耗测试脚本、ADB 收集工具。

快速指引：

1. 遵循 `../docs/android_setup.md` 完成模型量化与环境搭建。
2. 将量化模型（GGUF 或 MLC artifact）拷贝到对应工程的 `app/src/main/assets/models/`。
3. 为每个工程准备 `README` 记录编译命令、Gradle 配置、关键代码路径。
4. 若需在真机上采集耗时、电量等数据，可将日志写入 `/sdcard/Android/data/<pkg>/files/` 并通过 `adb pull` 导出。

> 当前目录未包含具体代码，可按需初始化 Android Studio 项目后放置于此。*** End Patch
