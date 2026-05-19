Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

python -m pip install --user pyyaml
Write-Host "Installed Python dependency: pyyaml"
Write-Host "ROS dependency and colcon build steps should be run inside ROS-enabled Linux/WSL/container environments."
