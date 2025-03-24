# 🏫 TNFSH Classtable

本專案旨在處理台南一中班級課表的相關資料，提供多種功能與格式支援，並整合圖形化介面以提升使用體驗。

---
## 即刻體驗
[點我體驗colab](https://colab.research.google.com/github/Skywind5487/TNFSH-Classtable/blob/main/tnfsh-classtable-alpha.ipynb)
依照頁面指引即可!

## ✨ Features

### 🗂️ 課表解析
- 支援南一中課表索引解析：
  - **匯出格式**：`JSON` (index, reverse_index, all)
- 支援南一中課表解析：
  - 適用於老師與班級課表
  - **匯出格式**：`JSON`, `CSV`, `ICS`

### 📋 新竹園 Wiki 整合
- 獲取教師索引資料：
  - **匯出格式**：`JSON` (index, reverse_index)

### 🌐 圖形化 Web 介面
- 使用 **Gradio** 提供直觀的網頁操作介面：
  - **功能**：顯示課表、匯出資料
  - **匯出格式**：`JSON`, `CSV`, `ICS`

### 📅 日曆功能
- 支援課表匯出為日曆格式：
  - **檔名格式**：`type_target.[csv, ics]`
  - **重複規則**：RRule (重複至 2/1 或 7/1 再加一週)
- 注意：Google Calendar 無法解析 CSV 的重複規則。

---

## 📅 日曆內容

- **檔名格式**：`type_target.[csv, ics]`
- **重複規則**：RRule (重複至 2/1 或 7/1 再加一週)

> 注意：Google Calendar 無法解析 CSV 的重複規則。

---

## 📂 專案架構

本專案以單檔執行為理念，適應簡單易用的 Colab 環境：[點我體驗](https://colab.research.google.com/github/Skywind5487/TNFSH-Classtable/blob/main/tnfsh-classtable-alpha.ipynb)

專案主要分為以下幾個 Class：

---

### 1. `NewWikiTeacherIndex`
**屬性**：
- `teacher_index`：教師索引資料。
- `reverse_index`：反向教師索引資料。

**方法**：
- `export(export_type: str, filepath: Optional[str])`：匯出索引資料，支援格式：`JSON`。export_type: `index`,`reverse_index`, `all`

---

### 2. `TNFSHClassTableIndex`
**屬性**：
- `index`：班級與教師課表索引資料。
- `reverse_index`：反向索引資料。

**方法**：
- `export_json(export_type: str, filepath: Optional[str])`：匯出索引資料，支援格式：`JSON`。export_type: `index`,`reverse_index`, `all`
- `refresh()`：重新載入索引資料。

---

### 3. `TNFSHClassTable`
**屬性**：
- `url`：課表網頁的 URL。
- `soup`：課表網頁經過 html parser 的檔案
- `lessons`：課程時間對應表。
- `table`：結構化的課表資料。
- `last_update`：課表最後更新時間。

**方法**：
- `export(type: str, filepath: Optional[str])`：匯出課表資料，支援格式(type)：`JSON`, `CSV`, `ICS`。

---

### 4. `GradioInterface`
**屬性**：
- `grades`：年級選項（如：`["一", "二", "三"]`）。
- `classes`：班級選項（如：`["01", "02", ..., "26"]`）。
- `export_formats`：匯出格式選項（如：`["JSON", "CSV", "ICS"]`）。

**方法**：
- `display(args: List[str])`：顯示課表。
- `save_json(args: List[str])`：儲存課表為 JSON 格式。
- `save_csv(args: List[str])`：儲存課表為 CSV 格式。
- `save_ics(args: List[str])`：儲存課表為 ICS 格式。
- `run()`：啟動 Gradio 介面。

---

### 5. `App`
**方法**：
- `run(interface_type: str)`：啟動應用程式，支援介面類型：`"gradio"` 或 `"both"`。

---

## 🚀 使用方式

### 1. 下載專案
點擊[下載專案](https://github.com/Skywind5487/TNFSH-Classtable/archive/refs/heads/main.zip)來下載最新的 repo。

### 2. 解壓縮專案
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

還沒寫完。
執行單元測試以確保功能正常：
```bash
pytest tests/
```

---


## 📚 資料來源

- [台南一中課表根目錄](http://w3.tnfsh.tn.edu.tw/deanofstudies/course/course.html)
- [新竹園 Wiki](https://tnfshwiki.tfcis.org)
- [台南一中官網](https://www.tnfsh.tn.edu.tw)

---

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request 來改進本專案。

---

## 📜 授權

本專案採用 [MIT License](LICENSE) 授權。
