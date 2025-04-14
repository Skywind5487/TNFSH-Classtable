---
title: TNFSHClassTable
emoji: 🏆
colorFrom: yellow
colorTo: yellow
sdk: gradio
sdk_version: 5.23.0
app_file: app.py
pinned: false
license: mit
short_description: 'parse class table of Tnfsh '
python_version: '3.13'
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference


# 🏫 TNFSH 課表查詢系統

**臺南一中專屬的課表查詢與管理工具**  
提供班級與教師課表查詢、資料匯出、AI 助手、調課查詢等功能，讓課表管理更輕鬆！

---

## 立刻體驗
[Hugging Face](https://huggingface.co/spaces/Skywind5487/TNFSHClassTable)

## 🚀 核心功能

### 📊 課表解析
- **班級與教師課表解析**：支援多種格式匯出，包括 `JSON`、`CSV`、`ICS`。
- **索引資料**：快速查詢班級與教師的課表連結與詳細資訊。

### 📅 日曆整合
- **ICS 格式**：支援匯入 Google Calendar、Outlook 等行事曆軟體。
  - 教學: [Google Calendar](https://support.google.com/calendar/answer/37118?hl=zh-Hant)
  - 手機請調整到電腦板模式
- **CSV 格式**：適合匯入 Google Calendar，提供簡易匯入步驟。
- **重複規則**：自動處理學期重複，無需手動調整。

### 🤖 AI 助手(Unstable)
- **自然語言查詢**：支援班級課表、教師課表、竹園Wiki 內容查詢。
- **調課建議**：提供教師調課可能性分析（Alpha 功能）。



### 🛠️ 使用教學
#### 1. 下載專案
點擊[下載專案](https://github.com/Skywind5487/TNFSH-Classtable/archive/refs/heads/main.zip)來下載最新的 repo。

#### 2. 解壓縮專案
1. 在「下載」資料夾找到 `TNFSH-Classtable-main.zip`。
2. 右鍵點擊壓縮檔，選擇「解壓縮全部」。
3. 將產生的資料夾 `TNFSH-Classtable-main` 移到你喜歡的地方(下稱專案資料夾)。

### 3. 安裝環境

#### 1️⃣ 安裝 `uv`
`uv` 是一個 Python 的虛擬環境管理工具。
請在專案資料夾打開 powershell / 終端機。
對於Windows用戶，顯示的會是`在終端中開啟`
參考資料: [參考資料](https://dev.to/codemee/shi-yong-uv-guan-li-python-huan-jing-53hg)

- **Windows**：
  在 PowerShell 中輸入：
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

- **macOS/Linux**：
  在終端機中輸入：
  ```bash
  wget -qO- https://astral.sh/uv/install.sh | sh
  ```

#### 2️⃣ 安裝 Python
關閉視窗後重新開啟 PowerShell 或終端機，並執行以下命令：
```bash
uv python install
```

#### 3️⃣ 安裝依賴
使用 `uv` 建立虛擬環境並安裝依賴：
```bash
uv venv
```

### 4. 執行專案
在虛擬環境中執行主程式：
```bash
uv python run.py
```

### 5. 使用 Gradio
等待約 10 秒，程式應該會自動開啟瀏覽器，依照頁面的指引使用即可！

---

## 🧪 測試

還沒寫完。執行單元測試以確保功能正常：
```bash
python interface.py
```

### 2. 使用 AI 助手
- **查詢課表**：例如「請告訴我 205 班的課表」。
- **查詢 Wiki**：例如「請告訴我顏永進老師的 Wiki 內容」。

### 3. 匯出課表
- 選擇班級或教師，並選擇匯出格式（`JSON`、`CSV`、`ICS`）。

---

## 📜 專案架構
- **`interface.py`**：Gradio 介面與 AI 助手實作。
- **`backend.py`**：課表解析與資料處理核心邏輯。
- **`README.md`**：專案說明與使用指南。

---

## License
我們使用[MIT](LICENSE)許可證。




## 📞 聯絡我們
如有任何問題或建議，歡迎透過 [GitHub Issues](https://github.com/Skywind5487/TNFSH-Classtable/issues) 聯繫我們！
