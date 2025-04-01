# TNFSHClassTable 類別

`TNFSHClassTable` 是台南一中課表處理的主要類別，負責從學校網站擷取課表資訊並進行解析，提供多種匯出格式。

## 屬性

- `url` (str): 課表網頁的 URL。
- `soup` (BeautifulSoup): 解析後的 HTML 內容。
- `lessons` (Dict[str, List[str]]): 課程時間對應表。
- `table` (List[List[Dict[str, Dict[str, str]]]]): 結構化的課表資料。
    - period , day
- `transpose_table` (List[List[Dict[str, Dict[str, str]]]]): 轉置後的課表資料。
    - day, period
- `last_update` (str): 課表最後更新時間。

## 方法

### `export(type: str, filepath: Optional[str] = None)`

匯出課表資料。

**參數**:
- `type` (str): 要匯出的資料類型，可選值為 "json"、"csv" 或 "ics"。
- `filepath` (Optional[str]): 輸出檔案路徑，若未指定則自動生成。

**返回值**:
- `str`: 實際儲存的檔案路徑。

**範例**:
```python
table = TNFSHClassTable("101")
filepath = table.export(type="json")
```

### `_export_to_json(filepath: Optional[str] = None)`

將課表資料匯出為 JSON 格式。

**參數**:
- `filepath` (Optional[str]): 輸出檔案路徑，若未指定則自動生成。

**返回值**:
- `str`: 實際儲存的檔案路徑。

### `_export_to_csv(filepath: Optional[str] = None)`

將課表資料匯出為 CSV 格式。

**參數**:
- `filepath` (Optional[str]): 輸出檔案路徑，若未指定則自動生成。

**返回值**:
- `str`: 實際儲存的檔案路徑。

### `_export_to_ics(filepath: Optional[str] = None)`

將課表資料匯出為 ICS 格式。

**參數**:
- `filepath` (Optional[str]): 輸出檔案路徑，若未指定則自動生成。

**返回值**:
- `str`: 實際儲存的檔案路徑。