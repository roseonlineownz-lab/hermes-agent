$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$InstallerPath = Join-Path $PSScriptRoot '..\scripts\install-buzz-windows.ps1'
$Installer = Get-Content -LiteralPath $InstallerPath -Raw -Encoding UTF8

function Assert-Contains {
    param([string]$Needle)
    if (-not $Installer.Contains($Needle)) {
        throw "Buzz installer contract missing: $Needle"
    }
}

function Assert-NotContains {
    param([string]$Needle)
    if ($Installer.Contains($Needle)) {
        throw "Buzz installer contract contains forbidden text: $Needle"
    }
}

Assert-Contains 'https://api.github.com/repos/block/buzz/releases/latest'
Assert-Contains 'draft -eq $true'
Assert-Contains 'prerelease -eq $true'
Assert-NotContains '$Version = ''0.5.2'''
Assert-NotContains '/releases/download/v$Version/'

Assert-Contains '^sha256:([0-9a-fA-F]{64})$'
Assert-Contains 'geen eenduidige SHA-256 digest'
Assert-Contains 'Get-FileHash -Path $Installer -Algorithm SHA256'
Assert-Contains 'if ($ActualSha256 -ne $ExpectedSha256)'

$DownloadIndex = $Installer.IndexOf('Invoke-WebRequest -Uri ([string]$InstallerAsset.browser_download_url)')
$VerifyIndex = $Installer.IndexOf('Get-FileHash -Path $Installer -Algorithm SHA256')
$ExecuteIndex = $Installer.IndexOf('Start-Process -FilePath $Installer')
if ($DownloadIndex -lt 0 -or $VerifyIndex -lt 0 -or $ExecuteIndex -lt 0) {
    throw 'Buzz installer contract cannot locate download, verification or execution stages.'
}
if (-not ($DownloadIndex -lt $VerifyIndex -and $VerifyIndex -lt $ExecuteIndex)) {
    throw 'Buzz installer must download, verify and only then execute.'
}

Assert-Contains '$Uri.Scheme -ne ''https'''
Assert-Contains '$Uri.Host -ne ''github.com'''
Assert-Contains '''/block/buzz/releases/tag/'''
Assert-Contains '''/block/buzz/releases/download/'''
Assert-Contains 'Meerdere mogelijke Buzz-installers gevonden'

Assert-Contains '[switch]$DownloadOnly'
Assert-Contains '[switch]$NonInteractive'
Assert-Contains 'if (-not $NonInteractive)'
Assert-Contains 'finally'
Assert-Contains 'Remove-Item $Installer -Force'

Write-Output 'Buzz installer contract: PASS'
