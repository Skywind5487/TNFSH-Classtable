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


## 立刻體驗:HuggingFace

Hugging Face: [Skywind5487/TNFSHClassTable](https://huggingface.co/spaces/Skywind5487/TNFSHClassTable)

# 🏫 TNFSH 課表助手

在台南一中，學生每天都在追趕時間、翻找課表：
「下一節上什麼課？」📚、「明天有沒有體育課？」、「可不可以加到手機行事曆提醒我上課？」
這些看似小事，卻是我們每天都在面對的痛點。

本專案正是為了解決這樣的困擾而誕生———
打造一個專屬於台南一中學生的智慧課表系統，結合日曆整合、AI 助手與即時資訊，讓看課表從此變得方便、好用、智慧。

## 🔑 主要功能

- Google 日曆一鍵匯出 📅：讓 Google 日曆提醒你下一節，不再手動尋找。

- AI 助手整合竹園維基 🤖：找課程、問老師、問維基，一次搞定。

- 課表快速查詢 🗓️：班級與教師課表，一目了然。

- 調課查詢工具 🔄：創新算法與 AI 整合推薦，讓「我跟這個老師不熟不好調課」不再是困難！

## ⚡ 技術亮點
自主研發兩套調課策略:

- 互換策略 🔁：基於教師兩兩互相調課的算法。
- 輪換策略 🔄：基於教師向下一個位置調動形成環的算法。
- 深度優先搜尋 (DFS) 應用 🧠：利用 DFS 算法在複雜的課程調度中探索所有可能方案，實現高效且精確的調課規劃。

doc(尚在準備) 📄：[兩種調課算法](https://hackmd.io/@sky-wind-note/how_to_swap_course) 


## 🌟 核心理念
讓校園與科技接軌，將課表數位化，利用科技讓學生的學習生活更有條理、更加輕鬆 🎓。

---

# Github

Github: [Skywind5487/TNFSH-Classtable](https://github.com/Skywind5487/TNFSH-Classtable)

---


# 🛠️ 開發專區

## 專案Wiki
待補 [Wiki-index](/wiki/wiki_index.md)

## 環境配置

### 1. 下載專案
點擊[下載專案](https://github.com/Skywind5487/TNFSH-Classtable/archive/refs/heads/main.zip)來下載最新的 repo。

### 2. 解壓縮專案
1. 在「下載」資料夾找到 `TNFSH-Classtable-main.zip`。
2. 右鍵點擊壓縮檔，選擇「解壓縮全部」。
3. 將產生的資料夾 `TNFSH-Classtable-main` 移到你喜歡的地方(下稱專案資料夾)。

### 3. 安裝 python 環境

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
