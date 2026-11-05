# Shared build/verification helpers, compatible with Windows PowerShell 5.1.
Set-StrictMode -Version Latest

function Assert-NoReparsePoints {
    param([Parameter(Mandatory=$true)][string]$Directory)
    foreach ($item in @((Get-Item -LiteralPath $Directory)) + @(Get-ChildItem -LiteralPath $Directory -Recurse -Force)) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Bundle must not contain links or junctions.' }
    }
}

function New-BundleManifest {
    param([Parameter(Mandatory=$true)][string]$Directory,
          [Parameter(Mandatory=$true)][ValidatePattern('^\d+\.\d+\.\d+$')][string]$AppVersion)
    Assert-NoReparsePoints $Directory
    $root = [IO.Path]::GetFullPath($Directory).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    $manifestPath = Join-Path $root 'bundle-manifest.json'
    if (Test-Path -LiteralPath $manifestPath) { throw 'Bundle manifest already exists.' }
    $records = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force | Sort-Object FullName | ForEach-Object {
        @{ path = $_.FullName.Substring($root.Length).Replace('\','/'); bytes = $_.Length;
           sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
    })
    if ($records.Count -eq 0) { throw 'Empty bundle.' }
    @{ schema_version = 1; platform = 'windows-x64'; app_version = $AppVersion;
       release_status = 'development-preview'; files = $records } |
        ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
}

function Test-BundleIntegrity {
    param([Parameter(Mandatory=$true)][string]$Directory)
    Assert-NoReparsePoints $Directory
    $root = [IO.Path]::GetFullPath($Directory).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    $manifest = Get-Content -LiteralPath (Join-Path $root 'bundle-manifest.json') -Raw | ConvertFrom-Json
    if ($manifest.schema_version -ne 1 -or $manifest.platform -ne 'windows-x64' -or
        $manifest.release_status -ne 'development-preview' -or @($manifest.files).Count -eq 0) { throw 'Invalid bundle manifest.' }
    $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    foreach ($record in $manifest.files) {
        $name = [string]$record.path
        if (-not $name -or $name.Contains(':') -or $name.Contains('\') -or $name.StartsWith('/') -or
            @($name.Split('/') | Where-Object { $_ -in @('..','.','') }).Count -gt 0 -or
            $name -eq 'bundle-manifest.json' -or -not $seen.Add($name)) { throw 'Unsafe or duplicate bundle path.' }
        if ($record.sha256 -notmatch '^[a-fA-F0-9]{64}$' -or $record.bytes -lt 0) { throw 'Invalid bundle digest/size.' }
        $path = Join-Path $root $name
        $file = Get-Item -LiteralPath $path
        if ($file.PSIsContainer -or $file.Length -ne $record.bytes -or
            (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $record.sha256) { throw "Bundle content mismatch: $name" }
    }
    foreach ($file in Get-ChildItem -LiteralPath $root -File -Recurse -Force) {
        $name = $file.FullName.Substring($root.Length).Replace('\','/')
        # Inno Setup adds its uninstaller at the installation root.
        if ($name -eq 'bundle-manifest.json' -or $name -match '^unins\d{3}\.(exe|dat|msg)$') { continue }
        if (-not $seen.Contains($name)) { throw "Untracked bundle file: $name" }
    }
    return $manifest
}

function ConvertTo-NativeArgument {
    param([AllowEmptyString()][string]$Argument)
    # Our arguments are switches and Windows file paths. Embedded quotes are
    # deliberately rejected; trailing backslashes must be doubled before '"'.
    if ($Argument.Contains('"') -or $Argument.Contains([char]0)) { throw 'Unsupported native argument.' }
    return '"' + [regex]::Replace($Argument,'(\\+)$','$1$1') + '"'
}

function Invoke-CheckedProcess {
    param([Parameter(Mandatory=$true)][string]$FilePath,[string[]]$Arguments = @(),
          [Parameter(Mandatory=$true)][string]$LogPrefix,[int]$TimeoutSeconds = 300)
    $parent = Split-Path -Parent ([IO.Path]::GetFullPath($LogPrefix))
    [IO.Directory]::CreateDirectory($parent) | Out-Null
    $nativeArgs = @($Arguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' '
    $process = Start-Process -FilePath $FilePath -ArgumentList $nativeArgs -PassThru `
        -RedirectStandardOutput ($LogPrefix + '.out.log') -RedirectStandardError ($LogPrefix + '.err.log')
    try {
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            if ($env:OS -eq 'Windows_NT') { & taskkill.exe /PID $process.Id /T /F | Out-Null }
            else { $process.Kill() }
            throw 'Validation process timed out; stopped the process started by this verifier.'
        }
        $process.WaitForExit()
        if ($process.ExitCode -ne 0) { throw "Process failed with exit code $($process.ExitCode). See $LogPrefix logs." }
    } finally { $process.Dispose() }
}
