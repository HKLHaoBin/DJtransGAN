# Activate this workspace (PowerShell)
# All caches stay under F:\编程\DJtransGAN (pip/torch); build temp uses F:\djtransgan-tmp
# because Chinese path segments break some sdist unpacking on Windows.

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

. "$Root\.venv\Scripts\Activate.ps1"

$env:PIP_CACHE_DIR      = Join-Path $Root ".cache\pip"
$env:TORCH_HOME         = Join-Path $Root ".cache\torch"
$env:HF_HOME            = Join-Path $Root ".cache\huggingface"
$env:PYTHONNOUSERSITE   = "1"
$env:TMP                = "F:\djtransgan-tmp"
$env:TEMP               = "F:\djtransgan-tmp"
$env:TMPDIR             = "F:\djtransgan-tmp"

New-Item -ItemType Directory -Force -Path $env:PIP_CACHE_DIR, $env:TORCH_HOME, $env:HF_HOME, $env:TMP | Out-Null

Write-Host "DJtransGAN env active"
Write-Host "  root: $Root"
Write-Host "  python: $((Get-Command python).Source)"
Write-Host "  PIP_CACHE_DIR=$env:PIP_CACHE_DIR"
Write-Host "  TORCH_HOME=$env:TORCH_HOME"
