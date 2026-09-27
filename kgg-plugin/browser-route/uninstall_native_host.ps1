param(
  [ValidateSet('Chrome', 'Chromium')]
  [string]$Browser = 'Chrome',
  [switch]$RemoveState
)

$ErrorActionPreference = 'Stop'
$HostName = 'com.kgg.project_status_route'
$RegistryRoot = if ($Browser -eq 'Chromium') {
  'HKCU:\Software\Chromium\NativeMessagingHosts'
} else {
  'HKCU:\Software\Google\Chrome\NativeMessagingHosts'
}
$RegistryPath = Join-Path $RegistryRoot $HostName
Remove-Item -Path $RegistryPath -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path (Join-Path $env:LOCALAPPDATA 'KGG\project-status-route') -Recurse -Force -ErrorAction SilentlyContinue
if ($RemoveState) {
  Remove-Item -Path (Join-Path $env:LOCALAPPDATA 'KGG\project-status\chatgpt-route-state.json') -Force -ErrorAction SilentlyContinue
}
Write-Output "uninstalled:${HostName}:${Browser}"
