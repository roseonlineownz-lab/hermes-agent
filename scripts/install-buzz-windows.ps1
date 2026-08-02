[CmdletBinding()]
param(
    [switch]$DownloadOnly,
    [switch]$NonInteractive
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$ReleaseApi = 'https://api.github.com/repos/block/buzz/releases/latest'
$Headers = @{
    Accept = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2026-03-10'
    'User-Agent' = 'Hermes-Buzz-Installer/1.0'
}

function Assert-TrustedGitHubUrl {
    param(
        [Parameter(Mandatory)]
        [string]$Url,
        [Parameter(Mandatory)]
        [string]$RequiredPathPrefix
    )

    $Uri = [Uri]$Url
    if ($Uri.Scheme -ne 'https' -or $Uri.Host -ne 'github.com') {
        throw "Onvertrouwde download-URL: $Url"
    }
    if (-not $Uri.AbsolutePath.StartsWith($RequiredPathPrefix, [StringComparison]::Ordinal)) {
        throw "Onverwacht GitHub-pad: $($Uri.AbsolutePath)"
    }
}

function Resolve-BuzzRelease {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $Release = Invoke-RestMethod -Uri $ReleaseApi -Headers $Headers -Method Get

    if ($Release.draft -eq $true -or $Release.prerelease -eq $true) {
        throw 'De latest-release API retourneerde geen stabiele Buzz-release.'
    }
    if ([string]$Release.tag_name -notmatch '^v\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$') {
        throw "Onverwachte Buzz-versietag: $($Release.tag_name)"
    }

    Assert-TrustedGitHubUrl -Url ([string]$Release.html_url) -RequiredPathPrefix '/block/buzz/releases/tag/'
    return $Release
}

function Select-BuzzWindowsAsset {
    param([Parameter(Mandatory)]$Release)

    $Candidates = @($Release.assets | Where-Object {
        [string]$_.name -match '(?i)^Buzz_.*_x64-setup(?:[_-].*)?\.exe$'
    })

    if ($Candidates.Count -eq 0) {
        throw "Geen Windows x64 Buzz-installer gevonden in release $($Release.tag_name)."
    }

    $SignedCandidates = @($Candidates | Where-Object { [string]$_.name -notmatch '(?i)unsigned' })
    if ($SignedCandidates.Count -eq 1) {
        $Asset = $SignedCandidates[0]
    } elseif ($Candidates.Count -eq 1) {
        $Asset = $Candidates[0]
    } else {
        $Names = ($Candidates | ForEach-Object { $_.name }) -join ', '
        throw "Meerdere mogelijke Buzz-installers gevonden; selectie is niet veilig: $Names"
    }

    Assert-TrustedGitHubUrl -Url ([string]$Asset.browser_download_url) -RequiredPathPrefix '/block/buzz/releases/download/'
    return $Asset
}

function Resolve-ExpectedSha256 {
    param(
        [Parameter(Mandatory)]$Release,
        [Parameter(Mandatory)]$InstallerAsset
    )

    $Digest = [string]$InstallerAsset.digest
    if ($Digest -match '^sha256:([0-9a-fA-F]{64})$') {
        return $Matches[1].ToLowerInvariant()
    }

    $ChecksumAssets = @($Release.assets | Where-Object {
        [string]$_.name -match '(?i)(sha256sums|sha256|checksums).*(\.txt|\.sha256|\.sha256sum)?$'
    })
    if ($ChecksumAssets.Count -ne 1) {
        throw 'De release bevat geen eenduidige SHA-256 digest of checksumbestand. Installatie wordt fail-closed gestopt.'
    }

    $ChecksumAsset = $ChecksumAssets[0]
    Assert-TrustedGitHubUrl -Url ([string]$ChecksumAsset.browser_download_url) -RequiredPathPrefix '/block/buzz/releases/download/'

    $ChecksumPath = Join-Path $env:TEMP ("buzz-checksums-{0}.txt" -f [Guid]::NewGuid().ToString('N'))
    try {
        Invoke-WebRequest -Uri ([string]$ChecksumAsset.browser_download_url) -OutFile $ChecksumPath -UseBasicParsing
        $EscapedName = [Regex]::Escape([string]$InstallerAsset.name)
        $Match = Select-String -Path $ChecksumPath -Pattern "(?i)^([0-9a-f]{64})\s+\*?$EscapedName$" | Select-Object -First 1
        if (-not $Match) {
            throw "Geen checksum gevonden voor $($InstallerAsset.name)."
        }
        return $Match.Matches[0].Groups[1].Value.ToLowerInvariant()
    } finally {
        Remove-Item $ChecksumPath -Force -ErrorAction SilentlyContinue
    }
}

$Release = Resolve-BuzzRelease
$InstallerAsset = Select-BuzzWindowsAsset -Release $Release
$ExpectedSha256 = Resolve-ExpectedSha256 -Release $Release -InstallerAsset $InstallerAsset
$Version = ([string]$Release.tag_name).TrimStart('v')
$Installer = Join-Path $env:TEMP ("Buzz_{0}_{1}.exe" -f $Version, [Guid]::NewGuid().ToString('N'))

try {
    Write-Host "Block Buzz Desktop $($Release.tag_name) wordt veilig gedownload..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri ([string]$InstallerAsset.browser_download_url) -OutFile $Installer -UseBasicParsing

    $ActualSha256 = (Get-FileHash -Path $Installer -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ActualSha256 -ne $ExpectedSha256) {
        throw "Veiligheidscontrole mislukt: SHA-256 komt niet overeen. Verwacht $ExpectedSha256, ontvangen $ActualSha256."
    }

    Write-Host "SHA-256 geverifieerd voor $($InstallerAsset.name)." -ForegroundColor Green

    if ($DownloadOnly) {
        $DownloadPath = Join-Path ([Environment]::GetFolderPath('Desktop')) ([string]$InstallerAsset.name)
        Move-Item -Path $Installer -Destination $DownloadPath -Force
        $Installer = $null
        Write-Host "Geverifieerde installer opgeslagen als: $DownloadPath" -ForegroundColor Green
        return
    }

    $Process = Start-Process -FilePath $Installer -PassThru -Wait
    if ($Process.ExitCode -notin @(0, 3010)) {
        throw "Buzz-installer stopte met exitcode $($Process.ExitCode)."
    }

    $Candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Buzz\Buzz.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Buzz\Buzz.exe')
    )
    if ($env:ProgramFiles) {
        $Candidates += Join-Path $env:ProgramFiles 'Buzz\Buzz.exe'
    }

    $BuzzExe = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($BuzzExe) {
        Start-Process $BuzzExe
        Write-Host 'Buzz Desktop is geïnstalleerd en geopend.' -ForegroundColor Green
    } else {
        $ShortcutRoots = @(
            (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'),
            (Join-Path $env:ProgramData 'Microsoft\Windows\Start Menu\Programs')
        )
        $Shortcut = Get-ChildItem $ShortcutRoots -Filter '*Buzz*.lnk' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($Shortcut) {
            Start-Process $Shortcut.FullName
            Write-Host 'Buzz Desktop is geïnstalleerd en via het Startmenu geopend.' -ForegroundColor Green
        } else {
            Write-Host 'De installatie is afgerond. Open Buzz via het Windows Startmenu.' -ForegroundColor Yellow
        }
    }

    Write-Host ''
    Write-Host 'VOLGENDE STAP:' -ForegroundColor Cyan
    Write-Host '1. Ga in Block Buzz naar Settings > Mobile pairing.'
    Write-Host '2. Klik Start pairing en scan de QR-code met Buzz Mobile.'
    Write-Host '3. Deel nooit de nostrpair://-koppelcode met iemand anders.'

    if (-not $NonInteractive) {
        Read-Host 'Druk op Enter om dit venster te sluiten'
    }
} finally {
    if ($Installer -and (Test-Path $Installer)) {
        Remove-Item $Installer -Force -ErrorAction SilentlyContinue
    }
}
