Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

$paths = @(
    "ros2_ws/build",
    "ros2_ws/install",
    "ros2_ws/log",
    "runtime/ngrok.env"
)

foreach ($path in $paths) {
    if (Test-Path $path) {
        Remove-Item -Recurse -Force $path
    }
}
