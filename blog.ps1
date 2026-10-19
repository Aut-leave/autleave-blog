# blog.ps1 - Autleave blog workspace
#
#   .\blog.ps1                interactive menu
#   .\blog.ps1 log [date]     new daily log   (date like 2026-10-19, default today)
#   .\blog.ps1 post [title]   new article
#   .\blog.ps1 publish        commit and push
#   .\blog.ps1 sync           sync Obsidian notes
#   .\blog.ps1 rules          edit publish rules
#   .\blog.ps1 serve          local preview on 1313
#   .\blog.ps1 status         repo status

param(
    [Parameter(Position = 0)]
    [string]$Command = 'menu',
    [Parameter(Position = 1)]
    [string]$Arg1
)

$ErrorActionPreference = 'Stop'

# Decode native command output (python/git) as UTF-8, otherwise Chinese is garbled
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$Root = $PSScriptRoot
$Hugo = Join-Path (Split-Path $Root -Parent) '.tools\hugo.exe'
$RulesFile = Join-Path $Root 'sync\rules.json'
$SyncPy = Join-Path $Root 'sync-notes.py'
$SiteUrl = 'https://autleave.top'

# ---------------------------------------------------------------- helpers
function Write-Section($Text) {
    Write-Host ''
    Write-Host "== $Text ==" -ForegroundColor Cyan
}

function Pause-Any {
    Write-Host ''
    [void](Read-Host 'Press Enter to continue')
}

function Get-Editor {
    $c = Get-Command code -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    return $null
}

function Open-File($Path) {
    $editor = Get-Editor
    if ($editor) { & $editor $Path } else { Start-Process notepad.exe -ArgumentList "`"$Path`"" }
}

function Invoke-Python {
    param([string[]]$PyArgs)

    $c = Get-Command python -ErrorAction SilentlyContinue
    if ($c) { & $c.Source @PyArgs | Out-Host; return $LASTEXITCODE }
    $c = Get-Command py -ErrorAction SilentlyContinue
    if ($c) { & $c.Source -3 @PyArgs | Out-Host; return $LASTEXITCODE }
    $b = Join-Path $env:LOCALAPPDATA 'Programs\DSH Desktop\resources\office-runtime\primary-runtime\dependencies\python\python.exe'
    if (Test-Path $b) { & $b @PyArgs | Out-Host; return $LASTEXITCODE }

    Write-Host 'Python not found. Install Python or add it to PATH.' -ForegroundColor Red
    return 1
}

function New-HugoFile($Type, $Slug) {
    if (-not (Test-Path $Hugo)) {
        Write-Host "Hugo not found: $Hugo" -ForegroundColor Red
        return $false
    }
    Push-Location $Root
    try { & $Hugo new "$Type/$Slug.md" | Out-Null } finally { Pop-Location }
    return ($LASTEXITCODE -eq 0)
}

# ---------------------------------------------------------------- commands
function Invoke-Log {
    param([string]$Date)

    if (-not $Date) { $Date = Get-Date -Format 'yyyy-MM-dd' }
    $file = Join-Path $Root "content\logs\$Date.md"

    if (Test-Path $file) {
        Write-Host "Already exists: content\logs\$Date.md" -ForegroundColor Yellow
    }
    else {
        if (-not (New-HugoFile 'logs' $Date)) { Write-Host 'Create failed.' -ForegroundColor Red; return }
        Write-Host "Created: content\logs\$Date.md" -ForegroundColor Green
    }
    Open-File $file
}

function Invoke-Post {
    param([string]$Title)

    if (-not $Title) {
        $Title = Read-Host 'Post title (used as filename)'
    }
    if (-not $Title) { return }

    $slug = $Title -replace '[\\/:*?"<>|]', ''
    $slug = ($slug -replace '\s+', '-').Trim('-').ToLower()

    $file = Join-Path $Root "content\posts\$slug.md"
    if (Test-Path $file) {
        Write-Host "Already exists: content\posts\$slug.md" -ForegroundColor Yellow
    }
    else {
        if (-not (New-HugoFile 'posts' $slug)) { Write-Host 'Create failed.' -ForegroundColor Red; return }
        Write-Host "Created: content\posts\$slug.md" -ForegroundColor Green
    }
    Open-File $file
}

function Invoke-Publish {
    Push-Location $Root
    try {
        $raw = @(& git -c core.quotepath=false status --porcelain)
        if ($raw.Count -eq 0) {
            Write-Host 'Nothing to commit.' -ForegroundColor Yellow
            return
        }

        $added = @(); $changed = @(); $deleted = @()
        foreach ($line in $raw) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            $code = $line.Substring(0, 2)
            $path = $line.Substring(3)

            if ($code -eq '??' -or $code -match 'A') { $added += $path }
            elseif ($code -match 'D') { $deleted += $path }
            else { $changed += $path }
        }

        Write-Section 'Changes to publish'
        foreach ($p in $added) { Write-Host "  [new]     $p" -ForegroundColor Green }
        foreach ($p in $changed) { Write-Host "  [changed] $p" }
        foreach ($p in $deleted) { Write-Host "  [deleted] $p" -ForegroundColor DarkGray }

        $noteAdds = @($added | Where-Object { $_ -like 'content/notes/*' -and $_ -notlike '*_index.md' })
        if ($noteAdds.Count -gt 0) {
            Write-Host ''
            Write-Host "WARNING: $($noteAdds.Count) new note file(s) will be public." -ForegroundColor Yellow
            $ok = Read-Host 'Confirm these are safe to publish? (y/N)'
            if ($ok -ne 'y') { Write-Host 'Cancelled.' -ForegroundColor Yellow; return }
        }

        $default = 'update ' + (Get-Date -Format 'yyyy-MM-dd HH:mm')
        $msg = Read-Host "Commit message [$default]"
        if ([string]::IsNullOrWhiteSpace($msg)) { $msg = $default }

        Write-Host ''
        & git add -A
        & git commit -m $msg | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Host 'Commit failed.' -ForegroundColor Red; return }

        Write-Host 'Pushing...' -ForegroundColor Cyan
        $pushOut = & git push 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host 'Push failed:' -ForegroundColor Red
            $pushOut | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
            Write-Host ''
            Write-Host 'Hint: is the proxy running on 127.0.0.1:2080?' -ForegroundColor Yellow
            return
        }

        Write-Host 'Pushed.' -ForegroundColor Green
        Write-Host "Live in ~1 min: $SiteUrl" -ForegroundColor Cyan
    }
    finally {
        Pop-Location
    }
}

function Invoke-Sync {
    if (-not (Test-Path $SyncPy)) { Write-Host 'sync-notes.py not found.' -ForegroundColor Red; return }

    $rc = Invoke-Python @($SyncPy)
    if ($rc -ne 0) { Write-Host 'Sync preview failed.' -ForegroundColor Red; return }

    Write-Host ''
    $ans = Read-Host 'Write these files? (y/N)'
    if ($ans -eq 'y') {
        Invoke-Python @($SyncPy, '--write') | Out-Null
        Write-Host 'Done. Run publish to push them.' -ForegroundColor Green
    }
    else {
        Write-Host 'Cancelled, nothing written.' -ForegroundColor Yellow
    }
}

function Invoke-Rules {
    if (-not (Test-Path $RulesFile)) { Write-Host 'sync/rules.json not found.' -ForegroundColor Red; return }

    Write-Host 'Editing sync/rules.json' -ForegroundColor Cyan
    Write-Host '  default : private | public' -ForegroundColor DarkGray
    Write-Host '  include : folders that publish automatically' -ForegroundColor DarkGray
    Write-Host '  exclude : folders/patterns that never publish' -ForegroundColor DarkGray
    Write-Host '  a note with "publish: false" in front matter is always private' -ForegroundColor DarkGray
    Open-File $RulesFile
    Write-Host ''
    [void](Read-Host 'Save the file, then press Enter to preview the result')

    Write-Section 'Preview (nothing written yet)'
    Invoke-Python @($SyncPy)
}

function Invoke-Serve {
    $busy = Get-NetTCPConnection -LocalPort 1313 -ErrorAction SilentlyContinue
    if ($busy) {
        Write-Host 'Port 1313 is already in use.' -ForegroundColor Yellow
        Write-Host 'Open http://localhost:1313 , or stop the running server first.' -ForegroundColor Yellow
        return
    }
    if (-not (Test-Path $Hugo)) { Write-Host "Hugo not found: $Hugo" -ForegroundColor Red; return }

    Write-Host 'Starting preview... open http://localhost:1313  (Ctrl+C to stop)' -ForegroundColor Cyan
    Push-Location $Root
    try { & $Hugo server -D } finally { Pop-Location }
}

function Invoke-Status {
    Push-Location $Root
    try {
        $branch = (& git status -sb | Select-Object -First 1)
        Write-Section 'Repository'
        Write-Host "  $branch"

        $changed = @(& git -c core.quotepath=false status --porcelain)
        $changed = @($changed | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        Write-Host "  uncommitted files: $($changed.Count)"

        $last = (& git log -1 --pretty='%h %s (%cr)')
        Write-Host "  last commit: $last"

        $ahead = (& git rev-list --count '@{u}..HEAD' 2>$null)
        if ($ahead) { Write-Host "  commits not pushed: $ahead" -ForegroundColor Yellow }

        Write-Section 'Site'
        Write-Host "  local:  http://localhost:1313"
        Write-Host "  live:   $SiteUrl"
    }
    finally {
        Pop-Location
    }
}

# ---------------------------------------------------------------- menu
function Show-Menu {
    while ($true) {
        Clear-Host
        Write-Host '===== Autleave blog =====' -ForegroundColor Cyan
        Write-Host ''
        Write-Host '  1. New daily log'
        Write-Host '  2. New article'
        Write-Host '  3. Publish (commit + push)'
        Write-Host '  4. Sync Obsidian notes'
        Write-Host '  5. Edit publish rules'
        Write-Host '  6. Local preview'
        Write-Host '  7. Status'
        Write-Host '  0. Exit'
        Write-Host ''
        $choice = Read-Host 'Choose'

        switch ($choice) {
            '1' { Invoke-Log; Pause-Any }
            '2' { Invoke-Post; Pause-Any }
            '3' { Invoke-Publish; Pause-Any }
            '4' { Invoke-Sync; Pause-Any }
            '5' { Invoke-Rules; Pause-Any }
            '6' { Invoke-Serve }
            '7' { Invoke-Status; Pause-Any }
            '0' { return }
            default { }
        }
    }
}

# ---------------------------------------------------------------- dispatch
switch ($Command.ToLower()) {
    'menu' { Show-Menu }
    'log' { Invoke-Log $Arg1 }
    'post' { Invoke-Post $Arg1 }
    'publish' { Invoke-Publish }
    'sync' { Invoke-Sync }
    'allow' { Invoke-Rules }
    'rules' { Invoke-Rules }
    'serve' { Invoke-Serve }
    'status' { Invoke-Status }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host 'Try: log | post | publish | sync | rules | serve | status'
    }
}
