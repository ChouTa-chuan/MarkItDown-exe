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
UsePreviousAppDir=no
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
