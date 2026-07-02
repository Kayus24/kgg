$ErrorActionPreference = "Stop"

$BatteryArgs = @($args)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
$BatteryScript = Join-Path $ScriptDir "kgg_test_battery.py"
$CodexRuntime = Join-Path $HOME ".cache\codex-runtimes\codex-primary-runtime\dependencies"

function New-ToolCandidate {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [string[]]$Prefix = @(),
        [string[]]$VersionArgs = @("--version")
    )
    [pscustomobject]@{
        Command = $Command
        Prefix = $Prefix
        VersionArgs = $VersionArgs
    }
}

function Test-ToolCandidate {
    param([Parameter(Mandatory = $true)]$Candidate)
    try {
        & $Candidate.Command @($Candidate.VersionArgs) > $null 2> $null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Resolve-ToolSource {
    param([Parameter(Mandatory = $true)][string]$Command)
    if (Test-Path -LiteralPath $Command) {
        return (Resolve-Path -LiteralPath $Command).Path
    }
    $resolved = Get-Command $Command -ErrorAction SilentlyContinue
    if ($resolved) {
        return $resolved.Source
    }
    return $Command
}

function Select-Python {
    $candidates = @()
    $bundled = Join-Path $CodexRuntime "python\python.exe"
    if (Test-Path -LiteralPath $bundled) {
        $candidates += New-ToolCandidate -Command $bundled
    }
    if ($env:KGG_PYTHON) {
        $candidates += New-ToolCandidate -Command $env:KGG_PYTHON
    }
    if ($env:PYTHON) {
        $candidates += New-ToolCandidate -Command $env:PYTHON
    }
    $candidates += New-ToolCandidate -Command "python3"
    $candidates += New-ToolCandidate -Command "python"
    $candidates += New-ToolCandidate -Command "py" -Prefix @("-3") -VersionArgs @("-3", "--version")

    foreach ($candidate in $candidates) {
        if (Test-ToolCandidate $candidate) {
            return $candidate
        }
    }
    throw "No working Python found. Install Python or set KGG_PYTHON to python.exe."
}

function Select-Node {
    $candidates = @()
    $bundled = Join-Path $CodexRuntime "node\bin\node.exe"
    if (Test-Path -LiteralPath $bundled) {
        $candidates += New-ToolCandidate -Command $bundled
    }
    if ($env:KGG_NODE) {
        $candidates += New-ToolCandidate -Command $env:KGG_NODE
    }
    if ($env:NODE) {
        $candidates += New-ToolCandidate -Command $env:NODE
    }
    $candidates += New-ToolCandidate -Command "node"

    foreach ($candidate in $candidates) {
        if (Test-ToolCandidate $candidate) {
            return $candidate
        }
    }
    throw "No working Node.js found. Install Node.js or set KGG_NODE to node.exe."
}

function Select-Npm {
    $candidates = @()
    $bundledCmd = Join-Path $CodexRuntime "node\bin\npm.cmd"
    $bundledUnix = Join-Path $CodexRuntime "node\bin\npm"
    if (Test-Path -LiteralPath $bundledCmd) {
        $candidates += New-ToolCandidate -Command $bundledCmd
    }
    if (Test-Path -LiteralPath $bundledUnix) {
        $candidates += New-ToolCandidate -Command $bundledUnix
    }
    if ($env:KGG_NPM) {
        $candidates += New-ToolCandidate -Command $env:KGG_NPM
    }
    if ($env:NPM) {
        $candidates += New-ToolCandidate -Command $env:NPM
    }
    $candidates += New-ToolCandidate -Command "npm.cmd"
    $candidates += New-ToolCandidate -Command "npm"

    foreach ($candidate in $candidates) {
        if (Test-ToolCandidate $candidate) {
            return $candidate
        }
    }
    return $null
}

$python = Select-Python
$node = Select-Node
$npm = Select-Npm

$env:KGG_NODE = Resolve-ToolSource $node.Command
if ($npm) {
    $env:KGG_NPM = Resolve-ToolSource $npm.Command
}

Push-Location $RepoRoot
try {
    & $python.Command @($python.Prefix) $BatteryScript @BatteryArgs
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
