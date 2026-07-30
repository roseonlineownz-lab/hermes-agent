$ErrorActionPreference = 'Stop'

$Version = '0.5.2'
$Url = "https://github.com/block/buzz/releases/download/v$Version/Buzz_${Version}_x64-setup_alpha-unsigned.exe"
$ExpectedSha256 = '52622e704025f7ea14ee4f327ec6d93cb054a7336daa6833357c64dd64968f2a'
$Installer = Join-Path $env:TEMP "Buzz_${Version}_Setup.exe"

Write-Host "Buzz Desktop v$Version wordt veilig gedownload..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $Url -OutFile $Installer -UseBasicParsing

$ActualSha256 = (Get-FileHash -Path $Installer -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ActualSha256 -ne $ExpectedSha256) {
    Remove-Item $Installer -Force -ErrorAction SilentlyContinue
    throw "Veiligheidscontrole mislukt: SHA-256 komt niet overeen. De download is verwijderd."
}

Write-Host 'SHA-256 klopt. De officiële installer wordt gestart.' -ForegroundColor Green
Write-Host 'Windows kan waarschuwen omdat deze Developer Preview nog niet digitaal ondertekend is.' -ForegroundColor Yellow
Write-Host "Klik dan op 'Meer informatie' en vervolgens op 'Toch uitvoeren'." -ForegroundColor Yellow

$Process = Start-Process -FilePath $Installer -PassThru
$Process.WaitForExit()

$Candidates = @(
    (Join-Path $env:LOCALAPPDATA 'Buzz\Buzz.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Buzz\Buzz.exe'),
    (Join-Path $env:ProgramFiles 'Buzz\Buzz.exe')
)

$BuzzExe = $Candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($BuzzExe) {
    Start-Process $BuzzExe
    Write-Host 'Buzz Desktop is geïnstalleerd en geopend.' -ForegroundColor Green
} else {
    $Shortcut = Get-ChildItem @(
        (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'),
        (Join-Path $env:ProgramData 'Microsoft\Windows\Start Menu\Programs')
    ) -Filter '*Buzz*.lnk' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1

    if ($Shortcut) {
        Start-Process $Shortcut.FullName
        Write-Host 'Buzz Desktop is geïnstalleerd en via het Startmenu geopend.' -ForegroundColor Green
    } else {
        Write-Host 'De installatie is afgerond. Open Buzz via het Windows Startmenu.' -ForegroundColor Yellow
    }
}

Write-Host ''
Write-Host 'VOLGENDE STAP:' -ForegroundColor Cyan
Write-Host '1. Open in Buzz de optie Pair mobile / Link device.'
Write-Host '2. Scan de QR-code met de Buzz-app op je gsm.'
Write-Host '3. Deel nooit de nostrpair://-koppelcode met iemand anders.'
Read-Host 'Druk op Enter om dit venster te sluiten'
