param(
    [string]$InstallDirectory,
    [Parameter(Mandatory=$true)][string]$ReportDirectory,
    [switch]$RequireNoPython
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows installation verification requires Windows.' }
. (Join-Path $PSScriptRoot 'windows-common.ps1')
if (-not $InstallDirectory) { $InstallDirectory = Join-Path $env:LOCALAPPDATA 'Programs\MarkItDownDesktop' }
if (Test-Path -LiteralPath $ReportDirectory) { throw 'Choose a new, empty report directory.' }
[IO.Directory]::CreateDirectory([IO.Path]::GetFullPath($ReportDirectory)) | Out-Null
$ReportDirectory = [IO.Path]::GetFullPath($ReportDirectory)
$pythonDetected = @('python','python3','py' | ForEach-Object { Get-Command $_ -ErrorAction SilentlyContinue }).Count -gt 0
$report = @{ schema_version = 1; scope = 'Windows automated installation smoke; not human acceptance or GPU validation';
    recorded_at = [DateTime]::UtcNow.ToString('o'); os_version = [Environment]::OSVersion.VersionString;
    python_command_detected = $pythonDetected; verifier_requires_external_python = $false;
    clean_machine_accepted = $false; gpu_executed = $false; checks = @(); complete = $false }
try {
    if ($RequireNoPython -and $pythonDetected) { throw 'Python command detected; cannot record a no-Python machine run.' }
    $manifest = Test-BundleIntegrity $InstallDirectory
    $report.app_version = $manifest.app_version
    $report.checks += @{ name = 'installed_bundle_hashes'; outcome = 'passed'; files = @($manifest.files).Count }
    $executable = Join-Path $InstallDirectory 'MarkItDownDesktop.exe'
    $runtimeReport = Join-Path $ReportDirectory 'runtime-self-test.json'
    Invoke-CheckedProcess -FilePath $executable -Arguments @('--self-test','--report',$runtimeReport) `
        -LogPrefix (Join-Path $ReportDirectory 'runtime') -TimeoutSeconds 300
    $runtime = Get-Content -LiteralPath $runtimeReport -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $runtime.complete -or -not $runtime.frozen -or $runtime.external_python_required -ne $false -or $runtime.platform -ne 'Windows' -or
        @($runtime.checks).Count -ne 5 -or @($runtime.checks | Where-Object { $_.outcome -ne 'passed' }).Count -gt 0) {
        throw 'Packaged runtime self-test did not pass all required checks.'
    }
    $report.checks += @{ name = 'packaged_runtime_self_test'; outcome = 'passed' }
    $process = Start-Process -FilePath $executable -PassThru
    try {
        if (-not $process.WaitForInputIdle(20000)) { throw 'Desktop did not become idle.' }
        $process.Refresh()
        $deadline = [DateTime]::UtcNow.AddSeconds(10)
        while (-not $process.HasExited -and $process.MainWindowHandle -eq [IntPtr]::Zero -and [DateTime]::UtcNow -lt $deadline) {
            Start-Sleep -Milliseconds 100
            $process.Refresh()
        }
        if ($process.HasExited -or $process.MainWindowHandle -eq [IntPtr]::Zero) { throw 'No desktop window found.' }
        if (-not $process.MainWindowTitle.StartsWith('MarkItDown')) { throw 'Unexpected desktop window.' }
        if (-not $process.CloseMainWindow() -or -not $process.WaitForExit(10000)) { throw 'Desktop did not close normally.' }
        if ($process.ExitCode -ne 0) { throw 'Desktop exited with an error.' }
        $report.checks += @{ name = 'desktop_launch_and_close'; outcome = 'passed' }
    } finally {
        if (-not $process.HasExited) { & taskkill.exe /PID $process.Id /T /F | Out-Null }
        $process.Dispose()
    }
    $report.complete = $true
} catch {
    $report.checks += @{ name = 'verification_failure'; outcome = 'failed'; detail = $_.Exception.Message }
} finally {
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $ReportDirectory 'installation-results.json') -Encoding UTF8
}
if (-not $report.complete) { throw 'Installation checks failed; see installation-results.json.' }
