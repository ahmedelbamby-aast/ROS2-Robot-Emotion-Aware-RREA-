Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

& "$PSScriptRoot/clean.ps1"
& "$PSScriptRoot/build.ps1"
