param(
  [ValidatePattern('^[a-p]{32}$')]
  [string]$ExtensionId = 'hpamfcbdlakklemljchpkfinmakjeada',

  [ValidateSet('Chrome', 'Chromium')]
  [string]$Browser = 'Chrome',

  [switch]$PlanOnly
)

$ErrorActionPreference = 'Stop'
$HostName = 'com.kgg.project_status_route'
$InstallDir = Join-Path $env:LOCALAPPDATA 'KGG\project-status-route'
$HostScript = Join-Path $InstallDir 'native_host.py'
$Launcher = Join-Path $InstallDir 'native_host_launcher.bat'
$Manifest = Join-Path $InstallDir 'native_host_manifest.json'

$RegistryRoot = if ($Browser -eq 'Chromium') {
  'HKCU:\Software\Chromium\NativeMessagingHosts'
} else {
  'HKCU:\Software\Google\Chrome\NativeMessagingHosts'
}
$RegistryPath = Join-Path $RegistryRoot $HostName

if ($PlanOnly) {
  Write-Output "plan:${HostName}:${Browser}:${ExtensionId}:$RegistryPath"
  exit 0
}

New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'native_host.py') $HostScript -Force

$Python = (Get-Command python.exe -ErrorAction Stop).Source
$LauncherText = '@echo off' + [Environment]::NewLine +
  '"' + $Python + '" -I "' + $HostScript + '"' + [Environment]::NewLine
Set-Content -LiteralPath $Launcher -Value $LauncherText -Encoding Ascii

$ManifestPayload = [ordered]@{
  name = $HostName
  description = 'KGG Project Status ChatGPT route host'
  path = $Launcher
  type = 'stdio'
  allowed_origins = @("chrome-extension://$ExtensionId/")
}
$ManifestJson = $ManifestPayload | ConvertTo-Json -Depth 4
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($Manifest, $ManifestJson, $Utf8NoBom)

New-Item -Path $RegistryPath -Force | Out-Null
(Get-Item $RegistryPath).SetValue('', $Manifest)

Write-Output "installed:${HostName}:${Browser}:${ExtensionId}"
