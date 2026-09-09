# 遊戲完整支援驗證計畫

本計畫用於驗證指定遊戲是否能正確完成 Read、Write、備份、還原及診斷輸出，最後再更新正式 support list。測試人員只使用 `GameTuner.exe`、Game Tuner GUI、遊戲設定畫面及 Windows 檔案總管；不需要 Python、CLI 或終端機。

詳細操作步驟與結果表請使用 [full-game-validation.md](full-game-validation.md)。

## 驗證狀態流程

每款遊戲必須依序通過以下狀態，不可直接跳到完整支援：

1. `candidate`：確認遊戲能被掃描，並收集 metadata-only 與匿名內容診斷包。
2. `read_verified`：維護者確認設定檔正確，Game Tuner 顯示值與遊戲 GUI 一致。
3. `write_candidate`：維護者發布精確匹配平台、版本及結構指紋的測試規則；測試人員可在明確同意後進行受保護寫入。
4. `write_verified`：所有宣告支援的設定均通過寫入、遊戲內確認、重新讀取、備份與還原，才更新正式 support list。

`N/A` 表示遊戲本身沒有該設定，不算失敗。遊戲有該設定但 Game Tuner 未顯示、讀錯或寫錯時，必須記為失敗。

## 清單正規化

原始清單中 `Cyberpunk 2077` 重複一次，合併後共有 18 款唯一遊戲。測試前必須使用掃描結果中的實際名稱，特別注意：

- `Diablo 4` 以快取名稱 `Diablo IV` 比對。
- `Diablo IV` 本輪限定 Battle.net 版本；必須先有 Battle.net scanner，且 OneDrive `LocalPrefs.txt` 必須可離線讀取。
- `Final Fantasy XIV` 目前快取鍵為 `Final Fantasy XIV: Dawntrail`，Wiki 頁面為 `Final Fantasy XIV Online`。
- `Arc Raiders` 目前快取鍵為 `ARC Raiders`。
- `Assassin's Creed Black Flag Resynced` 尚無快取路徑，必須先確認產品正式名稱及設定位置。

## 共通前置條件

每款遊戲開始測試前：

- 使用指定的平台安裝並至少啟動一次遊戲。
- 在遊戲 GUI 儲存一次畫面設定，確保設定檔已建立。
- 記錄平台、遊戲版本、Game Tuner EXE 版本及驗證名單版本。
- Write 測試前關閉遊戲與 launcher，並暫停該遊戲的雲端同步。
- 每款遊戲分開產生診斷 ZIP，不要把多款遊戲混在第一份驗證證據內。
- 未取得精確版本及結構指紋前，不得發布 `write_candidate`。

## 批次 1：優先完整驗證

這批已有專用 parser/writer，或已有實機解析證據，最適合先打通完整流程。

| # | 遊戲 | 目前依據 | 第一個目標 | Write 前置風險 |
|---|---|---|---|---|
| 1 | Cyberpunk 2077 | 已有專用 JSON parser/writer；需重新驗證目前版本 | Read → Output → `write_candidate` → Write | 遊戲更新可能改變 JSON 欄位 |
| 2 | Black Myth Wukong | 專用 Read parser；Unreal INI writer；實機已讀到 8 個欄位 | 完整驗證 | 只可寫 `GameUserSettings.ini`，不得碰同資料夾其他 INI |
| 3 | Forza Horizon 6 | 專用 XML parser/writer；已有本機解析紀錄 | 完整驗證 | XML 欄位與遊戲版本需精確匹配 |

完成條件：三款逐一完成 [full-game-validation.md](full-game-validation.md) 全部章節；每款獨立從 `write_candidate` 升級為 `write_verified`。

## 批次 2：引擎格式候選

這批有候選路徑，且部分可使用 Unreal 通用解析，但不能因共用格式就直接宣告 Write 支援。

| # | 遊戲 | 候選格式/路徑 | 驗證順序 | 可能需要的工作 |
|---|---|---|---|---|
| 4 | ARC Raiders | Unreal `GameUserSettings.ini` 類型 | Read/Output 先行 | 驗證通用 Unreal parser/writer 是否涵蓋實際鍵值 |
| 5 | Returnal | Steam/Epic Unreal Config 資料夾 | 分平台 Read/Output | Steam 與 Epic 必須建立不同規則及指紋 |
| 6 | Fortnite | Unreal `WindowsClient` Config | Read/Output 先行 | 避免收集 input、binding、cache 等非圖形檔 |
| 7 | F1 25 | 專用 XML Read parser | 先 Read，補專用 writer 後再測 Write | 現有通用 XML writer 不代表 F1 寫入支援 |

完成條件：每款先取得正確設定檔與遊戲 GUI 對照證據；只有 parser/writer 測試通過者才發布 `write_candidate`。

## 批次 3：Registry、XML 與自訂格式

這批已有設定路徑，但格式或寫入方式風險較高，必須先確認 Read，再逐款建立專用 writer。

| # | 遊戲 | 候選格式/路徑 | 主要風險 |
|---|---|---|---|
| 8 | Shadow of the Tomb Raider | Windows Registry | Registry 寫入不可用檔案備份方式直接驗證，需特別確認還原策略 |
| 9 | Horizon Zero Dawn Remastered | Documents + Registry | 可能同時存在檔案與 Registry，需確認實際權威來源 |
| 10 | Grand Theft Auto V Enhanced | `settings.xml` | 目前沒有 GTA 專用 parser/writer，不能沿用 Forza XML 假設 |
| 11 | Red Dead Redemption 2 | `Settings` 資料夾 | 需辨識 `system.xml` 等真正圖形檔並排除其他資料 |
| 12 | Monster Hunter Wilds Benchmark | Benchmark 安裝目錄 `config.ini` | 只驗證 Benchmark，不代表 Monster Hunter Wilds 正式版支援；現有 Unreal writer 不代表 RE Engine 格式可寫 |

完成條件：每款建立格式專用 fixture 與測試；Read 全欄位吻合後，另行審核 writer 才能進入 `write_candidate`。

## 批次 4：先做路徑與 Read 探索

這批目前只有候選路徑或完全沒有快取，先收集資料，不安排 Write 測試。

| # | 遊戲 | 目前狀態 | 第一個交付物 |
|---|---|---|---|
| 13 | Baldur's Gate 3 | 有 `graphicSettings.lsx` 等路徑，無 LSX 專用 parser/writer | 匿名 LSX fixture + 遊戲 GUI 對照表 |
| 14 | Battlefield 6 | 有 Documents `settings` 路徑，格式未驗證 | 實際檔案清單 + metadata/content 診斷包 |
| 15 | Diablo IV（Battle.net） | 已知安裝與 `LocalPrefs.txt`，但 GUI 無 Battle.net scanner；OneDrive 檔案可能未下載 | Battle.net 掃描 + Documents 重導 + 匿名 LocalPrefs fixture |
| 16 | DOOM: The Dark Ages | 有 Saved Games `base` 路徑，格式未驗證 | 真正圖形設定檔及欄位鍵值 |
| 17 | Final Fantasy XIV | 有 Documents 設定資料夾，名稱與版本別名需確認 | 掃描名稱、實際設定檔及遊戲 UI 對照 |
| 18 | Assassin's Creed Black Flag Resynced | 無快取路徑 | 正式掃描名稱、平台、版本、設定檔位置及匿名內容 |

完成條件：先達成 `read_verified`。在沒有專用 writer、可重現 fixture 及自動測試前，不得發布 `write_candidate`。

## 每款遊戲的執行票

每款遊戲都使用以下一張獨立測試票，不要一次將整批標為完成：

| 項目 | 結果/證據 |
|---|---|
| 掃描名稱與平台正確 | Pass / Fail + screenshot |
| 設定檔找到且屬於該遊戲 | Pass / Fail + diagnostic ZIP |
| 遊戲版本成功取得 | 版本字串 / Unknown |
| Read：所有宣告欄位與遊戲 GUI 一致 | Pass / Fail + 對照表 |
| Metadata-only ZIP | Pass / Fail + ZIP |
| Include-content ZIP | Pass / Fail + ZIP（私人管道） |
| Parser fixture 與自動測試 | Pass / Fail（維護者） |
| `write_candidate` 精確規則發布 | Manifest 版本 |
| 寫入同意閘門 | Pass / Fail |
| Write：每個宣告欄位逐項測試 | Pass / Fail + 對照表 |
| 遊戲啟動後設定持續存在 | Pass / Fail |
| Game Tuner 重新讀取正確 | Pass / Fail |
| 自動備份存在 | Pass / Fail |
| 原值還原成功 | Pass / Fail |
| Export/Import 還原成功 | Pass / Fail |
| 最終決策 | `write_verified` / `read_verified` / 保持 candidate |

## Support List 更新規則

- Read、Output 通過但 Write 尚未通過：只發布 `read_verified`。
- 準備進行受控 Write 測試：發布精確的 `write_candidate`，不可使用萬用版本或指紋。
- 全部驗收通過：將同一筆精確規則升級為 `write_verified`。
- 遊戲更新造成版本或指紋改變：停止 Write，建立新候選驗證；舊規則不得自動套用。
- 任一欄位讀錯、寫錯、備份缺失、還原失敗、隱私外洩或程式崩潰：不得列入完整 support list。

## 建議執行順序

1. Cyberpunk 2077
2. Black Myth Wukong
3. Forza Horizon 6
4. F1 25（先 Read，再補 writer）
5. ARC Raiders
6. Returnal（Steam、Epic 分開）
7. Fortnite
8. Monster Hunter Wilds Benchmark
9. Shadow of the Tomb Raider
10. Horizon Zero Dawn Remastered
11. Grand Theft Auto V Enhanced
12. Red Dead Redemption 2
13. Baldur's Gate 3
14. Battlefield 6
15. Diablo IV（Battle.net）
16. DOOM: The Dark Ages
17. Final Fantasy XIV
18. Assassin's Creed Black Flag Resynced
