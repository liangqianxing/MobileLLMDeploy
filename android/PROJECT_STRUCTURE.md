# Android 项目结构建议

为了方便团队协作与自动化测试，推荐按如下方式组织 Android 端代码与资源：

```
android/
  llama_cpp_demo/
    app/
      src/
        main/
          java/          # Kotlin/Java 业务逻辑
          cpp/           # JNI/Native 代码（如需）
          assets/
            models/      # GGUF、tokenizer 等静态模型
            prompts/     # 可选：提示模板、系统提示
          res/
            layout/      # UI 布局
            values/      # strings.xml、styles.xml
    gradle/
    build.gradle
  mlc_chat_app/
    app/
      src/
        main/
          java/
          assets/
            models/
              qwen/      # MLC artifact（params/weights/metadata/...）
            configs/     # 模型配置、对话模板、调度策略
  tools/
    profiler/            # 性能分析脚本、Perfetto 模板
    scripts/             # ADB 自动化脚本（可链接到项目根目录 scripts/）
```

## 注意事项

1. **模型体积**：避免直接提交超过 Git LFS 限额的模型，可使用 README 说明下载方式或在首次启动时自动拉取。
2. **配置隔离**：将模型名称、最大上下文长度、线程数等参数放入 `assets/configs/*.json`，方便切换实验设置。
3. **日志输出**：统一写入 `files/logs/<strategy>/<timestamp>.jsonl`，字段包含 `id`、`start_ms`、`end_ms`、`tokens`、`energy_mwh`，便于后续合并分析。
4. **安全与权限**：若需将模型存储在外置存储，请使用 `Scoped Storage` 并在运行时请求权限；避免在 release 构建中保留调试开关。
5. **Gradle 配置**：将 NDK、CMake 版本固定在 `gradle.properties`，并在 README 中注明编译命令（`./gradlew assembleDebug`）。
6. **自动化**：可在 `tools/scripts` 中添加 shell/PowerShell 脚本，用于 ADB 推送模型、收集日志、运行 monkey 测试等。

按照上述结构组织后，与 PC 端实验脚本的联动、性能调优和日志管理都会更加清晰高效。*** End Patch
