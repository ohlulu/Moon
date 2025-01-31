# Moon 🌕 - 虛擬幣投資分析工具

一個強大的虛擬幣投資分析與篩選工具，幫助投資者做出更明智的投資決策。

## 功能特點 ✨

- 即時市場數據追蹤
- 技術指標分析
- 投資組合風險評估
- 自動化篩選策略
- 歷史數據分析與視覺化

## 工作流程 🔄
### 前置作業
  - 使用 cctx 連接 binance 交易所，收集市值前 500 的現貨（USDT本位）、U本位合約的交易對，並儲存數據(mongodb)

### 數據收集
  - 使用 twetter api 蒐集所有交易對的新聞
  - 使用 newsapi 蒐集所有交易對的新聞
  - 儲存到 mongodb
  - 新聞需要標記時間
  - 後續繼續蒐集新聞的時候，可以根據時間戳去搜尋，不需要每次都從頭蒐集
  - 第一次預設蒐集最近 10 天

### 數據分析
  - 技術指標計算（RSI、MACD、ROC、BollingerBands、移動平均線等）
  - 市場趨勢分析
  - 波動性評估

### 篩選機制
  - 根據用戶定義的條件進行篩選
  - 風險評估指標計算
  - 投資建議生成

### 結果展示
  - 數據視覺化
  - 投資組合分析報告
  - 風險警告通知

## 專案架構
```
project_root/
├── README.md
├── setup.py                    # 專案安裝與設定檔
├── requirements.txt            # Python 套件相依
├── .env                        # 環境變數
│
├── src/
│   ├── main.py                 # 主程式進入點
│   ├── collection/             # 資料收集相關
│   ├── database/               # 資料庫相關
│   │   ├── mongodb.py
│   │   ├── models/
│   │   └── repositories/
│   │
│   ├── indicators/            # 技術指標
│   ├── strategies/            # 交易策略
│   ├── config/                # 設定檔
│   └── utils/                 # 工具類
│
├── scripts/                   # 腳本工具
│   ├── setup_db.py            # 資料庫初始化
│   └── data_migration.py
│
├── docs/                      # 文件目錄
│   ├── api/
│   ├── database/
│   └── deployment/
│
└── reports/                   # 分析報告
```

## 資料庫設計

### Collections

1. **crypto_pairs**
   - pair_symbol: String (e.g., "BTC/USDT")
   - market_type: String ("spot" | "futures")
   - market_cap: Number
   - volume_24h: Number
   - last_updated: Date
   - metadata: Object

2. **news**
   - title: String
   - content: String
   - source: String
   - published_at: Date
   - related_pairs: Array<String>
   - sentiment_score: Number
   - created_at: Date

3. **tweets**
   - tweet_id: String
   - content: String
   - author: String
   - created_at: Date
   - related_pairs: Array<String>
   - sentiment_score: Number
   - metrics: Object (likes, retweets, etc.)

4. **technical_indicators**
   - pair_symbol: String
   - timestamp: Date
   - indicators: Object
     - rsi: Number
     - macd: Object
     - bollinger_bands: Object
     - moving_averages: Object
   - created_at: Date

5. **analysis_reports**
   - report_id: String
   - timestamp: Date
   - type: String ("daily" | "weekly" | "monthly")
   - pairs_analysis: Array<Object>
   - recommendations: Array<Object>
   - risk_assessment: Object
   - created_at: Date

### 索引設計

為了優化查詢效能，我們為每個集合設計了以下索引：

1. **crypto_pairs 索引**
   - `pair_symbol`：升序索引，確保交易對唯一性
   - `market_cap`：降序索引，用於市值排序查詢

2. **news 索引**
   - `published_at`：降序索引，用於時間範圍查詢
   - `related_pairs`：升序索引，用於特定交易對相關新聞查詢
   - `sentiment_score`：降序索引，用於情緒分析排序

3. **tweets 索引**
   - `created_at`：降序索引，用於時間範圍查詢
   - `related_pairs`：升序索引，用於特定交易對相關推文查詢
   - `sentiment_score`：降序索引，用於情緒分析排序

4. **technical_indicators 索引**
   - 複合索引：`(pair_symbol, timestamp)`，用於查詢特定交易對在特定時間的技術指標

5. **analysis_reports 索引**
   - `timestamp`：降序索引，用於時間查詢
   - 複合索引：`(type, timestamp)`，用於查詢特定類型報告的時間序列

## 授權條款 📄

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 文件

---

## 初始化設定

### setup.py 功能說明

`setup.py` 負責專案的初始化設定，主要功能包括：

1. **環境檢查**
   - Python 版本驗證
   - 必要套件安裝
   - 環境變數檢查與設定

2. **資料庫初始化**
   - MongoDB 連接設定
   - Collections 建立
   - 索引建立
   - 初始資料建立（如果需要）

3. **設定檔生成**
   - 建立 `.env` 檔案
   - 生成必要的設定檔
   - 設定日誌目錄

4. **權限設定**
   - 建立必要的目錄
   - 設定檔案權限
   - 設定日誌輪替
