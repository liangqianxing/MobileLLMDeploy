Param(
    [string]$Python = "python",
    [string]$VenvPath = ".\.venv"
)

Write-Host "Creating virtual environment at $VenvPath" -ForegroundColor Cyan
& $Python -m venv $VenvPath

$pip = Join-Path $VenvPath "Scripts\pip.exe"
if (-Not (Test-Path $pip)) {
    throw "pip not found at $pip"
}

Write-Host "Upgrading pip..." -ForegroundColor Cyan
& $pip install --upgrade pip

Write-Host "Installing dependencies from requirements.txt" -ForegroundColor Cyan
& $pip install -r requirements.txt

Write-Host "Environment ready. Activate with: `n$VenvPath\Scripts\Activate.ps1`" -ForegroundColor Green
