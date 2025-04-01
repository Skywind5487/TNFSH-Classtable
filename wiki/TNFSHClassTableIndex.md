# 課表功能索引

## 功能列表
- [Gradio 介面](Gradiointerface.md)
- [新竹園 Wiki 索引](NewWikiIndex.md)
- [台南一中課表功能](TNFSHClassTable.md)
- [TNFSHClassTableIndex 類別](TNFSHClassTableIndex.md)

## 使用方式
1. 選擇所需功能
2. 點擊連結查看詳細說明
3. 依照說明操作

## 注意事項
- 請確保使用最新版本
- 如有問題，請參考對應的說明文件

# TNFSHClassTableIndex 類別

`TNFSHClassTableIndex` 是台南一中課表索引的單例類別，用於管理課表資料的索引與反查表。

## 屬性

- `base_url` (str): 課表資料的基礎 URL。
- `index` (Dict): 完整的課表索引資料。
- `reverse_index` (Dict): 反查表，將老師/班級對應到其 URL 和分類。

## 方法

### `get_instance()`

取得 `TNFSHClassTableIndex` 的單例實例。

**返回值**:
- `TNFSHClassTableIndex`: 單例實例。

**範例**:
```python
index = TNFSHClassTableIndex.get_instance()
```

### `export_json(export_type: str = "all", filepath: Optional[str] = None)`

匯出索引資料為 JSON 格式。

**參數**:
- `export_type` (str): 要匯出的資料類型，可選值為 "index"、"reverse_index" 或 "all"（預設）。
- `filepath` (Optional[str]): 輸出檔案路徑，若未指定則自動生成。

**返回值**:
- `str`: 實際儲存的檔案路徑。

**範例**:
```python
filepath = index.export_json(export_type="index")
```

### `refresh()`

重新載入索引資料。

**範例**:
```python
index.refresh()
```

### `_get_index()`

取得完整的台南一中課表索引。

**返回值**:
- `Dict`: 包含課表索引的字典。

### `_build_reverse_index()`

建立反查表，將老師/班級對應到其 URL 和分類。

**返回值**:
- `Dict`: 反查表結構為 {老師/班級: {url: url, category: category}}。