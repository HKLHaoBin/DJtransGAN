# Start Mix Studio Vue dev server
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $Root "web")
if (-not (Test-Path "node_modules")) {
  npm install
}
npm run dev
