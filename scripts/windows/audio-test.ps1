Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

$service = if ($args.Count -ge 1) { $args[0] } else { "robot" }
$duration = if ($args.Count -ge 2) { $args[1] } else { "3" }

if ($service -ne "robot" -and $service -ne "laptop") {
    throw "Usage: .\scripts\windows\audio-test.ps1 [robot|laptop] [duration_seconds]"
}

Write-Host "[audio-test] service=$service duration=$duration`s"

$cid = (docker compose -f docker/docker-compose.yml ps -q $service).Trim()
if ([string]::IsNullOrWhiteSpace($cid)) {
    throw "service '$service' is not running"
}

docker compose -f docker/docker-compose.yml exec -T $service test -d /dev/snd 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "container $service does not have /dev/snd mapped. Re-run .\scripts\windows\up.ps1 on a host with /dev/snd in WSL."
}

Write-Host "[audio-test] capture device list"
docker compose -f docker/docker-compose.yml exec -T $service bash -lc "arecord -l || true"

Write-Host "[audio-test] playback device list"
docker compose -f docker/docker-compose.yml exec -T $service bash -lc "aplay -l || true"

Write-Host "[audio-test] recording /tmp/mic_test.wav"
docker compose -f docker/docker-compose.yml exec -T $service bash -lc "arecord -q -d $duration -f cd -t wav /tmp/mic_test.wav"

Write-Host "[audio-test] playing /tmp/mic_test.wav"
docker compose -f docker/docker-compose.yml exec -T $service bash -lc "aplay -q /tmp/mic_test.wav"

Write-Host "[audio-test] success"
