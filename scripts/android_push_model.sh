#!/usr/bin/env bash
set -euo pipefail

if ! command -v adb >/dev/null 2>&1; then
  echo "adb 未找到，请先安装 Android SDK Platform-Tools." >&2
  exit 1
fi

if [ "$#" -lt 1 ]; then
  echo "用法: $0 <模型文件> [package.name] [设备路径]" >&2
  exit 1
fi

MODEL_FILE=$1
PACKAGE_NAME=${2:-}
DEVICE_PATH=${3:-/sdcard/Android/data}

if [ ! -f "$MODEL_FILE" ]; then
  echo "模型文件不存在: $MODEL_FILE" >&2
  exit 1
fi

echo "推送模型到 $DEVICE_PATH"
adb push "$MODEL_FILE" "$DEVICE_PATH"

if [ -n "$PACKAGE_NAME" ]; then
  TARGET="$DEVICE_PATH/$PACKAGE_NAME/files/models"
  BASENAME=$(basename "$MODEL_FILE")
  echo "复制到应用沙盒: $TARGET"
  adb shell "run-as $PACKAGE_NAME mkdir -p files/models"
  adb shell "run-as $PACKAGE_NAME cp $DEVICE_PATH/$BASENAME files/models/"
fi

echo "完成。"
