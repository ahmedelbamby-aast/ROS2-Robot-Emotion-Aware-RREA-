Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

$mode = (python scripts/lib_config.py get deployment.mode).Trim()
$transport = (python scripts/lib_config.py get gateway.transport).Trim()
$port = (python scripts/lib_config.py get gateway.port).Trim()
$host = (python scripts/lib_config.py get gateway.local_host).Trim()
$useEphemeral = (python scripts/lib_config.py get ngrok.use_ephemeral_tcp).Trim()
$tokenVar = (python scripts/lib_config.py get ngrok.authtoken_env).Trim()

$env:GATEWAY_PORT = $port

$audioOverrideFile = "runtime/docker-compose.audio.yml"
$composeArgs = @("-f", "docker/docker-compose.yml")
$hasHostSnd = $false

if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
    try {
        wsl.exe test -d /dev/snd
        if ($LASTEXITCODE -eq 0) {
            $hasHostSnd = $true
        }
    } catch {
        $hasHostSnd = $false
    }
}

if ($hasHostSnd) {
    @"
services:
  robot:
    devices:
      - /dev/snd:/dev/snd
  laptop:
    devices:
      - /dev/snd:/dev/snd
"@ | Set-Content -Path $audioOverrideFile -Encoding ascii
    $composeArgs += @("-f", $audioOverrideFile)
    Write-Host "Audio mapping enabled: /dev/snd"
} else {
    Remove-Item -ErrorAction SilentlyContinue $audioOverrideFile
    Write-Host "Audio mapping skipped: /dev/snd not available from WSL host"
}

if ($mode -eq "robot_only") {
    docker compose -f docker/docker-compose.yml stop laptop ngrok | Out-Null
    docker compose @composeArgs --profile robot up -d robot
    Remove-Item -ErrorAction SilentlyContinue "runtime/ngrok.env"
    Write-Host "Started robot_only path. Launch: ros2 launch emotion_robot_bringup robot_only.launch.py"
    exit 0
}

docker compose @composeArgs --profile robot --profile laptop up -d robot laptop

if ($transport -eq "local_tcp") {
    docker compose -f docker/docker-compose.yml stop ngrok | Out-Null
    Remove-Item -ErrorAction SilentlyContinue "runtime/ngrok.env"
    Write-Host "Laptop offload local tcp target: $host`:$port"
    Write-Host "Set ROBOT_GATEWAY_HOST=$host before robot endpoint launch."
    exit 0
}

$token = [Environment]::GetEnvironmentVariable($tokenVar)
if ([string]::IsNullOrWhiteSpace($token)) {
    throw "Missing required ngrok token env var: $tokenVar"
}

$env:NGROK_AUTHTOKEN = $token
docker compose -f docker/docker-compose.yml --profile ngrok up -d ngrok

if ($useEphemeral -eq "true") {
    & "$PSScriptRoot/ngrok-url.ps1"
}

Write-Host "Laptop offload ngrok ready. Launch laptop and robot endpoint launch files."
