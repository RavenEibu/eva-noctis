<#
.SYNOPSIS
  EVA Noctis - installs the color schemes for Windows Terminal (current user, no admin rights).
.DESCRIPTION
  Copies EvaNoctis.fragment.json to %LOCALAPPDATA%\Microsoft\Windows Terminal\Fragments\EvaNoctis.
  Windows Terminal then lists the 28 "Noctis (...)" schemes in Settings > Color schemes, and
  you pick one per profile. Your settings.json is never edited.
.PARAMETER Uninstall
  Removes the fragment.
.PARAMETER DryRun
  Prints what would change without touching any file.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File install.ps1
#>
param([switch]$Uninstall, [switch]$DryRun)
$ErrorActionPreference = 'Stop'

$target = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows Terminal\Fragments\EvaNoctis'
$source = Join-Path $PSScriptRoot 'windows-terminal\EvaNoctis.fragment.json'

if ($Uninstall) {
    if (Test-Path $target) {
        if ($DryRun) { Write-Host "[dry-run] remove $target" } else { Remove-Item -Recurse -Force $target }
        Write-Host "Removed $target"
    } else { Write-Host 'Nothing to uninstall.' }
    return
}

if (-not (Test-Path $source)) { throw "Fragment not found: $source (run this script from the terminals folder)" }
if ($DryRun) {
    Write-Host "[dry-run] copy $source -> $target\evanoctis.json"
} else {
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    Copy-Item -Force $source (Join-Path $target 'evanoctis.json')
}
Write-Host "Installed the EVA Noctis color schemes in $target"
Write-Host 'Restart Windows Terminal, then set "colorScheme": "Noctis (EVA-01)" in a profile (or use Settings > Appearance).'
