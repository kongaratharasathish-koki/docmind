# setup_env.ps1
#
# DocMind Environment Setup Script
# Creates a virtual environment with Python 3.11 and correct dependency versions.

param(
    [string]$PythonExe = "C:\Users\User\AppData\Local\Programs\Python\Python311\python.exe"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DocMind Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python installation
Write-Host "[1/6] Checking Python..." -ForegroundColor Yellow

if (-not (Test-Path $PythonExe)) {
    Write-Host "ERROR: Python executable not found at $PythonExe" -ForegroundColor Red
    exit 1
}

$pyVersionOutput = & $PythonExe --version 2>&1
Write-Host "Found $pyVersionOutput"

Write-Host "Python executable: $PythonExe" -ForegroundColor Green
Write-Host ""

# Step 2: Create virtual environment
Write-Host "[2/6] Creating virtual environment..." -ForegroundColor Yellow

if (Test-Path ".venv") {
    Write-Host "Removing existing .venv..." -ForegroundColor Yellow
    Remove-Item -Path ".venv" -Recurse -Force
}

& $PythonExe -m venv .venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor Red
    exit 1
}

Write-Host "Virtual environment created at .\.venv" -ForegroundColor Green
Write-Host ""

# Step 3: Activate virtual environment
Write-Host "[3/6] Activating virtual environment..." -ForegroundColor Yellow

$venvPath = Join-Path $PSScriptRoot ".venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $activateScript)) {
    Write-Host "ERROR: Activation script not found at $activateScript" -ForegroundColor Red
    exit 1
}

. $activateScript
Write-Host "Virtual environment activated." -ForegroundColor Green
Write-Host ""

# Step 4: Upgrade pip
Write-Host "[4/6] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet 2>&1 | Out-Null
Write-Host ""

# Step 5: Install dependencies
Write-Host "[5/6] Installing dependencies from requirements.txt..." -ForegroundColor Yellow

$requirementsPath = Join-Path $PSScriptRoot "requirements.txt"
if (-not (Test-Path $requirementsPath)) {
    Write-Host "ERROR: requirements.txt not found at $requirementsPath" -ForegroundColor Red
    exit 1
}

pip install -r $requirementsPath 2>&1 | ForEach-Object {
    Write-Host "  $_" -ForegroundColor Gray
}

Write-Host "Dependencies installed." -ForegroundColor Green
Write-Host ""

# Step 6: Verify installation
Write-Host "[6/6] Verifying installation..." -ForegroundColor Yellow
Write-Host ""

$checks = @(
    @{ Name = "langchain";       Import = "import langchain; print(langchain.__version__)" },
    @{ Name = "faiss";           Import = "import faiss; print('FAISS OK')" },
    @{ Name = "google-generativeai"; Import = "import google.generativeai; print('Gemini OK')" },
    @{ Name = "streamlit";       Import = "import streamlit; print('Streamlit OK')" },
    @{ Name = "fastapi";         Import = "import fastapi; print('FastAPI OK')" },
    @{ Name = "uvicorn";         Import = "import uvicorn; print('Uvicorn OK')" },
    @{ Name = "pydantic";        Import = "import pydantic; print('Pydantic OK')" },
    @{ Name = "supabase";        Import = "import supabase; print('Supabase OK')" },
    @{ Name = "python-jose";     Import = "import jose; print('JWT OK')" },
    @{ Name = "slowapi";         Import = "import slowapi; print('Rate Limiter OK')" }
)

$allPassed = $true
foreach ($check in $checks) {
    $output = python -c $check.Import 2>&1 | Out-String
    $output = $output.Trim()
    if ($output -match "ERROR|Traceback|ModuleNotFoundError") {
        Write-Host "  $($check.Name): FAILED" -ForegroundColor Red
        $output = $output -split "`n" | Select-Object -First 2 | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
        $allPassed = $false
    } else {
        Write-Host "  $($check.Name): $output" -ForegroundColor Green
    }
}

Write-Host ""
if (-not $allPassed) {
    Write-Host "WARNING: Some packages failed verification." -ForegroundColor Yellow
    Write-Host "Check the errors above and re-run setup." -ForegroundColor Yellow
} else {
    Write-Host "All checks passed!" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Environment Ready" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To activate the environment in future sessions:" -ForegroundColor White
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "Run Streamlit:" -ForegroundColor White
Write-Host "  streamlit run app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Run FastAPI:" -ForegroundColor White
Write-Host "  uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host ""
Write-Host "Swagger docs:" -ForegroundColor White
Write-Host "  http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
