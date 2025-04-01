# NewWikiIndex 類別

## 介紹
本專案整合了新竹園 Wiki 的教師索引功能，方便查詢教師相關資訊。

## 功能
- 查詢教師科目
- 取得教師 Wiki 頁面連結
- 建立教師反查表

## 使用方式
1. 輸入教師名稱
2. 系統會自動查詢並回傳相關資訊
3. 可取得教師的 Wiki 頁面連結

## 注意事項
- 教師名稱需完整且正確
- 部分教師可能無 Wiki 頁面

# NewWikiTeacherIndex 類別

`NewWikiTeacherIndex` 是新竹園 Wiki 教師索引的單例類別，用於管理教師資料的索引與反查表。

## 屬性

- `base_url` (str): 新竹園 Wiki 的基礎 URL。
- `index` (Dict): 完整的教師索引資料。
- `reverse_index` (Dict): 反查表，將教師名稱對應到其科目與 URL。

## 方法

### `get_instance()`

取得 `NewWikiTeacherIndex` 的單例實例。

**返回值**:
- `NewWikiTeacherIndex`: 單例實例。

**範例**:
```python
index = NewWikiTeacherIndex.get_instance()
```

### `export(export_type: str = "all", filepath: Optional[str] = None)`

匯出索引資料為 JSON 格式。

**參數**:
- `export_type` (str): 要匯出的資料類型，可選值為 "index"、"reverse_index" 或 "all"（預設）。
- `filepath` (Optional[str]): 輸出檔案路徑，若未指定則自動生成。

**返回值**:
- `str`: 實際儲存的檔案路徑。

**範例**:
```python
filepath = index.export(export_type="index")
```

### `refresh()`

重新載入索引資料。

**範例**:
```python
index.refresh()
```

### `_get_new_wiki_teacher_index()`

並發從新竹園 Wiki 網站取得教師索引。

**返回值**:
- `Dict`: 包含教師索引的字典。

### `_build_teacher_reverse_index()`

建立教師反查表，將教師名稱對應到其科目與 URL。

**返回值**:
- `Dict`: 反查表結構為 {教師名稱: {url: url, category: category}}。