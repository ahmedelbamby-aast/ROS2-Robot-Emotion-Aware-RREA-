Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

Write-Host "[doctor] docker"
docker --version
docker compose version

Write-Host "[doctor] config"
$mode = (python scripts/lib_config.py get deployment.mode).Trim()
$transport = (python scripts/lib_config.py get gateway.transport).Trim()
$backend = (python scripts/lib_config.py get inference.backend).Trim()
Write-Host "mode=$mode transport=$transport backend=$backend"

Write-Host "[doctor] model dir"
if (Test-Path "models") {
    Write-Host "models/ exists"
} else {
    throw "models/ missing"
}

Write-Host "[doctor] audio host checks"
$hasHostSnd = $false
if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
    try {
        wsl.exe test -d /dev/snd
        if ($LASTEXITCODE -eq 0) {
            $hasHostSnd = $true
            Write-Host "/dev/snd exists in default WSL distro"
        }
    } catch {
        $hasHostSnd = $false
    }
}
if (-not $hasHostSnd) {
    Write-Host "/dev/snd not detected via WSL (container audio I/O likely unavailable)"
}

Write-Host "[doctor] ngrok checks"
if ($transport -eq "ngrok_tcp") {
    $tokenVar = (python scripts/lib_config.py get ngrok.authtoken_env).Trim()
    $token = [Environment]::GetEnvironmentVariable($tokenVar)
    if ([string]::IsNullOrWhiteSpace($token)) {
        throw "missing $tokenVar"
    }
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -Method Get | Out-Null
        Write-Host "ngrok api reachable"
    } catch {
        Write-Host "ngrok api not reachable yet"
    }
}

Write-Host "[doctor] backend/runtime checks"
$dockerInfo = docker info 2>$null
$hasNvidia = ($dockerInfo | Select-String -Pattern "nvidia" -SimpleMatch -CaseSensitive:$false) -ne $null
$hasOpenvino = (docker images --format '{{.Repository}}:{{.Tag}}' | Select-String -Pattern '^emotion_robot:openvino$') -ne $null

$selected = $backend
if ($backend -eq "auto") {
    if ($hasNvidia) {
        $selected = "tensorrt"
    } elseif ($hasOpenvino) {
        $selected = "openvino"
    } else {
        $selected = "cpu"
    }
    Write-Host "auto backend resolved to: $selected"
}

if ($backend -eq "tensorrt" -and -not $hasNvidia) {
    throw "tensorrt selected but nvidia runtime not detected"
}
if ($backend -eq "openvino" -and -not $hasOpenvino) {
    throw "openvino selected but emotion_robot:openvino image is not built"
}

Write-Host "[doctor] audio container checks"
foreach ($service in @("robot", "laptop")) {
    $cid = (docker compose -f docker/docker-compose.yml ps -q $service).Trim()
    if ([string]::IsNullOrWhiteSpace($cid)) {
        Write-Host "$service`: not running"
        continue
    }

    docker compose -f docker/docker-compose.yml exec -T $service test -d /dev/snd 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "$service`: /dev/snd mapped"
    } else {
        Write-Host "$service`: /dev/snd not mapped"
    }
}

Write-Host "doctor completed"
