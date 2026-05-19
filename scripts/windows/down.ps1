Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

docker compose -f docker/docker-compose.yml down --remove-orphans
Remove-Item -ErrorAction SilentlyContinue "runtime/ngrok.env"
