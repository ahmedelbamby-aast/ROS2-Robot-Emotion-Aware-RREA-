Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

$reserved = (python scripts/lib_config.py get ngrok.reserved_tcp_addr).Trim()
New-Item -ItemType Directory -Force runtime | Out-Null

if (-not [string]::IsNullOrWhiteSpace($reserved)) {
    $parts = $reserved.Split(":")
    if ($parts.Count -ne 2) {
        throw "Invalid ngrok.reserved_tcp_addr format. Expected host:port."
    }
    "NGROK_HOST=$($parts[0])" | Out-File -Encoding utf8 runtime/ngrok.env
    "NGROK_PORT=$($parts[1])" | Out-File -Encoding utf8 -Append runtime/ngrok.env
    Write-Host "Using reserved ngrok endpoint: $reserved"
    exit 0
}

$resp = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -Method Get
$tcpTunnel = $resp.tunnels | Where-Object { $_.proto -eq "tcp" } | Select-Object -First 1
if ($null -eq $tcpTunnel -or [string]::IsNullOrWhiteSpace($tcpTunnel.public_url)) {
    throw "No tcp tunnel found in ngrok API."
}

$endpoint = $tcpTunnel.public_url -replace "^tcp://", ""
$parts = $endpoint.Split(":")
if ($parts.Count -ne 2) {
    throw "Invalid ngrok endpoint format: $endpoint"
}
"NGROK_HOST=$($parts[0])" | Out-File -Encoding utf8 runtime/ngrok.env
"NGROK_PORT=$($parts[1])" | Out-File -Encoding utf8 -Append runtime/ngrok.env
Write-Host "Ephemeral ngrok endpoint: $endpoint"
