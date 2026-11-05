; 每位使用者的開發預覽安裝包；需在 Windows 使用 Inno Setup 6.3+ 編譯。
#ifndef BundleDir
  #error BundleDir is required
#endif
#ifndef OutputDir
  #error OutputDir is required
#endif
#ifndef AppVersion
  #error AppVersion is required
#endif
#if !FileExists(AddBackslash(BundleDir) + "MarkItDownDesktop.exe")
  #error Windows executable is missing
#endif
#if !FileExists(AddBackslash(BundleDir) + "bundle-manifest.json")
  #error Verified bundle manifest is missing
#endif

[Setup]
AppId={{28905A59-5D70-42DD-8C28-2D41A93E1B66}
AppName=MarkItDown Desktop (Development Preview)
AppVersion={#AppVersion}
AppVerName=MarkItDown Desktop {#AppVersion} (Development Preview)
AppPublisher=MarkItDown Desktop contributors
DefaultDirName={localappdata}\Programs\MarkItDownDesktop
DisableDirPage=yes
DefaultGroupName=MarkItDown Desktop
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
MinVersion=10.0.17763
OutputDir={#OutputDir}
OutputBaseFilename=MarkItDownDesktop-Setup-{#AppVersion}-windows-x64
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
UninstallDisplayIcon={app}\MarkItDownDesktop.exe
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[InstallDelete]
; 升級時替換受管理的原生依賴，使用者設定與模型放在此目錄之外。
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "{#BundleDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\MarkItDown Desktop"; Filename: "{app}\MarkItDownDesktop.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\MarkItDown Desktop"; Filename: "{app}\MarkItDownDesktop.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\MarkItDownDesktop.exe"; Description: "Launch MarkItDown Desktop"; Flags: nowait postinstall skipifsilent

; 不設定 UninstallDelete：安裝目錄外的使用者設定、下載模型與輸出文件須保留。
