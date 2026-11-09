// 此檔於 [Code] 內引入；只操作固定來源清單，不把 marker 當任意路徑或刪除權限。
function PendingPath: String;
begin
  Result := AddBackslash(WizardDirValue) + '.markitdown-install.pending';
end;

function MatchingRecoveryIntent(Name: String): Boolean;
var Size: Integer; Contents: AnsiString;
begin
  Result := False;
  // metadata 是固定長度 ASCII；先限制大小，避免讀入損壞或不屬於安裝器的大型文件。
  if not FileSize(Name, Size) then exit;
  if Size <> Length(RecoveryToken) then exit;
  Result := LoadStringFromFile(Name, Contents) and (Contents = RecoveryToken);
end;

function RecoveryIntentError: String;
var Name, TemporaryName: String;
begin
  Result := '';
  IsRecovery := False;
  Name := PendingPath;
  TemporaryName := Name + '.new';
  if not SafeAncestors(Name) or not SafeAncestors(TemporaryName) or
     DirExists(Name) or DirExists(TemporaryName) then begin
    Result := 'Recovery metadata path is linked or replaced with a directory.'; exit;
  end;
  if FileExists(Name) and FileExists(TemporaryName) then begin
    Result := 'Ambiguous recovery metadata. Preserve the installation for manual recovery.'; exit;
  end;
  if not FileExists(Name) then Name := TemporaryName;
  if not FileExists(Name) then exit;
  if not MatchingRecoveryIntent(Name) then begin
    Result := 'Interrupted installation belongs to another build or has damaged metadata. Use the matching installer.'; exit;
  end;
  if not ResumeConsent then begin
    if ExpandConstant('{param:RESUMEINSTALL|0}') = '1' then ResumeConsent := True
    else if not WizardSilent then
      ResumeConsent := MsgBox('The previous installation did not finish. Resume repair of application files in this directory? Documents and unrelated files will be preserved.', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
  end;
  if not ResumeConsent then begin
    Result := 'Interrupted installation detected. Confirm repair, or use /RESUMEINSTALL=1 with the matching installer.'; exit;
  end;
  IsRecovery := True;
end;

procedure WriteRecoveryIntent;
var Name, TemporaryName: String;
begin
  Name := PendingPath; TemporaryName := Name + '.new';
  if not SafeAncestors(Name) or not SafeAncestors(TemporaryName) then
    RaiseException('Recovery metadata path changed before installation.');
  if not ForceDirectories(WizardDirValue) then RaiseException('Cannot create the application directory.');
  if FileExists(Name) then begin
    if not MatchingRecoveryIntent(Name) then
      RaiseException('Recovery metadata changed before installation.');
    exit;
  end;
  // 完整寫入並關閉暫存檔後才 rename；不宣稱已處理斷電或部分 metadata 寫入損壞。
  if FileExists(TemporaryName) then begin
    if not MatchingRecoveryIntent(TemporaryName) then
      RaiseException('Recovery temporary metadata changed.');
  end else if not SaveStringToFile(TemporaryName, RecoveryToken, False) then
    RaiseException('Cannot write recovery intent; no application files should be installed.');
  if not RenameFile(TemporaryName, Name) then RaiseException('Cannot commit recovery intent.');
end;

procedure RecoveryCheckpoint(Stage: String);
#ifdef CiFaultInjection
var Signal: String;
#endif
begin
#ifdef CiFaultInjection
  // 僅明確編譯的 CI 測試安裝器含停點；一般安裝器沒有此分支或可被參數啟動的等待功能。
  if (not FaultFired) and (ExpandConstant('{param:CISTOP|}') = Stage) then begin
    FaultFired := True;
    Signal := ExpandConstant('{param:CISIGNAL|}');
    if (Signal = '') or FileExists(Signal) or not SaveStringToFile(Signal, AnsiString(Stage), False) then
      RaiseException('Cannot create the CI interruption handshake.');
    while True do Sleep(100);
  end;
#endif
end;

procedure BaseFileInstalled;
begin
  RecoveryCheckpoint('first-file');
end;

procedure FinishRecoveryIntent;
var I: Integer; Name: String;
begin
  // 最後逐檔驗 compiled source hash；不能只因為 Setup 沒報錯就清除未完成標記。
  for I := 0 to TargetNames.Count - 1 do begin
    Name := AddBackslash(WizardDirValue) + TargetNames[I];
    if not SafeAncestors(Name) or not FileExists(Name) or
       (CompareText(GetSHA256OfFile(Name), TargetHashes[I]) <> 0) then
      RaiseException('Installed application is incomplete; rerun the matching installer to resume repair.');
  end;
  Name := PendingPath;
  if not SafeAncestors(Name) or not MatchingRecoveryIntent(Name) then
    RaiseException('Recovery intent changed; preserve the matching installer.');
  if not DeleteFile(Name) then RaiseException('Cannot finish recovery intent; preserve the matching installer.');
end;
