# Windows 建置入口：重建隔離環境、執行驗證、打包並選擇產生安裝精靈。
param([switch]$BuildInstaller,[string]$IsccPath)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows build requires Windows.' }
. (Join-Path $PSScriptRoot 'windows-common.ps1')
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$OriginalQtPlatform = $env:QT_QPA_PLATFORM
$OriginalLatinFont = $env:TEST_LATIN_FONT
$OriginalCjkFont = $env:TEST_CJK_FONT
Push-Location $ProjectRoot
try {
    python -c "import sys,struct; assert sys.version_info[:2] == (3, 12) and struct.calcsize('P') == 8, 'Use x64 Python 3.12'"
    if ($LASTEXITCODE -ne 0) { throw 'Python version check failed.' }
    if ((Test-Path -LiteralPath '.venv-build') -and
        ((Get-Item -LiteralPath '.venv-build').Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Managed build environment must not be a link/junction.'
    }
    python -m venv --clear .venv-build
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
    $BuildPython = Join-Path $ProjectRoot '.venv-build\Scripts\python.exe'
    $Reports = Join-Path $ProjectRoot ('dist\reports\build-' + [Guid]::NewGuid().ToString('N'))
    [IO.Directory]::CreateDirectory($Reports) | Out-Null
    & $BuildPython -m pip install --require-hashes -r packaging/requirements-windows.txt
    if ($LASTEXITCODE -ne 0) { throw 'Hashed dependency installation failed.' }
    & $BuildPython scripts/verify_upstream.py
    if ($LASTEXITCODE -ne 0) { throw 'Source verification failed.' }
    & $BuildPython scripts/license_inventory.py --verify
    if ($LASTEXITCODE -ne 0) { throw 'License inventory verification failed.' }
    & $BuildPython -m pip install --no-deps --no-build-isolation ./vendor/markitdown .
    if ($LASTEXITCODE -ne 0) { throw 'Local project installation failed.' }
    $env:QT_QPA_PLATFORM = 'offscreen'
    $env:TEST_LATIN_FONT = 'C:\Windows\Fonts\arial.ttf'
    $env:TEST_CJK_FONT = 'C:\Windows\Fonts\msjh.ttc'
    # 將原生 stderr 直接存檔，避免 PowerShell 5.1 把正常測試日誌當成終止錯誤。
    Invoke-CheckedProcess -FilePath $BuildPython -Arguments @('-m','unittest','discover','-s','tests','-v') `
        -LogPrefix (Join-Path $Reports 'unit-tests') -TimeoutSeconds 900
    & $BuildPython -m PyInstaller --noconfirm --clean packaging/desktop.spec
    if ($LASTEXITCODE -ne 0) { throw 'Packaging failed.' }
    & $BuildPython scripts/smoke_frozen.py --acceptance-report (Join-Path $Reports 'public-pdf-results.json') dist/MarkItDownDesktop/MarkItDownDesktop.exe
    if ($LASTEXITCODE -ne 0) { throw 'Bundled executable smoke test failed.' }
    Copy-Item THIRD_PARTY_NOTICES dist/MarkItDownDesktop/
    $Bundle = Join-Path $ProjectRoot 'dist\MarkItDownDesktop'
    Invoke-CheckedProcess -FilePath (Join-Path $Bundle 'MarkItDownDesktop.exe') `
        -Arguments @('--self-test','--report',(Join-Path $Reports 'runtime-self-test.json')) `
        -LogPrefix (Join-Path $Reports 'runtime')
    $Version = & $BuildPython -c "from importlib.metadata import version; print(version('markitdown-desktop'))"
    if ($LASTEXITCODE -ne 0) { throw 'Application version query failed.' }
    New-BundleManifest -Directory $Bundle -AppVersion $Version.Trim()
    Test-BundleIntegrity $Bundle | Out-Null
    $summary = @{ platform = 'Windows'; version = $Version.Trim(); folder_build_verified = $true;
        installer_created = $false; clean_machine_accepted = $false; gpu_executed = $false;
        tesseract_bundled = $false; onnx_models_bundled = $true }
    if ($BuildInstaller) {
        if (-not $IsccPath) { $IsccPath = Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe' }
        if (-not (Test-Path -LiteralPath $IsccPath)) { throw 'Install Inno Setup 6.3+ or pass -IsccPath.' }
        $SetupDir = Join-Path $ProjectRoot 'dist\installer'
        & $IsccPath "/DBundleDir=$Bundle" "/DOutputDir=$SetupDir" "/DAppVersion=$($Version.Trim())" `
            (Join-Path $PSScriptRoot 'windows-installer.iss')
        if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed.' }
        $SetupFile = Join-Path $SetupDir "MarkItDownDesktop-Setup-$($Version.Trim())-windows-x64.exe"
        $hash = (Get-FileHash -LiteralPath $SetupFile -Algorithm SHA256).Hash.ToLowerInvariant()
        "$hash  $([IO.Path]::GetFileName($SetupFile))" | Set-Content -LiteralPath ($SetupFile + '.sha256') -Encoding ASCII
        $summary.installer_created = $true
        $summary.installer_compiler = (Get-Item -LiteralPath $IsccPath).VersionInfo.FileVersion
    }
    $summary | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $Reports 'build-summary.json') -Encoding UTF8
    Write-Host "Development build verified; reports: $Reports. Tesseract native engine is not bundled."
} finally {
    $env:QT_QPA_PLATFORM = $OriginalQtPlatform
    $env:TEST_LATIN_FONT = $OriginalLatinFont
    $env:TEST_CJK_FONT = $OriginalCjkFont
    Pop-Location
}
