# Use a disposable Windows account/VM. Never replace an existing installation.
param([Parameter(Mandatory=$true)][string]$SetupFile,
      [Parameter(Mandatory=$true)][string]$ReportDirectory)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Installer lifecycle test requires Windows.' }
. (Join-Path $PSScriptRoot 'windows-common.ps1')
$install = Join-Path $env:LOCALAPPDATA 'Programs\MarkItDownDesktop'
if (Test-Path -LiteralPath $install) { throw 'Existing installation found; lifecycle test will not replace it.' }
if (Test-Path -LiteralPath $ReportDirectory) { throw 'Choose a new report directory.' }
$ReportDirectory = [IO.Path]::GetFullPath($ReportDirectory)
[IO.Directory]::CreateDirectory($ReportDirectory) | Out-Null
$results = @{ schema_version = 1; scope = 'Automated installer lifecycle on disposable Windows';
    install_verified = $false; uninstall_verified = $false; user_data_preserved = $false; complete = $false }
# Qt AppLocalDataLocation uses organization/application names. Use a unique
# sentinel, not settings.json or any user/model file.
$dataDir = Join-Path $env:LOCALAPPDATA 'MarkItDownDesktop\MarkItDownDesktop'
[IO.Directory]::CreateDirectory($dataDir) | Out-Null
$sentinel = Join-Path $dataDir ('installer-test-' + [Guid]::NewGuid().ToString('N') + '.txt')
[IO.File]::WriteAllText($sentinel,'KEEP INSTALLER TEST DATA')
try {
    Invoke-CheckedProcess -FilePath ([IO.Path]::GetFullPath($SetupFile)) `
        -Arguments @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-',('/LOG=' + (Join-Path $ReportDirectory 'setup.log'))) `
        -LogPrefix (Join-Path $ReportDirectory 'setup-process')
    & (Join-Path $PSScriptRoot 'verify-windows-install.ps1') -InstallDirectory $install `
        -ReportDirectory (Join-Path $ReportDirectory 'installed')
    $results.install_verified = $true
} catch { $results.error = $_.Exception.Message }
finally {
    try {
        $uninstaller = Join-Path $install 'unins000.exe'
        if (Test-Path -LiteralPath $uninstaller) {
            Invoke-CheckedProcess -FilePath $uninstaller -Arguments @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',
                ('/LOG=' + (Join-Path $ReportDirectory 'uninstall.log'))) -LogPrefix (Join-Path $ReportDirectory 'uninstall-process')
            # Inno's original uninstaller can spawn a temporary copy. Wait for
            # its installed payload to disappear, rather than trust parent exit.
            $deadline = [DateTime]::UtcNow.AddSeconds(30)
            while ((Test-Path -LiteralPath $install) -and [DateTime]::UtcNow -lt $deadline) {
                Start-Sleep -Milliseconds 200
            }
            $results.uninstall_verified = -not (Test-Path -LiteralPath $install)
        }
        $results.user_data_preserved = (Test-Path -LiteralPath $sentinel) -and ([IO.File]::ReadAllText($sentinel) -eq 'KEEP INSTALLER TEST DATA')
        $results.complete = $results.install_verified -and $results.uninstall_verified -and $results.user_data_preserved
    } catch { $results.cleanup_error = $_.Exception.Message }
    # Remove only the sentinel created here. User settings/model directories stay.
    Remove-Item -LiteralPath $sentinel -ErrorAction SilentlyContinue
    $results | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $ReportDirectory 'installer-lifecycle.json') -Encoding UTF8
}
if (-not $results.complete) { throw 'Installer lifecycle failed; see installer-lifecycle.json.' }
