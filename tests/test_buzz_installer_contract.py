from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install-buzz-windows.ps1"


def _script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_buzz_installer_resolves_latest_stable_release() -> None:
    script = _script()
    assert "https://api.github.com/repos/block/buzz/releases/latest" in script
    assert "draft -eq $true" in script
    assert "prerelease -eq $true" in script
    assert "$Version = '0.5.2'" not in script
    assert "/releases/download/v$Version/" not in script


def test_buzz_installer_is_fail_closed_on_integrity() -> None:
    script = _script()
    assert "^sha256:([0-9a-fA-F]{64})$" in script
    assert "geen eenduidige SHA-256 digest" in script
    assert "Get-FileHash -Path $Installer -Algorithm SHA256" in script
    assert "if ($ActualSha256 -ne $ExpectedSha256)" in script

    download = script.index("Invoke-WebRequest -Uri ([string]$InstallerAsset.browser_download_url)")
    verify = script.index("Get-FileHash -Path $Installer -Algorithm SHA256")
    execute = script.index("Start-Process -FilePath $Installer")
    assert download < verify < execute


def test_buzz_installer_pins_downloads_to_official_repository() -> None:
    script = _script()
    assert "$Uri.Scheme -ne 'https'" in script
    assert "$Uri.Host -ne 'github.com'" in script
    assert "'/block/buzz/releases/tag/'" in script
    assert "'/block/buzz/releases/download/'" in script
    assert "Meerdere mogelijke Buzz-installers gevonden" in script


def test_buzz_installer_supports_safe_automation_and_cleanup() -> None:
    script = _script()
    assert "[switch]$DownloadOnly" in script
    assert "[switch]$NonInteractive" in script
    assert "if (-not $NonInteractive)" in script
    assert "finally" in script
    assert "Remove-Item $Installer -Force" in script
