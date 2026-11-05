# 跨平台工具檢查；語法與合成檔案測試不代表 Windows 安裝包已建置或安裝。
param([Parameter(Mandatory=$true)][string]$ReportPath)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'packaging/windows-common.ps1')
$checks = @()
function Assert-True { param([bool]$Condition,[string]$Message) if (-not $Condition) { throw $Message } }
function Assert-Rejected {
    param([scriptblock]$Operation)
    $rejected = $false
    try { & $Operation | Out-Null } catch { $rejected = $true }
    Assert-True $rejected 'Invalid input was accepted.'
}
$temp = Join-Path ([IO.Path]::GetTempPath()) ('markitdown-tooling-' + [Guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($temp) | Out-Null
try {
    $scripts = @(Get-ChildItem -LiteralPath (Join-Path $root 'packaging') -Filter '*.ps1') + @((Get-Item -LiteralPath $PSCommandPath))
    foreach ($script in $scripts) {
        $tokens = $null; $errors = $null
        [Management.Automation.Language.Parser]::ParseFile($script.FullName,[ref]$tokens,[ref]$errors) | Out-Null
        Assert-True ($errors.Count -eq 0) ($script.Name + ': ' + ($errors -join '; '))
    }
    $checks += @{ name = 'powershell_ast'; passed = $true; scripts = $scripts.Count }
    $bundle = Join-Path $temp ('bundle with spaces-' + [char]0x6e2c)
    [IO.Directory]::CreateDirectory((Join-Path $bundle '_internal')) | Out-Null
    [IO.File]::WriteAllText((Join-Path $bundle 'MarkItDownDesktop.exe'),'SYNTHETIC EXE - not a Windows executable')
    [IO.File]::WriteAllText((Join-Path $bundle '_internal/native.dll'),'SYNTHETIC DLL')
    New-BundleManifest -Directory $bundle -AppVersion '0.1.0'
    $manifest = Test-BundleIntegrity $bundle
    Assert-True (@($manifest.files).Count -eq 2) 'Manifest lost files.'
    Assert-Rejected { New-BundleManifest -Directory $bundle -AppVersion '0.1.0' }
    $checks += @{ name = 'manifest_roundtrip_and_no_overwrite'; passed = $true }
    $payload = Join-Path $bundle '_internal/native.dll'
    [IO.File]::AppendAllText($payload,'tampered')
    Assert-Rejected { Test-BundleIntegrity $bundle }
    [IO.File]::WriteAllText($payload,'SYNTHETIC DLL')
    $extra = Join-Path $bundle 'extra.dll';[IO.File]::WriteAllText($extra,'untracked')
    Assert-Rejected { Test-BundleIntegrity $bundle };Remove-Item -LiteralPath $extra
    Remove-Item -LiteralPath $payload
    Assert-Rejected { Test-BundleIntegrity $bundle }
    [IO.File]::WriteAllText($payload,'SYNTHETIC DLL')
    $checks += @{ name = 'tampered_missing_extra_files_rejected'; passed = $true }
    $uninstaller = Join-Path $bundle 'unins000.exe';[IO.File]::WriteAllText($uninstaller,'synthetic installer metadata')
    Test-BundleIntegrity $bundle | Out-Null
    Remove-Item -LiteralPath $uninstaller
    $checks += @{ name = 'inno_metadata_allowed'; passed = $true }
    $manifestPath = Join-Path $bundle 'bundle-manifest.json'
    $original = [IO.File]::ReadAllText($manifestPath)
    foreach ($invalid in @('../escape','/absolute','C:/drive','_internal\native.dll','./dot','_internal//empty')) {
        $bad = $original | ConvertFrom-Json;$bad.files[0].path = $invalid
        $bad | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
        Assert-Rejected { Test-BundleIntegrity $bundle }
    }
    $bad = $original | ConvertFrom-Json;$bad.files[1].path = $bad.files[0].path.ToUpperInvariant()
    $bad | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
    Assert-Rejected { Test-BundleIntegrity $bundle }
    [IO.File]::WriteAllText($manifestPath,$original)
    $checks += @{ name = 'unsafe_and_case_duplicate_paths_rejected'; passed = $true }
    if ($env:OS -ne 'Windows_NT') {
        $link = Join-Path $bundle 'linked.dll'
        New-Item -ItemType SymbolicLink -Path $link -Target $payload | Out-Null
        Assert-Rejected { Test-BundleIntegrity $bundle }
        Remove-Item -LiteralPath $link
        $checks += @{ name = 'symbolic_links_rejected'; passed = $true }
        Assert-Rejected { & (Join-Path $root 'packaging/build-windows.ps1') }
        Assert-Rejected { & (Join-Path $root 'packaging/verify-windows-install.ps1') -ReportDirectory (Join-Path $temp 'must-not-create') }
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $temp 'must-not-create'))) 'Wrong-platform verifier changed files.'
        $checks += @{ name = 'wrong_platform_guards'; passed = $true }
    }
    Assert-True ((ConvertTo-NativeArgument 'path with spaces') -eq '"path with spaces"') 'Space quoting failed.'
    Assert-True ((ConvertTo-NativeArgument 'C:\trailing\') -eq '"C:\trailing\\"') 'Trailing slash quoting failed.'
    Assert-Rejected { ConvertTo-NativeArgument 'bad"quote' }
    $checks += @{ name = 'native_argument_quoting'; passed = $true }
    $child = Join-Path $temp ('child with spaces-' + [char]0x8a66 + '.ps1')
    [IO.File]::WriteAllText($child,'param([string]$Value) if ($Value -ne "path with spaces") { exit 7 }; exit 0')
    $powershell = (Get-Process -Id $PID).Path
    Invoke-CheckedProcess -FilePath $powershell -Arguments @('-NoProfile','-File',$child,'-Value','path with spaces') -LogPrefix (Join-Path $temp 'successful-process')
    Assert-Rejected { Invoke-CheckedProcess -FilePath $powershell -Arguments @('-NoProfile','-Command','exit 5') -LogPrefix (Join-Path $temp 'failed-process') }
    Assert-Rejected { Invoke-CheckedProcess -FilePath $powershell -Arguments @('-NoProfile','-Command','Start-Sleep -Seconds 5') -LogPrefix (Join-Path $temp 'timeout-process') -TimeoutSeconds 1 }
    $checks += @{ name = 'process_exit_codes_and_timeout'; passed = $true }
    $parent = Split-Path -Parent ([IO.Path]::GetFullPath($ReportPath))
    [IO.Directory]::CreateDirectory($parent) | Out-Null
    @{ scope = 'Synthetic file manifests and PowerShell parser/processes; no Windows build or installer executed';
       powershell = $PSVersionTable.PSVersion.ToString(); os = [Environment]::OSVersion.Platform.ToString();
       windows_executed = ($env:OS -eq 'Windows_NT'); windows_installer_executed = $false;
       complete = $true; checks = $checks } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    Write-Host "Tooling checks passed: $($checks.Count). No Windows installer claim."
} finally { Remove-Item -LiteralPath $temp -Recurse -Force }
