# 重置并导出指定应用的电量统计
Param(
    [Parameter(Mandatory = $true)]
    [string]$PackageName,

    [string]$Output = "logs\android\batterystats.txt"
)

if (-not (Get-Command adb -ErrorAction SilentlyContinue)) {
    throw "adb 未找到，请先配置 Android SDK Platform-Tools。"
}

Write-Host "重置 Batterystats..." -ForegroundColor Cyan
adb shell dumpsys batterystats --reset

Write-Host "请在设备上运行测试，结束后按任意键继续..."
[void][System.Console]::ReadKey($true)

Write-Host "导出 Batterystats" -ForegroundColor Cyan
adb shell dumpsys batterystats $PackageName > $Output

Write-Host "结果保存在 $Output" -ForegroundColor Green
