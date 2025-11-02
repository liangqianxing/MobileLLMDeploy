# llama.cpp Android Demo (预配置版)

本目录来自 `ggerganov/llama.cpp/examples/llama.android`，已预先放入 Qwen2.5 1.5B Instruct 的 Q4_K_M 量化模型，开箱即可在 Android Studio 中运行。

## 快速开始
1. 在 Android Studio 中 `File > Open`，选择本目录。
2. 等待 Gradle Sync 完成，确认 NDK/CMake 依赖正常。
3. 连接手机（USB 调试已启用），点击 `Run` 安装 `app` 模块。
4. 启动后应用会自动将内置模型从 `assets/models/` 复制到沙盒目录，并在界面底部显示“Qwen2.5 1.5B Instruct (Q4_K_M, 内置)”按钮；点击 `Load` 即可加载模型，随后在文本框中输入问题并点击 `Send` 发起推理。

## 日志与调试
- 推理日志会显示在应用主界面；可通过 `Copy` 按钮复制。
- 使用 `adb logcat -s LLamaAndroid MainViewModel` 观察底层日志。
- 若需采集能耗/性能数据，参考仓库根目录下的 `scripts/android_collect_batterystats.ps1` 与 `docs/logging_guidelines.md`。

## 自定义模型
1. 将新的 GGUF 文件放入 `app/src/main/assets/models/`。
2. 在 `MainActivity.kt` 中更新 `bundledModelName` 和展示文案。
3. 重新构建并安装即可。*** End Patch
