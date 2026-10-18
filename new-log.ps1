param(
    [string]$Date,
    [switch]$NoOpen
)

if (-not $Date) { $Date = Get-Date -Format 'yyyy-MM-dd' }

$root = $PSScriptRoot
$hugo = Join-Path (Split-Path $root -Parent) '.tools\hugo.exe'
$file = Join-Path $root "content\logs\$Date.md"

if (-not (Test-Path $hugo)) {
    Write-Host "Hugo not found: $hugo" -ForegroundColor Red
    exit 1
}

if (Test-Path $file) {
    Write-Host "Already exists, opening: $file" -ForegroundColor Yellow
}
else {
    Push-Location $root
    & $hugo new "logs/$Date.md"
    $code = $LASTEXITCODE
    Pop-Location

    if ($code -ne 0 -or -not (Test-Path $file)) {
        Write-Host "Failed to create $file" -ForegroundColor Red
        exit 1
    }
    Write-Host "Created: $file" -ForegroundColor Green
}

if (-not $NoOpen) {
    Start-Process notepad.exe -ArgumentList "`"$file`""
}
