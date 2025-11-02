Param(
    [Parameter(Mandatory = $true)]
    [string]$ModelFile,

    [string]$PackageName,

    [string]$DevicePath = "/sdcard/Android/data"
)

if (-not (Get-Command adb -ErrorAction SilentlyContinue)) {
    throw "adb 未找到，请先配置 Android SDK Platform-Tools。"
}

if (-not (Test-Path $ModelFile)) {
    throw "模型文件不存在: $ModelFile"
}

$escaped = $ModelFile -replace '\\', '/'

Write-Host "推送模型到设备..." -ForegroundColor Cyan
adb push "$ModelFile" "$DevicePath"

if ($PackageName) {
    $targetPath = "$DevicePath/$PackageName/files/models/"
    Write-Host "将模型移动到应用沙盒: $targetPath" -ForegroundColor Cyan
    adb shell "run-as $PackageName mkdir -p files/models"
    adb shell "run-as $PackageName cp $DevicePath/$(Split-Path $escaped -Leaf) files/models/"
}

Write-Host "完成。请在应用中使用对应路径加载模型。" -ForegroundColor Green
