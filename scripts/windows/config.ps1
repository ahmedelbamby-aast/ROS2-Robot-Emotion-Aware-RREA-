Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

if ($args.Count -eq 0) {
    throw "Usage: .\scripts\windows\config.ps1 set <key> <value> | get <key>"
}

$cmd = $args[0]
if ($cmd -eq "set") {
    if ($args.Count -ne 3) {
        throw "Usage: .\scripts\windows\config.ps1 set <key> <value>"
    }
    python scripts/lib_config.py set $args[1] $args[2]
} elseif ($cmd -eq "get") {
    if ($args.Count -ne 2) {
        throw "Usage: .\scripts\windows\config.ps1 get <key>"
    }
    python scripts/lib_config.py get $args[1]
} else {
    throw "Unknown command: $cmd"
}
