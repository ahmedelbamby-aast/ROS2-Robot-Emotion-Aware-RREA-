Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

$backend = (python scripts/lib_config.py get inference.backend).Trim()

docker build -f docker/Dockerfile.base -t emotion_robot_base:latest .
docker compose -f docker/docker-compose.yml build robot laptop

if ($backend -eq "openvino") {
    docker build -f docker/Dockerfile.openvino -t emotion_robot:openvino .
} elseif ($backend -eq "tensorrt") {
    docker build -f docker/Dockerfile.tensorrt -t emotion_robot:tensorrt .
} elseif ($backend -eq "cpu") {
    docker build -f docker/Dockerfile.cpu -t emotion_robot:cpu .
}

Write-Host "Build complete (backend=$backend)"
