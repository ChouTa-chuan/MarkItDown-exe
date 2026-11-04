$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows build requires Windows.' }
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$OriginalQtPlatform = $env:QT_QPA_PLATFORM
$OriginalLatinFont = $env:TEST_LATIN_FONT
$OriginalCjkFont = $env:TEST_CJK_FONT
Push-Location $ProjectRoot
try {
    python -c "import sys; assert sys.version_info[:2] == (3, 12), 'Use Python 3.12'"
    if ($LASTEXITCODE -ne 0) { throw 'Python version check failed.' }
    python -m venv .venv-build
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
    $BuildPython = Join-Path $ProjectRoot '.venv-build\Scripts\python.exe'
    & $BuildPython -m pip install --require-hashes -r packaging/requirements-windows.txt
    if ($LASTEXITCODE -ne 0) { throw 'Hashed dependency installation failed.' }
    & $BuildPython scripts/verify_upstream.py
    if ($LASTEXITCODE -ne 0) { throw 'Source verification failed.' }
    & $BuildPython -m pip install --no-deps --no-build-isolation ./vendor/markitdown .
    if ($LASTEXITCODE -ne 0) { throw 'Local project installation failed.' }
    $env:QT_QPA_PLATFORM = 'offscreen'
    $env:TEST_LATIN_FONT = 'C:\Windows\Fonts\arial.ttf'
    $env:TEST_CJK_FONT = 'C:\Windows\Fonts\msjh.ttc'
    & $BuildPython -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
    & $BuildPython -m PyInstaller --noconfirm --clean packaging/desktop.spec
    if ($LASTEXITCODE -ne 0) { throw 'Packaging failed.' }
    & $BuildPython scripts/smoke_frozen.py dist/MarkItDownDesktop/MarkItDownDesktop.exe
    if ($LASTEXITCODE -ne 0) { throw 'Bundled executable smoke test failed.' }
    Copy-Item THIRD_PARTY_NOTICES dist/MarkItDownDesktop/
    Write-Host 'Development folder build created. Tesseract and OCR models are not bundled.'
} finally {
    $env:QT_QPA_PLATFORM = $OriginalQtPlatform
    $env:TEST_LATIN_FONT = $OriginalLatinFont
    $env:TEST_CJK_FONT = $OriginalCjkFont
    Pop-Location
}
