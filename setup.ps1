# Requires -Version 5.1
param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

function Write-Section($text) {
    Write-Host "`n=== $text ===" -ForegroundColor Cyan
}

function Assert-Command($name, $hint) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        throw "Missing: $name. Hint: $hint"
    }
}

# 1) Checks
Write-Section "Environment check"
Assert-Command python "Install Python 3.9+ from https://www.python.org/downloads/ and put in PATH"
Assert-Command node "Install Node.js LTS from https://nodejs.org/en/download/"
Assert-Command npm "npm is installed with Node.js"

# 2) Backend: venv + pip install
Write-Section "Backend dependencies (Python)"
$backendPath = Join-Path $PSScriptRoot 'backend'
$venvPath = Join-Path $backendPath '.venv'
if ((Test-Path $venvPath) -and $Force) {
    Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $venvPath
}
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..."
    python -m venv $venvPath | Out-Null
}

$pip = Join-Path $venvPath 'Scripts/pip.exe'
$pythonExe = Join-Path $venvPath 'Scripts/python.exe'

& $pip install --upgrade pip wheel setuptools
& $pip install -r (Join-Path $backendPath 'requirements.txt')

# 3) Frontend: npm ci
Write-Section "Frontend dependencies (Node)"
$frontendPath = Join-Path $PSScriptRoot 'react-ts-vite-tailwind'
Push-Location $frontendPath
try {
    if (Test-Path 'package-lock.json') {
        npm ci
    } else {
        npm install
    }
}
finally {
    Pop-Location
}

Write-Section "Done"
Write-Host "Backend venv: $venvPath" -ForegroundColor Green
Write-Host "How to run:" -ForegroundColor Green
Write-Host ("1) Activate venv (PowerShell): {0}\Scripts\Activate.ps1" -f $venvPath) -ForegroundColor Gray
Write-Host ("   or (cmd.exe): {0}\Scripts\activate.bat" -f $venvPath) -ForegroundColor Gray
Write-Host "2) Run backend: python .\backend\Beta.py" -ForegroundColor Gray
Write-Host "3) Run frontend dev server (in another console)" -ForegroundColor Gray
Write-Host "   cd .\react-ts-vite-tailwind && npm run dev" -ForegroundColor Gray

Write-Host "Reinstall from scratch: .\setup.ps1 -Force" -ForegroundColor DarkGray 