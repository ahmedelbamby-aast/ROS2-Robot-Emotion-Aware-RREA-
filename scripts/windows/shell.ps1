Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

$service = if ($args.Count -gt 0) { $args[0] } else { "robot" }
docker compose -f docker/docker-compose.yml exec $service bash
