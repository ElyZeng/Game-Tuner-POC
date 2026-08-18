# Game Tuner Collaboration TODO

這份清單依照「先完成本機資料，再建立客戶收集流程，最後擴充各遊戲 parser」排列。每次完成一個階段即可暫停。

## 1. 確認本機環境

- [x] 使用 `D:\AI\.venv` 執行專案
- [x] 安裝 `requirements.txt` 中的執行依賴
- [x] 安裝 `pytest`
- [x] 通過完整測試：`131 passed`（pytest 測試案例全部通過，不代表遊戲數量）
- [x] 通過依賴檢查：`python -m pip check`
- [x] 通過 Python 語法檢查：`python -m compileall`

## 2. 蒐集本機已安裝遊戲

目前已完成原始檔案擷取與標準欄位解析：

| 遊戲 | 解析度 | 螢幕模式 | VSync | 幀率限制 | 超採樣 | 幀生成 | 畫質預設 |
|---|---|---|---|---|---|---|---|
| Black Myth: Wukong | 3840x2160 | Borderless Windowed | Off | Unlimited | DLSS (mode 1) | On | Medium |
| Clair Obscur: Expedition 33 | 3840x2160 | Borderless Windowed | Off | Unlimited | XeSS (mode 5) | On (mode 1) | Medium |
| Counter-Strike 2 | 3840x2160 | Borderless Windowed | Off | 400 FPS | Off | N/A | N/A |
| Street Fighter 6 | 1680x1050 | Windowed | On | 60 FPS | Off | N/A | Custom |
| F1 25 | 1920x1080 | Fullscreen | Off | Unlimited | Off | Off | Custom |
| Forza Horizon 6 | 1920x1080 | Fullscreen | On | 120 FPS | Off | Off | Custom |

`未解析` 表示原始設定存在但 parser 尚未支援該欄位；`N/A` 表示遊戲或格式沒有該設定項。CS2 現在會保留所有 Steam 使用者目錄，能找到有 `cs2_video.txt` 的帳號，不再依賴目前登入者。黑神話與 33 號遠征隊已完成超採樣與幀生成欄位解析；mode 數值是遊戲設定檔的原始模式編號。Cyberpunk 2077 與 Baldur's Gate 3 的舊資料仍需重新驗證後再加入此表。

- [x] 黑神話：悟空：已解析解析度、全螢幕、畫質預設、超採樣、幀生成
- [x] 光與影：33 號遠征隊：已讀取 `GameUserSettings.ini` 並解析超採樣與幀生成
- [x] Counter-Strike 2：讀取所有 Steam 使用者目錄中的 `cs2_video.txt` 與 ConVar 設定
- [x] Street Fighter 6：已讀取 `config.ini` 並完成專用 parser
- [x] F1 25：已讀取 `hardware_settings_config.xml` 並完成專用 parser

每款遊戲執行：

```powershell
python cli.py query "遊戲英文名稱"
python cli.py detect "遊戲英文名稱"
python cli.py parse "遊戲英文名稱"
python cli.py export --games "遊戲英文名稱" --output "遊戲英文名稱-config.json"
```

完成條件：

- [x] `detect` 找到至少一個設定檔（黑神話、33 號遠征隊、CS2、SF6、F1 25、Forza 6）
- [x] 設定檔有 `found: true` 與 `content`
- [x] `parse` 輸出 `resolution` 與 `screen_mode`
- [x] `parse` 輸出 `quality_preset`、`upscaling` 或 `frame_generation`；不支援時輸出 `N/A`
- [x] 6 款遊戲已匯出匿名化 JSON 到 `local_exports/`，且沒有修改遊戲設定

第 2 階段已完成 6 款已驗證遊戲的本機匿名化 JSON 備份。

## 3. 處理已安裝但尚未找到設定檔的遊戲

- [x] Forza Horizon 6：已讀取 `UserConfigSelections` 並完成解析
- [x] Final Fantasy XVI：已啟動並重新偵測
- [x] Final Fantasy XVI：已調查 OneDrive、Documents、AppData 與遊戲目錄
- [x] Final Fantasy XVI：目前只找到截圖與 `steam_autocloud.vdf`，判定需要客戶協助提供原始設定資料
- [x] 確認目前 Wiki 路徑與本機路徑不含可讀圖形設定檔
- [ ] 將新找到的檔案保存為匿名化 fixture
- [ ] 為每個新格式新增 parser 測試

## 4. 建立客戶端原始資料收集流程

- [x] 建立只讀取、不修改的客戶收集命令：`tools/collect_configs.py`
- [x] 以 `--game`、`--platform` 與 `--game-version` 讓客戶指定遊戲資料
- [x] 只讀取 Wiki 已知設定檔，不掃描整個磁碟
- [x] 匯出相對路徑、格式、遊戲版本與原始內容
- [x] 在客戶端先解析並輸出 `parsed_settings`
- [x] 收集器預設匿名化後才產生匯出檔
- [x] 記錄 `collector_version` 與 `collection_time`

## 5. 建立匿名化與安全檢查

- [x] 將 Windows 使用者名稱替換為 `%USERPROFILE%`
- [x] 遮罩 Steam User ID 與 account ID
- [x] 移除 token、密碼、帳號識別碼與敏感設定行
- [ ] 不上傳整個 `AppData`、Steam `userdata` 或遊戲安裝目錄
- [ ] 匯出前顯示檔案清單
- [ ] 允許客戶取消或刪除單一檔案
- [ ] 在 README 說明資料用途
- [x] 本機匿名化匯出放在 `local_exports/`，並由 `.gitignore` 排除

## 6. 向客戶收集尚未安裝的遊戲

優先順序：

- [ ] Valorant
- [ ] Call of Duty: Black Ops 6
- [ ] EA Sports FC 26
- [ ] NBA 2K26
- [ ] Minecraft
- [ ] Roblox：RIVALS
- [ ] Elden Ring: Nightreign
- [ ] Nioh 3
- [ ] Like a Dragon: Kiwami 3
- [ ] Where Winds Meet
- [ ] Grand Theft Auto VI
- [ ] God of War Ragnarök

客戶需提供：正式英文名稱、平台與版本、設定檔相對路徑、匿名化原始內容，以及遊戲內實際顯示的解析度、畫面模式、畫質預設、超採樣與幀生成設定。

## 7. 為每款遊戲建立 parser

- [ ] 判斷格式：JSON、INI、XML、VCFG、Registry 或自訂格式
- [ ] 建立專用 parser
- [ ] 轉換成統一欄位
- [ ] 保留 `raw_value` 與 `source_key`
- [ ] 無法判斷時輸出 `null`，遊戲不支援時輸出 `N/A`
- [ ] 加入匿名化 fixture 與 pytest 測試
- [ ] 以客戶的 `observed_settings` 驗證解析結果

統一欄位：

```json
{
  "resolution": "1920x1080",
  "screen_mode": "Fullscreen",
  "quality_preset": "High",
  "upscaling": {"technology": "DLSS", "quality": "Quality"},
  "frame_generation": {"enabled": true, "technology": "DLSS"}
}
```

## 8. 整合 GUI 與客戶工作流程

- [ ] 顯示設定檔是否找到
- [ ] 顯示欄位來源檔案與原始 key
- [ ] 區分未找到檔案、未解析與遊戲不支援
- [ ] 提供只讀取的擷取功能
- [ ] 提供匿名化預覽
- [ ] 提供 JSON 匯出
- [ ] 使用 fixture 驗證未安裝遊戲的流程