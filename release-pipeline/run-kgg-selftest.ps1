$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
$Gate = Join-Path $ScriptDir "kgg_selftest_build.py"
$Mode = if ($args.Count -gt 0) { [string]$args[0] } else { "--smart" }

Push-Location $RepoRoot
try {
    python $Gate $Mode
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
