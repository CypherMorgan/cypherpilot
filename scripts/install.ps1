<#
.SYNOPSIS
    CypherPilot — Install / Uninstall Script (Windows)
.DESCRIPTION
    One-command install of CypherPilot with full inline progress.

    Install:
        irm https://raw.githubusercontent.com/CypherMorgan/cypherpilot/main/scripts/install.ps1 | iex

    Uninstall:
        $env:CYPHERPILOT_UNINSTALL = "1"; irm https://raw.githubusercontent.com/CypherMorgan/cypherpilot/main/scripts/install.ps1 | iex

    Or run locally:
        .\scripts\install.ps1          # Install
        .\scripts\install.ps1 -Uninstall  # Remove
.PARAMETER Uninstall
    Switch to run in uninstall mode.
#>

param([switch]$Uninstall)

# ── Configuration ────────────────────────────────────────────────────────────
$RepoUrl     = "https://github.com/CypherMorgan/cypherpilot.git"
$Branch      = "master"
$InstallDir  = if ($env:CYPHERPILOT_HOME) { $env:CYPHERPILOT_HOME } else { "$env:USERPROFILE\.cypherpilot" }
$Version     = "0.5.2"

# ── Colors (PowerShell 5+ compatible) ───────────────────────────────────────
$Host.UI.RawUI.ForegroundColor = "White"
function Write-Step    { Write-Host "`n── $args ──" -ForegroundColor White }
function Write-Info    { Write-Host "==> " -ForegroundColor Cyan -NoNewline; Write-Host $args }
function Write-Ok      { Write-Host "  ✓ " -ForegroundColor Green -NoNewline; Write-Host $args }
function Write-Warn    { Write-Host "  ⚠ " -ForegroundColor Yellow -NoNewline; Write-Host $args }
function Write-Err     { Write-Host "  ✗ " -ForegroundColor Red -NoNewline; Write-Host $args }

# ── Helper: check a command exists ──────────────────────────────────────────
function Test-Command($cmd) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        Write-Ok "$cmd found: $(Get-Command $cmd | Select-Object -ExpandProperty Source)"
        return $true
    }
    Write-Err "'$cmd' is required but not installed."
    switch ($cmd) {
        'python'  { Write-Info "Install Python 3.11+ from https://www.python.org/downloads/" }
        'node'    { Write-Info "Install Node.js 18+ from https://nodejs.org/" }
        'npm'     { Write-Info "npm comes with Node.js — install from https://nodejs.org/" }
        'git'     { Write-Info "Install git from https://git-scm.com/downloads/win" }
    }
    return $false
}

# ── Install ──────────────────────────────────────────────────────────────────
function Install-CypherPilot {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor White
    Write-Host "║        CypherPilot v$Version — Installer           ║" -ForegroundColor White
    Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor White
    Write-Host ""

    # ── Step 1: Check prerequisites ─────────────────────────────────────────
    Write-Step "Checking prerequisites"

    $allOk = $true
    foreach ($cmd in @('python', 'git', 'node', 'npm')) {
        if (-not (Test-Command $cmd)) { $allOk = $false }
    }
    if (-not $allOk) { exit 1 }

    # Verify Python version
    $pyVer = python --version 2>&1
    Write-Ok "Python: $pyVer"

    # ── Step 2: Clone / update repository ───────────────────────────────────
    Write-Step "Getting CypherPilot source"

    if (Test-Path $InstallDir) {
        Write-Info "Updating existing installation in $InstallDir"
        Push-Location $InstallDir
        git fetch origin $Branch
        git reset --hard "origin/$Branch"
        Pop-Location
        Write-Ok "Repository updated"
    } else {
        Write-Info "Cloning into $InstallDir"
        git clone --depth 1 --branch $Branch $RepoUrl $InstallDir
        Write-Ok "Repository cloned"
    }

    # ── Step 3: Python virtual environment ──────────────────────────────────
    Write-Step "Setting up Python environment"

    $venvPath = "$InstallDir\.venv"
    if (Test-Path $venvPath) {
        Write-Info "Removing existing virtual environment..."
        Remove-Item -Recurse -Force $venvPath
    }

    Write-Info "Creating virtual environment..."
    python -m venv $venvPath
    Write-Ok "Virtual environment created"

    # Activate & upgrade pip
    $pip = "$venvPath\Scripts\pip.exe"
    $python = "$venvPath\Scripts\python.exe"

    Write-Info "Upgrading pip..."
    & $pip install --upgrade pip --quiet 2>&1 | Select-Object -Last 1
    Write-Ok "pip upgraded"

    # Install dependencies
    Write-Info "Installing Python dependencies..."
    Push-Location $InstallDir
    & $pip install --no-cache -e "$InstallDir" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Python dependency installation failed"
        Pop-Location
        exit 1
    }
    Pop-Location
    Write-Ok "Python dependencies installed"

    # ── Step 4: Frontend ────────────────────────────────────────────────────
    Write-Step "Building frontend"

    Push-Location "$InstallDir\frontend"
    Write-Info "Installing frontend dependencies..."
    npm install --silent 2>&1 | Select-Object -Last 1
    Write-Ok "Frontend dependencies installed"

    Write-Info "Building production bundle..."
    npm run build 2>&1 | Select-Object -Last 1
    Write-Ok "Frontend built"
    Pop-Location

    # ── Step 5: Database ────────────────────────────────────────────────────
    Write-Step "Setting up database"

    Push-Location $InstallDir
    $envPath = "$InstallDir\.env"
    if (-not (Test-Path $envPath)) {
        Write-Info "Creating .env from .env.example (SQLite by default)"
        Copy-Item ".env.example" ".env"
        # Switch to SQLite
        (Get-Content ".env") -replace 'postgresql\+asyncpg://.*', 'sqlite+aiosqlite:///./cypherpilot.db' | Set-Content ".env"
        (Get-Content ".env") -replace 'postgresql://.*', 'sqlite:///./cypherpilot.db' | Set-Content ".env"
        Write-Ok ".env created with SQLite"
    } else {
        Write-Info ".env already exists, keeping it"
    }

    Write-Info "Running database migrations..."
    & $python -m alembic upgrade head 2>&1
    Write-Ok "Database ready"
    Pop-Location

    # ── Step 6: Create start script ─────────────────────────────────────────
    Write-Step "Creating start shortcuts"

    # Create a batch file for easy launching
@"
@echo off
cd /d "$InstallDir"
call "$venvPath\Scripts\activate.bat"
uvicorn app.main:app --host 0.0.0.0 --port 8000
"@ | Out-File -FilePath "$InstallDir\start.bat" -Encoding ASCII
    Write-Ok "Created $InstallDir\start.bat — double-click to run CypherPilot"

    # Create uninstall batch file
@"
@echo off
echo Removing CypherPilot...
rmdir /s /q "$InstallDir"
echo CypherPilot has been removed.
pause
"@ | Out-File -FilePath "$InstallDir\uninstall.bat" -Encoding ASCII

    # Add to PATH for current user
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -notlike "*$InstallDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$userPath;$InstallDir", "User")
        Write-Ok "Added $InstallDir to user PATH"
    }

    # ── Summary ─────────────────────────────────────────────────────────────
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor White
    Write-Host "║          CypherPilot v$Version installed!           ║" -ForegroundColor White
    Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor White
    Write-Host ""
    Write-Host "  Install path:     $InstallDir" -ForegroundColor White
    Write-Host "  Python venv:      $venvPath" -ForegroundColor White
    Write-Host "  Config:           $InstallDir\.env" -ForegroundColor White
    Write-Host ""
    Write-Host "  Quick start:" -ForegroundColor White
    Write-Host "    Double-click: $InstallDir\start.bat"
    Write-Host "    Or run:       cd $InstallDir && .venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
    Write-Host ""
    Write-Host "  Open in browser:  http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  API docs:         http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  To uninstall:     Double-click $InstallDir\uninstall.bat" -ForegroundColor White
    Write-Host ""
}

# ── Uninstall ────────────────────────────────────────────────────────────────
function Uninstall-CypherPilot {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor White
    Write-Host "║         CypherPilot — Uninstall                       ║" -ForegroundColor White
    Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor White
    Write-Host ""

    if (-not (Test-Path $InstallDir)) {
        Write-Warn "No installation found at $InstallDir"
        exit 0
    }

    # ── Remove from PATH ───────────────────────────────────────────────────
    Write-Step "Removing from PATH"
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -like "*$InstallDir*") {
        $newPath = ($userPath -split ';' | Where-Object { $_ -ne $InstallDir }) -join ';'
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Ok "Removed from user PATH"
    }

    # ── Remove files ───────────────────────────────────────────────────────
    Write-Step "Removing installed files"
    Write-Info "Removing $InstallDir ..."

    $confirm = Read-Host "Remove everything under '$InstallDir'? [y/N] "
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Warn "Uninstall cancelled."
        exit 0
    }

    Remove-Item -Recurse -Force $InstallDir -ErrorAction SilentlyContinue
    Write-Ok "Removed $InstallDir"

    # ── Verify ──────────────────────────────────────────────────────────────
    Write-Step "Verifying clean removal"
    if (Test-Path $InstallDir) {
        Write-Err "Directory still exists: $InstallDir"
        Write-Warn "Close any programs using the directory and try again."
    } else {
        Write-Host ""
        Write-Host "  ✓ CypherPilot has been completely removed." -ForegroundColor Green
        Write-Host "    Restart your terminal to clear PATH changes." -ForegroundColor White
        Write-Host ""
    }
}

# ── Main ─────────────────────────────────────────────────────────────────────

if ($Uninstall -or $env:CYPHERPILOT_UNINSTALL) {
    Uninstall-CypherPilot
} else {
    Install-CypherPilot
}
