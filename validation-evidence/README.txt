GAME TUNER VALIDATION EVIDENCE
Game Tuner 遊戲驗證資料

====================
中文指示
====================

目的
每款 Game 使用一個獨立資料夾，收集 Read、Output、Write、Backup、Restore 的驗證證據。不同 Game 的資料不可混放。

開始前
1. 閱讀 Game 資料夾內的 COLLECT.txt，確認目前允許測試到哪個 Phase。
2. 記錄 Platform、Game Version、Game Tuner Version、Rule Manifest Version 與測試日期。
3. Write 或 Restore 前，必須完全關閉 Game 與 Launcher，並暫停 Cloud Sync。
4. 不要重新命名四個編號資料夾。
5. GUI 未顯示精確匹配的 write_candidate: verified 時，禁止 Write。

01-read-evidence
- game-ui-before.png：Game 內完整 Graphics/Video 設定畫面。
- game-tuner-read.png：Game Tuner 展開後顯示的相同設定。
- environment.txt：Platform、Game Version、Game Tuner Version、Rule Version、測試日期。
- read-comparison.txt：每個欄位的 Game Value、Game Tuner Value、Pass/Fail/N/A。

Read 判定
- Pass：所有宣告支援欄位一致。
- N/A：只有 Game 本身沒有該功能時可使用。
- Fail：Game 有該欄位，但 Game Tuner 未顯示或 Value 錯誤。

02-diagnostic-output
- Metadata-only Diagnostic ZIP：不勾選 Include anonymized config content。
- Selected-content Diagnostic ZIP：勾選內容並使用 Recommended，只透過核准的 Private Channel 交付。
- verification.log：Check Rules 或 Import Rules 失敗時附上。
- export-result.png：GUI 顯示 Export 成功的畫面。

不要額外選取 input、key、binding、save、log、cache 或無關檔案。不要公開上傳 Diagnostic ZIP。

03-write-evidence
只在 COLLECT.txt 明確允許且 GUI 顯示 write_candidate: verified 時使用。每次只修改一個 Setting：
- <setting>-before.png：修改前 Game Value。
- <setting>-apply.png：Game Tuner Apply 成功訊息。
- <setting>-after-game.png：啟動 Game 後的新 Value。
- <setting>-readback.png：重開 Game Tuner 後讀回的新 Value。
- write-results.txt：Original Value、Test Value、Apply、Persistence、Read-back、Restore 結果。

任何 Setting 失敗時，停止後續 Write，先 Restore 原值並回報步驟與錯誤訊息。

04-backup-restore
- Game Tuner Export Selected 產生的 JSON Backup。
- backup-folder.png：Automatic Backup 資料夾與檔名，不要截出 Windows Username。
- restore-result.png：Import/Restore 成功訊息。
- restored-game-ui.png：Game 內已回到 Original Value。

Privacy 與 Git
Screenshot、ZIP、log、Config、Backup 預設由 Git 忽略，只能透過核准的 Private Channel 交付。只有 README.txt 與 COLLECT.txt 應進入 Version Control。Benchmark/Demo 通過只代表該 Tool，不代表 Full Game 支援。

====================
English Instructions
====================

Purpose
Use one folder per game to collect evidence for Read, Output, Write, Backup, and Restore. Never mix evidence from different games.

Before testing
1. Read the game's COLLECT.txt and confirm the permitted phase.
2. Record platform, game version, Game Tuner version, rule manifest version, and test date.
3. Fully close the game and launcher and pause cloud sync before Write or Restore.
4. Do not rename the four numbered folders.
5. Do not test Write unless the GUI shows an exact write_candidate: verified match.

01-read-evidence
Store full in-game Graphics/Video screenshots, matching Game Tuner screenshots, environment.txt, and a field-by-field read-comparison.txt.

02-diagnostic-output
Store metadata-only and selected-content diagnostic ZIPs, verification.log when updates fail, and an export-success screenshot. Never upload diagnostic ZIPs publicly.

03-write-evidence
Change one setting at a time. Capture the original value, Apply result, in-game persisted value, Game Tuner read-back, and result notes.

04-backup-restore
Store the Export Selected JSON backup, automatic-backup screenshot, restore/import result, and restored in-game value.

Privacy and Git
Evidence is ignored by Git and must use the approved private channel. Only README.txt and COLLECT.txt belong in version control. Benchmark/demo success never proves full-game support.
