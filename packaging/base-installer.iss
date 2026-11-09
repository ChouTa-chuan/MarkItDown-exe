; 獨立基本包開發驗證；與舊 MarkItDownDesktop 預覽安裝器使用不同 AppId。
#ifndef BundleDir
  #error BundleDir is required
#endif
#ifndef OutputDir
  #error OutputDir is required
#endif
#ifndef AppVersion
  #error AppVersion is required
#endif
#ifndef TransitionRules
  #error Verified TransitionRules is required
#endif
#if !FileExists(AddBackslash(BundleDir) + "MarkItDownBase.exe")
  #error Verified Windows base executable is required
#endif
#if !FileExists(AddBackslash(BundleDir) + "base-install-catalog.json")
  #error Verified base install catalog is required
#endif

[Setup]
AppId={{DB61BCA4-7678-4BEA-9140-27B548460D75}
AppName=MarkItDown Base Preview
AppVersion={#AppVersion}
AppPublisher=MarkItDown Desktop contributors
DefaultDirName={localappdata}\Programs\MarkItDownBasePreview
DefaultGroupName=MarkItDown Base Preview
PrivilegesRequired=lowest
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
MinVersion=10.0.18362
OutputDir={#OutputDir}
OutputBaseFilename=MarkItDownBase-Setup-{#AppVersion}-windows-x64
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
UsePreviousAppDir=yes
DisableProgramGroupPage=yes
CloseApplications=yes
RestartApplications=no
UninstallDisplayIcon={app}\MarkItDownBase.exe
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#BundleDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\MarkItDown Base Preview"; Filename: "{app}\MarkItDownBase.exe"; WorkingDir: "{app}"

; 不使用 InstallDelete／UninstallDelete；重新安裝只覆寫受管檔案，保留使用者檔案。

[Code]
var
  ObsoleteNames, ObsoleteHashes, AddedNames, TargetNames: TStringList;
  IsTransition: Boolean;

#include TransitionRules

function NativeAttributes(Name: String): LongWord;
  external 'GetFileAttributesW@kernel32.dll stdcall';

function SafeAncestors(Name: String): Boolean;
var Parent: String; Attr: LongWord;
begin
  Result := False;
  Name := ExpandFileName(Name);
  while Name <> '' do begin
    Attr := NativeAttributes(Name);
    if (Attr <> $FFFFFFFF) and ((Attr and $400) <> 0) then exit;
    Parent := ExtractFileDir(RemoveBackslashUnlessRoot(Name));
    if Parent = Name then break;
    Name := Parent;
  end;
  Result := True;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  InstalledVersion, InstalledDir, CatalogPath, Name: String;
  InstalledPacked, TargetPacked: Int64;
  I: Integer;
begin
  Result := '';
  IsTransition := False;
  if not SafeAncestors(WizardDirValue) then begin
    Result := 'Installation path contains a reparse point.'; exit;
  end;
  // 每個目標檔的父鏈也要檢查，避免 _internal 等子目錄被 junction 替換。
  for I := 0 to TargetNames.Count - 1 do begin
    Name := AddBackslash(WizardDirValue) + TargetNames[I];
    if not SafeAncestors(Name) or DirExists(Name) then begin
      Result := 'A target file path is linked or replaced with a directory.'; exit;
    end;
  end;
  if not RegKeyExists(HKCU64, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{DB61BCA4-7678-4BEA-9140-27B548460D75}_is1') then begin
    if FileExists(AddBackslash(WizardDirValue) + 'base-install-catalog.json') or
       FileExists(AddBackslash(WizardDirValue) + 'MarkItDownBase.exe') then
      Result := 'An unregistered installation already exists. Select a fresh directory.';
    exit;
  end;
  if not RegQueryStringValue(HKCU64, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{DB61BCA4-7678-4BEA-9140-27B548460D75}_is1', 'DisplayVersion', InstalledVersion) or
     not RegQueryStringValue(HKCU64, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{DB61BCA4-7678-4BEA-9140-27B548460D75}_is1', 'InstallLocation', InstalledDir) then begin
    Result := 'Existing registration is incomplete.'; exit;
  end;
  if CompareText(AddBackslash(ExpandFileName(InstalledDir)), AddBackslash(ExpandFileName(WizardDirValue))) <> 0 then begin
    Result := 'Upgrade and repair must use the registered installation directory.'; exit;
  end;
  if not StrToVersion(InstalledVersion, InstalledPacked) or not StrToVersion('{#AppVersion}', TargetPacked) then begin
    Result := 'Existing version is invalid.'; exit;
  end;
  // 降版必須明確指定；此為已知版本重新安裝，不宣稱中斷時可自動交易回復。
  if (ComparePackedVersion(InstalledPacked, TargetPacked) > 0) and
     (ExpandConstant('{param:ALLOWDOWNGRADE|0}') <> '1') then begin
    Result := 'Downgrade blocked. Explicit /ALLOWDOWNGRADE=1 is required.'; exit;
  end;
  CatalogPath := AddBackslash(WizardDirValue) + 'base-install-catalog.json';
  if not SafeAncestors(CatalogPath) or not FileExists(CatalogPath) then begin
    Result := 'Existing catalog is missing or linked.'; exit;
  end;
  if InstalledVersion = '{#AppVersion}' then begin
    if CompareText(GetSHA256OfFile(CatalogPath), TargetCatalogHash) <> 0 then
      Result := 'Same-version catalog differs from this build. Repair with the matching installer.';
    exit;
  end;
  if (InstalledVersion <> PreviousVersion) or
     (CompareText(GetSHA256OfFile(CatalogPath), PreviousCatalogHash) <> 0) then begin
    Result := 'This installer has no verified transition from the installed build.'; exit;
  end;
  // 新版新增的受管路徑若已被未知檔案占用，不能把使用者文件直接覆寫成程式資產。
  for I := 0 to AddedNames.Count - 1 do
    if FileExists(AddBackslash(WizardDirValue) + AddedNames[I]) then begin
      Result := 'A new application path is occupied by an untracked file.'; exit;
    end;
  // 只容許移除已知前版且 hash 未變的 obsolete 檔；有使用者修改就先停止，不遞迴刪目錄。
  for I := 0 to ObsoleteNames.Count - 1 do begin
    Name := AddBackslash(WizardDirValue) + ObsoleteNames[I];
    if not SafeAncestors(Name) then begin Result := 'Obsolete path contains a reparse point.'; exit; end;
    if DirExists(Name) then begin Result := 'Obsolete file was replaced with a directory.'; exit; end;
    if FileExists(Name) and (CompareText(GetSHA256OfFile(Name), ObsoleteHashes[I]) <> 0) then begin
      Result := 'Obsolete owned file changed. Back it up before upgrading.'; exit;
    end;
  end;
  IsTransition := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var I: Integer; Name: String;
begin
  if (CurStep = ssPostInstall) and IsTransition then
    for I := 0 to ObsoleteNames.Count - 1 do begin
      Name := AddBackslash(WizardDirValue) + ObsoleteNames[I];
      if FileExists(Name) then begin
        if not SafeAncestors(Name) or (CompareText(GetSHA256OfFile(Name), ObsoleteHashes[I]) <> 0) then
          RaiseException('Obsolete file changed during installation; preserved for manual recovery.');
        if not DeleteFile(Name) then RaiseException('Cannot remove obsolete owned file.');
      end;
    end;
end;

procedure InitializeWizard;
begin
  ObsoleteNames := TStringList.Create;
  ObsoleteHashes := TStringList.Create;
  AddedNames := TStringList.Create;
  TargetNames := TStringList.Create;
  PopulateObsolete;
end;
