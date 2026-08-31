# Start Mix Studio API (run from workspace root)
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
. "$Root\activate.ps1"
python -m uvicorn server.main:app --reload --host 127.0.0.1 --port 8010
