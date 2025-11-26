# Edge Impulse Plugin Server

串聯 Virtual Device 與 Edge Impulse 的橋接服務，提供資料採集、自動訓練觸發、模型部署及推論模擬等功能。

## 功能特色

### 1. 資料採集整合（Data Ingestion Integration）
- 自動轉換 Virtual Device 資料格式為 Edge Impulse 相容格式（JSON、CBOR、二進位）
- 支援多種感測器類型（加速度計、麥克風、陀螺儀等）
- 自動管理 sensor metadata（取樣率、單位等）
- 直接上傳至 Edge Impulse Data Ingestion API

### 2. 自動訓練觸發（Automated Training Trigger）
- 累積達到 N 筆新資料後自動觸發訓練
- 監控訓練狀態並自動部署完成的模型
- 支援手動觸發訓練
- 完整的訓練歷史記錄

### 3. 端邊推論部署模擬（Edge Deployment Simulation）
- 模擬多種平台推論效能（Linux、Arduino、MCU、Raspberry Pi）
- 提供延遲（latency）和記憶體使用（memory usage）統計
- 支援即時推論 API

## 系統架構

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│ Virtual Device  │─────>│  Plugin Server   │─────>│  Edge Impulse   │
│                 │      │                  │      │                 │
│  - 感測器資料    │      │  - FastAPI       │      │  - ML 訓練      │
│  - 資料介面      │      │  - Celery Worker │      │  - 模型部署     │
└─────────────────┘      │  - Redis Queue   │      │  - 推論 API     │
                         └──────────────────┘      └─────────────────┘
```

## 快速開始

### 前置需求
- Docker & Docker Compose
- Edge Impulse 帳號及 API Key
- Python 3.11+ (本地開發)

### 安裝步驟

1. **複製專案**
```bash
git clone <repository-url>
cd edge-impulse-plugin-server
```

2. **設定環境變數**
```bash
cp .env.example .env
# 編輯 .env 檔案，填入你的 Edge Impulse API Key 和 Project ID
```

3. **啟動服務**
```bash
docker-compose up -d
```

4. **檢查服務狀態**
```bash
# 查看 API 服務
curl http://localhost:8000/health

# 查看 API 文件
open http://localhost:8000/docs

# 查看 Celery Flower (任務監控)
open http://localhost:5555
```

## API 端點

### 資料採集 (Data Ingestion)

#### 接收資料
```bash
POST /api/ingest/data
```

範例：
```json
{
  "device_id": "device_001",
  "samples": [
    {
      "sensor_type": "accelerometer",
      "sample_rate": 62.5,
      "data": [
        {"x": 0.1, "y": 0.2, "z": 9.8},
        {"x": 0.15, "y": 0.25, "z": 9.75}
      ],
      "metadata": {"location": "factory_floor"}
    }
  ],
  "label": "idle",
  "auto_upload": true
}
```

#### 從 Virtual Device 獲取資料
```bash
POST /api/ingest/fetch/{device_id}
```

#### 查詢樣本
```bash
GET /api/ingest/samples?device_id=device_001&uploaded=false&limit=100
```

### 設備管理與訓練 (Devices & Training)

#### 列出所有設備
```bash
GET /api/devices/
```

#### 取得設備詳情
```bash
GET /api/devices/{device_id}
```

#### 手動觸發訓練
```bash
POST /api/devices/training/trigger
```

```json
{
  "triggered_by": "manual"
}
```

#### 查詢訓練任務
```bash
GET /api/devices/training/jobs
```

#### 取得訓練任務狀態
```bash
GET /api/devices/training/jobs/{job_id}
```

#### 取得統計摘要
```bash
GET /api/devices/stats/summary
```

### 推論模擬 (Inference)

#### 執行推論
```bash
POST /api/infer/classify
```

範例：
```json
{
  "device_id": "device_001",
  "data": [0.1, 0.2, 9.8, 0.15, 0.25, 9.75],
  "platform": "arduino",
  "simulate_performance": true
}
```

#### 取得平台效能統計
```bash
GET /api/infer/performance/{platform}?device_id=device_001
```

#### 列出支援平台
```bash
GET /api/infer/platforms
```

## 配置說明

### 環境變數

| 變數名稱 | 說明 | 預設值 |
|---------|------|--------|
| `EI_API_KEY` | Edge Impulse API Key | (必填) |
| `EI_PROJECT_ID` | Edge Impulse Project ID | (必填) |
| `EI_API_BASE_URL` | Edge Impulse API 基礎 URL | `https://studio.edgeimpulse.com` |
| `VIRTUAL_DEVICE_URL` | Virtual Device 服務 URL | `http://virtual-device:8000` |
| `AUTO_TRAINING_THRESHOLD` | 自動訓練閾值（樣本數） | `100` |
| `DATA_FORMAT` | 資料格式 | `json` |
| `SIMULATE_PLATFORM` | 預設模擬平台 | `linux` |

### 支援的平台

| 平台 | 典型延遲 | 典型記憶體 | 說明 |
|------|---------|-----------|------|
| `linux` | 5-20ms | 200-500KB | 標準 Linux 平台 |
| `arduino` | 50-200ms | 50-150KB | Arduino 開發板 |
| `mcu` | 20-100ms | 30-100KB | 通用微控制器 |
| `raspberry-pi` | 10-30ms | 100-300KB | Raspberry Pi |

## 開發指南

### 本地開發

1. **建立虛擬環境**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **安裝依賴**
```bash
pip install -r requirements.txt
```

3. **啟動 Redis**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

4. **啟動 FastAPI**
```bash
uvicorn app.main:app --reload --port 8000
```

5. **啟動 Celery Worker**
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

### 執行測試

```bash
pytest tests/ -v
```

### 查看 API 文件

啟動服務後，訪問以下 URL：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 工作流程

### 資料採集流程

```
1. Virtual Device 發送資料 → POST /api/ingest/data
2. Plugin Server 儲存到資料庫
3. Celery Worker 上傳到 Edge Impulse
4. 檢查是否達到自動訓練閾值
```

### 自動訓練流程

```
1. 累積樣本達到閾值
2. 觸發 Celery 訓練任務
3. 呼叫 Edge Impulse Training API
4. 監控訓練狀態（每 30 秒檢查）
5. 訓練完成後自動部署模型
```

### 推論流程

```
1. 接收推論請求 → POST /api/infer/classify
2. 呼叫 Edge Impulse Inference API
3. 模擬目標平台效能
4. 記錄推論日誌
5. 返回預測結果及效能指標
```

## 監控與維護

### Celery Flower (任務監控)

訪問 http://localhost:5555 查看：
- 正在執行的任務
- 任務歷史記錄
- Worker 狀態
- 任務統計

### 日誌

查看容器日誌：
```bash
# API 服務日誌
docker-compose logs -f api

# Worker 日誌
docker-compose logs -f worker

# 所有服務日誌
docker-compose logs -f
```

### 資料庫管理

SQLite 資料庫位於 `./data/plugin_server.db`

```bash
# 查看資料庫
sqlite3 ./data/plugin_server.db

# 清空資料庫
rm ./data/plugin_server.db
docker-compose restart api worker
```

## 故障排除

### 常見問題

**Q: Edge Impulse API 呼叫失敗**
- 檢查 `EI_API_KEY` 和 `EI_PROJECT_ID` 是否正確
- 確認 Edge Impulse 專案存在且有權限

**Q: Celery Worker 無法連接 Redis**
- 確認 Redis 容器正在運行：`docker-compose ps redis`
- 檢查 Redis 連線字串：`redis://redis:6379/0`

**Q: 自動訓練未觸發**
- 檢查 `AUTO_TRAINING_THRESHOLD` 設定
- 確認樣本已成功上傳到 Edge Impulse
- 查看 Worker 日誌：`docker-compose logs worker`

## 授權

MIT License

## 聯絡方式

如有問題或建議，請開啟 Issue 或 Pull Request。